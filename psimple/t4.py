import PySimpleGUI as sg

sg.theme('Dark Blue 3')

layout = [[sg.Text('SHA-1 and SHA-256 Hashes for the file')],
                [sg.InputText(), sg.FileBrowse()],
                [sg.Submit(), sg.Cancel()]]

window = sg.Window('SHA-1 & 256 Hash', layout)

event, values = window.read()
window.close()

source_filename = values[0]

print ("source file name is: " + source_filename)
