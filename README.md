[![PyPI version](https://badge.fury.io/py/drivedl.svg)](https://badge.fury.io/py/drivedl)

# drivedl

This is a CLI tool for concurrent downloads of directories in any drive type. (My Drive, Team Drive or Shared with me)

The tool requires the `'https://www.googleapis.com/auth/drive'` scope as of now. This scope can be tightened since all that the script needs is permission to traverse and download data from the drives. Feel free to PR a different scope if it is more relevant

## Installation:

- Install the binary through PyPI using the following command:
```bash
$ pip install drivedl
```

## Pre-requisites:

- Download `credentials.json` for a Desktop drive application. Instructions on how to get that can be found [here](https://developers.google.com/drive/api/v3/quickstart/python) (refer to Step 1)
- Save the `credentials.json` file in the same directory as `drivedl.py`
- Install the Drive API for python by running the following command:
```bash
$ pip install -r requirements.txt
```

## Usage:

```bash
$ python drivedl.py <folder_id / file_id> <path_to_save>
```
It is as straightforward as that!

Note that on the first run, you will have to authorize the scope of the application. This is pretty straightforward as well!

## Skipping existing files:

Adding an argument `--skip` to your command will skip existing files and not redownload them.
- By default the behaviour is to download everything without skipping.

## Assigning extra processes:

Adding an argument `--proc` followed by an integer of processes to assign the application will spawn the specified processes to do the download
- Example: `--proc 10` for 10 processes

## Downloading using process map instead of an iterated map:

Adding an argument `--noiter` tells the program to download via `process.map` instead of `process.imap_unordered`. This lets you download faster with the drawback of no process bar being shown because of no iterable item. Recommended to be used if speed is of essence.

## Add extra accounts:

Run the following command to add a new account. (Adding an account means that it will also be searched when using drivedl)
```bash
$ python drivedl.py --add
```
You will have to authorize the scope of the application for the new account as well. The token will automatically be saved for future uses once permission is granted!

## Searches:

If you add `--search` to your command, you can search for the folder name using keywords instead of using the folder link or the folder ID. This searches through all drives in all registered accounts and gives a maximum of 10 results per drive. There is no cap on the global maximum results. The search is limited to folders and will not index loose files.

An example of usage is as follows:
```
$ python drivedl.py "avengers endgame" --search "D:/Google Drive Downloads"
```
This also works with default path configurations (stated below).

## Default Path [Optional]

```bash
$ python drivedl.py --path <default_path>
```

This lets you specify a default path for your download location.

## Debugging:

Adding `--debug` writes a log file once the entire task is completed so that any issues can be documented. This is helpful while making GitHub issues to pinpoint issues with the script.

## TODO:

- [x] Add URL parsing
- [x] Add default path
- [x] Single file download support
- [x] Color support
- [x] Multi-Account support
- [x] Skip existing files
- [x] Search functionality
- [x] Functionality to download docs