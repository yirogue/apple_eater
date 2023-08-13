import pandas as pd
import gzip
import codecs
import blackboxprotobuf
import json
import hashlib
import struct
from datetime import datetime
from .utils import get_database_connection, create_directory, MDFile
from Crypto.Cipher import AES


def aes_unwrap_key(kek, wrapped):
    quad = struct.Struct('>Q')
    n = len(wrapped) // 8 - 1
    R = [b'None'] + [wrapped[i * 8:i * 8 + 8] for i in range(1, n + 1)]
    A = quad.unpack(wrapped[:8])[0]
    decrypt = AES.new(kek, AES.MODE_ECB).decrypt
    for j in range(5, -1, -1):
        for i in range(n, 0, -1):
            ciphertext = quad.pack(A ^ (n * j + i)) + R[i]
            B = decrypt(ciphertext)
            A = quad.unpack(B[:8])[0]
            R[i] = B[8:]
    return b"".join(R[1:])


def derive_password_key(data, password):
    password_key = hashlib.pbkdf2_hmac("sha256",
                                       bytes(password, 'utf-8'),
                                       data["crypto_salt"],
                                       data["crypto_iteration"],
                                       dklen=16)
    return password_key


def unwrap_encryption_key(data, password_key):
    unwrapped_key = aes_unwrap_key(password_key,
                                   data["crypto_wrapped_key"])
    return unwrapped_key


def decrypt_data(data, password):
    if not password:
        raise ValueError("Please put in your password to process the locked notes.")
    password_key = derive_password_key(data, password)
    key = unwrap_encryption_key(data, password_key)
    cipher = AES.new(key, AES.MODE_GCM, data["crypto_initialization_vector"])
    unwrapped_data = cipher.decrypt(data["data"])
    return unwrapped_data


def get_text(data, password):
    message = None
    unwrapped_data = decrypt_data(data, password) if data["is_password_protected"] else data["data"]
    try:
        unwrapped_data = gzip.decompress(unwrapped_data)
        unwrapped_data = codecs.decode(unwrapped_data.hex(), encoding='hex', errors='strict')
        message, typedef = blackboxprotobuf.protobuf_to_json(unwrapped_data)
        message = json.loads(message)['2']['3']['2']
    except Exception as error:
        print(f"note decryption failed for <{data['title']}>")
        print(f"Error: {error}")
    return message


def get_metadata(db_dir, password):
    database = get_database_connection(db_dir, 'notes')
    query = """
    SELECT 
        Z.Z_PK as key, Z.ZTITLE1 as title, _FOLDER.ZTITLE2 as folder, NOTEDATA.ZDATA as data, 
        Z.ZCREATIONDATE3 as creation_date, Z.ZMODIFICATIONDATE1 as modification_date,
        Z.ZISPASSWORDPROTECTED as is_password_protected,
        Z.ZCRYPTOITERATIONCOUNT as crypto_iteration, Z.ZCRYPTOSALT as crypto_salt, Z.ZCRYPTOTAG as crypto_tag,
        Z.ZCRYPTOINITIALIZATIONVECTOR as crypto_initialization_vector, Z.ZCRYPTOWRAPPEDKEY as crypto_wrapped_key
    FROM ZICCLOUDSYNCINGOBJECT as Z 
    INNER JOIN ZICCLOUDSYNCINGOBJECT AS _FOLDER ON Z.ZFOLDER = _FOLDER.Z_PK 
    INNER JOIN ZICNOTEDATA as NOTEDATA ON Z.ZNOTEDATA = NOTEDATA.Z_PK 
    WHERE _FOLDER.ZTITLE2 != 'Recently Deleted'
    """
    metadata = pd.read_sql_query(query, database)
    metadata["data"] = [get_text(metadata.loc[i], password) for i in metadata.index]
    for col in ["creation_date", "modification_date"]:
        metadata[col] = [datetime.fromtimestamp(date + 978307200).strftime('%Y-%m-%d %H:%M:%S')
                         for date in metadata[col]]
    return metadata


def save_raw_data(data, path):
    raw_data = data[["key", "title", "folder", "data", "creation_date", "modification_date", "is_password_protected"]]
    raw_data.to_csv(path, index=False)


def create_md_file(note, directory):
    title = note["title"]
    folder_path = create_directory(directory, note["folder"])
    md_file = MDFile(title=title, directory=folder_path)
    md_file.add_header(level=1, title='Note Overview')
    for key in ["folder", "creation_date", "modification_date"]:
        md_file.add_paragraph(f"**{key.capitalize()}**: {note[key]}")
    md_file.add_header(level=1, title='Note Content')
    md_file.add_paragraph(note["data"])
    md_file.write_file()
