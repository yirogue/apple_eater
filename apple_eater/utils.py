import os
import re
from glob import glob
import sqlite3


class MDFile:
    def __init__(self, title, directory):
        self.file = ""
        self.filename = os.path.join(directory, f"{title.replace('/', '&')}_notes.md")
        self.headers = []
        self.title = get_title(title)

    def add_header(self, level, title, header_id=""):
        header, header_id = get_header(level, title, header_id)
        self.file += header
        self.headers.append({"level": level, "header": f"[{title}](#{header_id})"})

    def add_paragraph(self, text):
        self.file += f"\n\n{text}"

    def add_table_of_content(self, title, depth):
        toc = []
        title = get_title(title)
        for header in self.headers:
            level = header["level"]
            if level <= depth:
                toc.append("\t"*(level-1) + f"* {header['header']}")
        toc = '\n'.join(toc) + '\n'
        self.file = title + toc + self.file

    def add_line(self, text):
        self.file += " \n" + text

    def add_status(self, title, level):
        header, _ = get_header(level, title)
        self.file = header + self.file

    def write_annotations(self, annotations, chapter):
        self.add_header(level=2, title=chapter)
        index = 1
        for annotation in annotations:
            note = annotation["notes"]
            self.add_header(level=3, title=str(index).rjust(3, '0'))
            self.add_paragraph(annotation["highlights"])
            if note:
                note = note.split('\n')
                if len(note) > 1:
                    for n in note:
                        self.add_line(f"> {n}")
                else:
                    self.add_paragraph(f"> {note[0]}")
            index += 1

    def write_file(self):
        with open(self.filename, 'w') as file:
            file.write(self.title + self.file)


def get_title(title):
    return "\n" + title + "\n" + "".join(["=" for _ in title]) + "\n"


def get_header(level, title, header_id=""):
    header_id = header_id if header_id else re.sub("[^a-z0-9_\-]", "", title.lower().replace(" ", "-"))
    header = f"\n\n{'#' * level} {title} \n"
    return header, header_id


def get_database_path(db_dir):
    databases = glob(db_dir + '/*.sqlite')
    if len(databases) == 0:
        raise ValueError("No data found in the database.")
    return databases[0]


def get_database_connection(db_dir, db_type):
    db_path = get_database_path(db_dir) if db_type == 'ibooks' else db_dir
    try:
        database = sqlite3.connect(db_path)
    except sqlite3.Error as error:
        raise ValueError(error)
    database.text_factory = lambda x: str(x, "utf8")
    return database


def create_directory(directory, path):
    full_path = os.path.join(directory, path)
    if not os.path.exists(full_path):
        os.makedirs(full_path)
    return full_path
