from .utils import MDFile, create_directory
from . import ibooks, notes
import os
import getopt
import sys


def get_argument():
    arg_list = sys.argv[1:]
    options = "ht:d:"
    long_options = ["Help", "Type=", "Directory="]
    data_type = 'ibooks'
    directory = None

    try:
        arguments, values = getopt.getopt(arg_list, options, long_options)
        for current_arg, current_val in arguments:
            if current_arg in ("-h", "--Help"):
                print("apple_eater")
                print("-t --Type : the type of files you want to export, e.g., ibooks, notes")
                print("-d --Directory : the output directory name")
            elif current_arg in ("-t", "--Type"):
                print("Exporting data from type: ", current_val)
                if current_val not in ("ibooks", "notes"):
                    raise ValueError("Only ibooks and notes can be exported for now")
                data_type = current_val
            elif current_arg in ("-d", "--Directory"):
                print("Output directory: ", current_val)
                directory = current_val
            else:
                raise ValueError(f"Argument name {current_arg} is not recognized")
    except getopt.error as err:
        raise ValueError(str(err))

    directory = data_type + '/' if not directory else directory
    return data_type, directory


def export_ibooks(user, directory):
    data_path = os.path.join(directory, "raw_data/")
    if not os.path.exists(data_path):
        os.makedirs(data_path)
    lib_dir = f"/Users/{user}/Library/Containers/com.apple.iBooksX/Data/Documents"
    books_dir = lib_dir + "/BKLibrary"
    notes_dir = lib_dir + "/AEAnnotation"

    books_metadata_raw = ibooks.get_metadata(books_dir, mode="books")
    notes_metadata_raw = ibooks.get_metadata(notes_dir, mode="notes")

    books, metadata = ibooks.save_combined_data(books_metadata_raw, notes_metadata_raw, data_path)
    for title in books["Title"]:
        book = books[books["Title"] == title].to_dict(orient="records")[0]
        book_meta = metadata[metadata["Title"] == title].reset_index()
        if book_meta.shape[0] > 0:
            ibooks.create_md_file(book, book_meta, directory)
    print(f"Exported highlights & notes from {len(books)} books.")


def export_notes(user, password="", directory="notes/"):
    data_path = create_directory(directory, "raw_data/")
    lib_dir = f"/Users/{user}/Library/Group Containers/group.com.apple.notes/NoteStore.sqlite"
    exports = notes.get_metadata(lib_dir, password)
    notes.save_raw_data(exports, os.path.join(data_path, "notes_data.csv"))
    for index in exports.index:
        notes.create_md_file(exports.loc[index], directory)
    print(f"Exported {len(exports)} notes successfully from Apple Notes.")
