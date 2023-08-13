from apple_eater import export_notes, export_ibooks, get_argument
import getpass as gt

if __name__ == "__main__":
    username = gt.getuser()
    export_type, dir_name = get_argument()
    if export_type == "notes":
        note_password = input("Enter your password for notes if there are locked notes: \n")
        export_notes(username, note_password, dir_name)
    else:
        export_ibooks(username, dir_name)
