# apple_eater

## Overview
An easy to eat the Apple - to export your Apple notes and ibook annotations in one command.

## How to use
Simply run the one-line command as below in the terminal to export your notes or ibook annotations.
```
$ python3 eater.py -t TYPE_TO_EXPORT -d EXPORT_DIRECTORY
```
Use argument:
1. -t or --t to specify the type of data to export. options include `notes` and `ibooks`.
2. -d or --d to specify the path to save your markdown files. If not specified, it would create a new directory called `books` or `notes` by default.


## Output

#### For Notes:
- Markdown files for each note, including its creation & modification date (under the subdirectory of its folder name)
- CSV files for notes metadata (under a `raw_data` sub-folder)

#### For iBooks Annotations:
- Markdown files for each book containing its highlights and notes (under the directory specified)
- CSV files for books metadata and annotations metadata (under a `raw_data` sub-folder)