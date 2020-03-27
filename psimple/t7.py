import PySimpleGUI as sg

sg.theme('Dark Blue 3')

layout = [[sg.Text('Rename files or folders')],
            [sg.Text('Source for Folders', size=(15, 1)), sg.InputText(), sg.FolderBrowse()],
            [sg.Text('Source for Files ', size=(15,1)), sg.InputText(), sg.FolderBrowse()],
            [sg.Submit(), sg.Cancel()]]

window = sg.Window('Rename Files or folders', layout)

event, values = window.read()
window.close()

folder_path, file_path = values[0], values[1]

print (folder_path, file_path)
