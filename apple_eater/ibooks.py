import pandas as pd
import os
from .utils import get_database_connection, MDFile


def get_metadata(db_dir, mode):
    database = get_database_connection(db_dir, 'ibooks')
    if mode == 'books':
        query = """
        SELECT 
            ZASSETID as AssetID, ZTITLE AS Title, ZAUTHOR AS Author, ZCOVERURL as CoverURL, ZGENRE as Genre,
            ZISFINISHED as IsFinished
        FROM ZBKLIBRARYASSET 
        WHERE ZTITLE IS NOT NULL
        """
    else:
        query = '''
        SELECT
            ZANNOTATIONREPRESENTATIVETEXT as BroaderText,
            ZANNOTATIONSELECTEDTEXT as HighlightedText,
            ZANNOTATIONNOTE as Note,
            ZFUTUREPROOFING5 as Chapter,
            ZANNOTATIONCREATIONDATE as Created,
            ZANNOTATIONMODIFICATIONDATE as Modified,
            ZANNOTATIONASSETID,
            ZPLLOCATIONRANGESTART,
            ZANNOTATIONLOCATION
        FROM ZAEANNOTATION
        WHERE ZANNOTATIONSELECTEDTEXT IS NOT NULL
        ORDER BY ZANNOTATIONASSETID ASC,Created ASC
        '''
    metadata = pd.read_sql_query(query, database)
    return metadata


def save_refined(data, filename):
    data["Title"] = data["Title"].str.replace(r'(\(|【)(.*?)(】|\))', '', regex=True)
    data.to_csv(filename, index=False)
    return data


def save_combined_data(books, notes, data_path):
    metadata_raw = pd.merge(books, notes, how="inner", left_on="AssetID", right_on="ZANNOTATIONASSETID")
    metadata_raw.drop(["ZANNOTATIONASSETID"], axis=1, inplace=True)
    books = save_refined(books, os.path.join(data_path, "ibooks_library_books.csv"))
    metadata = save_refined(metadata_raw, os.path.join(data_path, "ibooks_library_notes.csv"))
    return books, metadata


def get_chapter(metadata, index):
    chapter = metadata.loc[index, "Chapter"]
    chapter = chapter if chapter else "Unknown"
    return chapter


def create_md_file(book, metadata, directory):
    title = book["Title"]
    md_file = MDFile(title=title, directory=directory)
    md_file.add_header(level=1, title='Book Overview')
    for k, v in book.items():
        if k != 'IsFinished':
            md_file.add_paragraph(f"**{k}**: {v}")
    chapter_collection = []
    notes_collection = {}
    annotation_collection = {}
    for i in metadata.index:
        chapter = get_chapter(metadata, i)
        if chapter not in notes_collection:
            chapter_collection.append(chapter)
            notes_collection[chapter] = []
            annotation_collection[chapter] = []
        annotation = {'highlights': metadata.loc[i, 'HighlightedText'],
                      'notes': metadata.loc[i, 'Note']}
        if metadata.loc[i, 'Note']:
            notes_collection[chapter].append(annotation)
        annotation_collection[chapter].append(annotation)
    md_file.add_header(level=1, title='Notes Collection')
    for chapter in chapter_collection:
        notes = notes_collection[chapter]
        if notes:
            md_file.write_annotations(notes, chapter)
    md_file.add_header(level=1, title='Highlights & Notes')
    for chapter in chapter_collection:
        annotations = annotation_collection[chapter]
        md_file.write_annotations(annotations, chapter)
    md_file.add_table_of_content(title='Contents', depth=2)
    status = "✅ Finished" if book["IsFinished"] else "📖 In Progress"
    md_file.add_status(status, level=3)
    md_file.write_file()
