# drivedl

This is a CLI tool for concurrent downloads of directories in any drive type. (My Drive, Team Drive or Shared with me)

The tool requires the `'https://www.googleapis.com/auth/drive'` scope as of now. This scope can be tightened since all that the script needs is permission to traverse and download data from the drives. Feel free to PR a different scope if it is more relevant

## Pre-requisites:

- Download `credentials.json` for a Desktop drive application. Instructions on how to get that can be found [here](https://developers.google.com/drive/api/v3/quickstart/python) (refer to Step 1)
- Save the `credentials.json` file in the same directory as `drivedl.py`
- Install the Drive API for python by running the following command:
```bash
$ pip install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib tqdm
```

## Usage:

```bash
$ python drivedl.py <folder_id> <path_to_save>
```

It is as straightforward as that!

Note that on the first run, you will have to authorize the scope of the application. This is pretty straightforward as well!

## TODO:

- [ ] Add URL parsing
- [ ] Possible GUI?
- [ ] Search functionality