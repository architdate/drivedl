from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.http import MediaIoBaseDownload
from colorama import Fore, Style
import io, os, shutil, uuid, sys, json, time

FOLDER = 'application/vnd.google-apps.folder'
DEBUG = False
CHUNK_SIZE = 20 * 1024 * 1024 # 20MB chunks

DEBUG_STATEMENTS = [] # cache all debug statements

def debug_write(logfile):
    with open(logfile, 'w') as f:
        f.write('\n'.join(DEBUG_STATEMENTS))
    print(f"{Fore.YELLOW}DEBUG LOG SAVED HERE:{Style.RESET_ALL} {logfile}")

def list_td(service):
    # Call the Drive v3 API
    results = service.drives().list(pageSize=100).execute()

    if not results['drives']:
        return None
    else:
        return results['drives']

def iterfiles(service, name=None, is_folder=None, parent=None, order_by='folder,name,createdTime'):
    q = []
    if name is not None:
        q.append("name = '%s'" % name.replace("'", "\\'"))
    if is_folder is not None:
        q.append("mimeType %s '%s'" % ('=' if is_folder else '!=', FOLDER))
    if parent is not None:
        q.append("'%s' in parents" % parent.replace("'", "\\'"))
    params = {'pageToken': None, 'orderBy': order_by, 'includeItemsFromAllDrives': True, 'supportsAllDrives': True}
    if q:
        params['q'] = ' and '.join(q)
    while True:
        response = service.files().list(**params).execute()
        for f in response['files']:
            yield f
        try:
            params['pageToken'] = response['nextPageToken']
        except KeyError:
            return

def walk(service, top='root', by_name=False):
    if by_name:
        top, = iterfiles(service, name=top, is_folder=True)
    else:
        top = service.files().get(fileId=top, supportsAllDrives=True).execute()
        if top['mimeType'] != FOLDER:
            raise ValueError('not a folder: %r' % top)
    stack = [((top['name'],), top)]
    print(f"Indexing: {Fore.YELLOW}{top['name']}{Style.RESET_ALL}\nFolder ID: {Fore.YELLOW}{top['id']}{Style.RESET_ALL}\n")
    while stack:
        path, top = stack.pop()
        dirs, files = is_file = [], []
        for f in iterfiles(service, parent=top['id']):
            is_file[f['mimeType'] != FOLDER].append(f)
        yield path, top, dirs, files
        if dirs:
            stack.extend((path + (d['name'],), d) for d in reversed(dirs))

def querysearch(service, name=None, drive_id=None, is_folder=None, parent=None, order_by='folder,name,createdTime'):
    q = []
    items = []
    if name is not None:
        q.append("name contains '%s'" % name.replace("'", "\\'"))
    if is_folder is not None:
        q.append("mimeType %s '%s'" % ('=' if is_folder else '!=', FOLDER))
    if parent is not None:
        q.append("'%s' in parents" % parent.replace("'", "\\'"))
    if drive_id == None:
        params = {'pageToken': None, 'orderBy': order_by, 'includeItemsFromAllDrives': True, 'supportsAllDrives': True}
    else:
        params = {'pageToken': None, 'orderBy': order_by, 'includeItemsFromAllDrives': True, 'supportsAllDrives': True, 'corpora': 'allDrives'}
    if q:
        params['q'] = ' and '.join(q)
    while len(items) < 10:
        response = service.files().list(**params).execute()
        for f in response['files']:
            items.append(f)
        try:
            params['pageToken'] = response['nextPageToken']
        except KeyError:
            break
    return items

def download(service, file, destination, skip=False, noiter=False):
    # file is a dictionary with file id as well as name
    if skip and os.path.exists(os.path.join(destination, file['name'])):
        return -1
    mimeType = file['mimeType']
    if "application/vnd.google-apps" in mimeType:
        if "form" in mimeType: return -1
        elif "document" in mimeType:
            dlfile = service.files().export_media(fileId=file['id'], mimeType='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
        elif "spreadsheet" in mimeType:
            dlfile = service.files().export_media(fileId=file['id'], mimeType='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        elif "presentation" in mimeType:
            dlfile = service.files().export_media(fileId=file['id'], mimeType='application/vnd.openxmlformats-officedocument.presentationml.presentation')
        else:
            dlfile = service.files().export_media(fileId=file['id'], mimeType='application/pdf')
    else:
        dlfile = service.files().get_media(fileId=file['id'], supportsAllDrives=True)
    rand_id = str(uuid.uuid4())
    os.makedirs('buffer', exist_ok=True)
    fh = io.FileIO(os.path.join('buffer', rand_id), 'wb')
    downloader = MediaIoBaseDownload(fh, dlfile, chunksize=CHUNK_SIZE)
    if noiter: print(f"{Fore.GREEN}Downloading{Style.RESET_ALL} {file['name']} ...")
    done = False
    rate_limit_count = 0
    while done is False and rate_limit_count < 20:
        try:
            status, done = downloader.next_chunk()
        except Exception as ex:
            DEBUG_STATEMENTS.append(f'File Name: {file["name"]}, File ID: {file["id"]}, Exception: {ex}')
            rate_limit_count += 1
    fh.close()
    if noiter and rate_limit_count == 20: print(f"{Fore.RED}Error      {Style.RESET_ALL} {file['name']} ...")
    os.makedirs(destination, exist_ok=True)
    while True:
        try:
            shutil.move(os.path.join('buffer', rand_id), os.path.join(destination, file['name']))
            break
        except PermissionError:
            # wait out the file write before attempting to move
            pass
    return rate_limit_count

def get_folder_id(link):
    # function to isolate folder id
    if 'drive.google.com' in link:
        link = link.split('/view')[0].split('/edit')[0] # extensions to file names
        link = link.rsplit('/', 1)[-1] # final backslash
        link = link.split('?usp')[0] # ignore usp=sharing and usp=edit
        # open?id=
        link = link.rsplit('open?id=')[-1] # only take what is after open?id=
        return link
    else:
        return link

def save_default_path(path):
    if os.path.isfile('config.json'):
        with open('config.json', 'r') as f:
            config = json.load(f)
        config['default_path'] = path
    else:
        config = {}
        config['default_path'] = path
    with open('config.json', 'w') as f:
        f.write(json.dumps(config, indent= 4))

def get_download_status(rlc, start):
    if rlc == -1: # skipped file
        status = f'{Fore.CYAN}Skipped:   {Style.RESET_ALL} '
    elif rlc == 0:
        status = f'{Fore.GREEN}Downloaded:{Style.RESET_ALL} '
    elif rlc < 20:
        status = f'{Fore.YELLOW}Warning:   {Style.RESET_ALL} '
    else:
        status = f'{Fore.RED}Error:     {Style.RESET_ALL} '
    time_req = str(int(time.time() - start)) + 's'
    main_str = f'{Fore.BLUE}[Time: {time_req.rjust(5)}]{Style.RESET_ALL}'
    end_str = ''
    if rlc > 0 and rlc < 20:
        end_str += f' [Rate Limit Count: {rlc}] File saved'
    elif rlc >= 20:
        end_str += f' [Rate Limit Count: {rlc}] Partial file saved'
    return (status, main_str, end_str)