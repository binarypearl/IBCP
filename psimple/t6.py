import PySimpleGUI as sg

sg.theme('Dark Blue 3')

layout = [[sg.Text('Your typed chars appear here:'), sg.Text(size=(12,1), key='-OUTPUT-')],
            [sg.Input(key='-IN-')],
            [sg.Button('Show'), sg.Button('Exit')]]

window = sg.Window('Window Title', layout)

while True:
    event, values = window.read()

    print (event, values)

    if event is None or event == 'Exit':
        break

    if event == 'Show':
        window['-OUTPUT-'].update(values['-IN-'])

        # or...
        #window['-OUTPUT-'](values['-IN-'])

window.close()
