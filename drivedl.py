from __future__ import print_function
import pickle, util, sys
import os.path
from multiprocessing import Pool
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/drive']
PROCESS_COUNT = 5

def get_service():
    """Shows basic usage of the Drive v3 API.
    Prints the names and ids of the first 10 files the user has access to.
    """
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
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
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('drive', 'v3', credentials=creds)
    return service

if __name__ == '__main__':
    # Set path
    abspath = os.path.abspath(__file__)
    dname = os.path.dirname(abspath)
    os.chdir(dname)

    service = get_service()

    
    # File Listing
    if len(sys.argv) < 2:
        print("Usage: tdlist <folderid> <destination>")
    else:
        folderid = sys.argv[1]
        if len(sys.argv) > 2:
            destination = sys.argv[2]
        else:
            destination = os.getcwd()
        
    file_dest = []
    for kwargs in [{'top': folderid, 'by_name': False}]:
        for path, root, dirs, files in util.walk(service, **kwargs):
            for f in files:
                dest = os.path.join(destination, os.path.join(*path))
                file_dest.append((service, f, dest))

    p = Pool(PROCESS_COUNT)
    p.map(util.download_helper, file_dest)