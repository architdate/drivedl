from __future__ import print_function
import pickle, util, sys, tqdm, time, json, uuid
import os.path
from multiprocessing import Pool
from colorama import Fore, Style
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/drive']
PROCESS_COUNT = 5

def add_account():
    tokenfile = f'token_{str(uuid.uuid4())}.pickle'
    os.makedirs('tokens', exist_ok=True)
    flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
    creds = flow.run_local_server(port=0)
    # Save the credentials for the next run
    with open(f'tokens/{tokenfile}', 'wb') as token:
        pickle.dump(creds, token)

def migrate():
    # Migrate token.pickle file to tokens folder
    os.makedirs('tokens', exist_ok=True)
    if os.path.exists('token.pickle'):
        print("Older token configuration detected. Migrating to the new setup")
        new_name = f'token_{str(uuid.uuid4())}.pickle'
        os.rename('token.pickle', f'tokens/{new_name}')

def get_accounts():
    return [x for x in os.listdir('tokens') if x.endswith('.pickle')]

def get_service(tokenfile):
    """Shows basic usage of the Drive v3 API.
    Prints the names and ids of the first 10 files the user has access to.
    """
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists(f'tokens/{tokenfile}'):
        with open(f'tokens/{tokenfile}', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open(f'tokens/{tokenfile}', 'wb') as token:
            pickle.dump(creds, token)

    service = build('drive', 'v3', credentials=creds)
    return service

def download_helper(args):
    rlc = util.download(*args)
    return (args[1]['name'], rlc)

def mapped_dl(args):
    rlc = util.download(*args, noiter=True)
    return (args[1]['name'], rlc)

def main(console_call=True):
    # Set path
    if console_call:
        os.chdir(os.path.dirname(os.path.abspath(__file__)))
    else:
        os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    if not os.path.exists('credentials.json'):
        print(f"Missing Credentials!\nEnable Drive API by clicking the blue button at https://developers.google.com/drive/api/v3/quickstart/python \nDownload the credentials.json file and save it here: {os.getcwd()}")

    migrate()
    accounts = get_accounts()
    service = None
    search = False
    skip = False
    noiter = False

    # File Listing
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <folderid> <destination>")
        sys.exit(-1)
    else:
        if sys.argv[1] == '--path':
            util.save_default_path(sys.argv[2])
            sys.exit(0)
        if sys.argv[1] == '--add':
            add_account()
            print("Account successfully added!")
            sys.exit(0)
        if '--search' in sys.argv:
            search = True
            sys.argv.remove('--search')
        if '--skip' in sys.argv:
            skip = True
            sys.argv.remove('--skip')
        if '--debug' in sys.argv:
            util.DEBUG = True
            sys.argv.remove('--debug')
        if '--noiter' in sys.argv:
            noiter = True
            sys.argv.remove('--noiter')
        if '--proc' in sys.argv:
            index = sys.argv.index('--proc')
            PROCESS_COUNT = int(sys.argv[index + 1])
            sys.argv.pop(index + 1)
            sys.argv.pop(index)
        else:
            PROCESS_COUNT = 5
        folderid = util.get_folder_id(sys.argv[1])
        if len(sys.argv) > 2:
            destination = sys.argv[2]
        elif os.path.isfile('config.json'):
            with open('config.json', 'r') as f:
                config = json.load(f)
            destination = config['default_path']
        else:
            destination = os.getcwd()
        
    file_dest = []

    def build_files():
        try:
            kwargs = {'top': folderid, 'by_name': False}
            for path, root, dirs, files in util.walk(service, **kwargs):
                path = ["".join([c for c in dirname if c.isalpha() or c.isdigit() or c in [' ', '-', '_', '.', '(', ')', '[', ']']]).rstrip() for dirname in path]
                for f in files:
                    dest = os.path.join(destination, os.path.join(*path))
                    file_dest.append((service, f, dest, skip))
            if file_dest != []:
                # First valid account found, break to prevent further searches
                return True
        except ValueError: # mimetype is not a folder
            dlfile = service.files().get(fileId=folderid, supportsAllDrives=True).execute()
            print(f"\nNot a valid folder ID. \nDownloading the file : {dlfile['name']}")
            # Only use a single process for downloading 1 file
            util.download(service, dlfile, destination, skip)
            sys.exit(0)
        except HttpError:
            print(f"{Fore.RED}File not found in account: {acc}{Style.RESET_ALL}")
            return False

    searches = []
    for acc in accounts:
        service = get_service(acc)
        if not search:
            valid = build_files()
            if valid: break
        else:
            searches += util.querysearch(service, folderid, 'rand', True)

    if searches != []:
        print("\nEnter the number of the folder you want to download:")
        for i in range(len(searches)):
            print(f" {Fore.YELLOW}{str(i+1).ljust(3)}{Style.RESET_ALL}    {searches[i]['name']}")
        print(f"\n{Fore.GREEN}Index:{Style.RESET_ALL} ", end='')
        index = int(input()) - 1
        if index + 1 > len(searches):
            print(f"{Fore.RED}Invalid Index. Exiting.{Style.RESET_ALL}")
            sys.exit(1)
        folderid = searches[index]['id']
        build_files()

    if service == None:
        # No accounts found with access to the drive link, exit gracefully
        print("No valid accounts with access to the file/folder. Exiting...")
        sys.exit(1)
    try:
        p = Pool(PROCESS_COUNT)
        if noiter:
            p.map(mapped_dl, file_dest)
        else:
            pbar = tqdm.tqdm(p.imap_unordered(download_helper, file_dest), total=len(file_dest))
            start = time.time()
            for i in pbar:
                rlc = i[1]
                status, main_str, end_str = util.get_download_status(rlc, start)
                pbar.write(status + main_str + f' {i[0]}' + end_str)
            p.close()
            p.join()
        if util.DEBUG:
            util.debug_write(f'debug_{int(time.time())}.log')
    except ImportError:
        # Multiprocessing is not supported (example: Android Devices)
        for fd in file_dest:
            download_helper(fd)

if __name__ == '__main__':
    main(False)
