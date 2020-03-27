import PySimpleGUI as sg

sg.theme('Dark Blue 3')

layout = [  [sg.Text('Filename')],
            [sg.Input(), sg.FileBrowse()],
            [sg.OK(), sg.Cancel()]]

window = sg.Window('Get filename example', layout)

event, values = window.Read()

window.close()
