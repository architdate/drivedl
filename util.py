from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.http import MediaIoBaseDownload
import io, os, shutil, uuid, sys

FOLDER = 'application/vnd.google-apps.folder'
CHUNK_SIZE = 20 * 1024 * 1024 # 20MB chunks

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
    print(f"Indexing: {top['name']}\nFolder ID: {top['id']}\nDrive ID: {top['driveId']}\n")
    while stack:
        path, top = stack.pop()
        dirs, files = is_file = [], []
        for f in iterfiles(service, parent=top['id']):
            is_file[f['mimeType'] != FOLDER].append(f)
        yield path, top, dirs, files
        if dirs:
            stack.extend((path + (d['name'],), d) for d in reversed(dirs))

def download(service, file, destination):
    # file is a dictionary with file id as well as name
    dlfile = service.files().get_media(fileId=file['id'], supportsAllDrives=True)
    rand_id = str(uuid.uuid4())
    fh = io.FileIO(os.path.join('buffer', rand_id), 'wb')
    downloader = MediaIoBaseDownload(fh, dlfile, chunksize=CHUNK_SIZE)
    done = False
    while done is False:
        try:
            status, done = downloader.next_chunk()
        except Exception as ex:
            print(f"User rate limit exceeded for {file['name']}")
    fh.close()
    os.makedirs(destination, exist_ok=True)
    while True:
        try:
            shutil.move(os.path.join('buffer', rand_id), os.path.join(destination, file['name']))
            break
        except PermissionError:
            # wait out the file write before attempting to move
            pass
    