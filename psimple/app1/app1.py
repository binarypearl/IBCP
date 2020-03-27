import PySimpleGUI as sg
import subprocess
from nonblock import nonblock_read
import os
import time
import sys

sg.theme('Dark Blue 3')

layout =    [
            [sg.Text('Welcome to IBCP huamn interface!', size=(50, 1))],
            [sg.Multiline(default_text='Output area', size=(200,20), autoscroll=True, do_not_clear=True, enter_submits=True, key='-OUTPUT-')],
            [sg.Text('Enter some input', size=(15,1))],
            [sg.Text('Guess a number', size=(15,1)), sg.InputText('', key='-INPUT-')],
            [sg.Submit(), sg.Cancel()]
            ]

window = sg.Window('What goes here?', layout)

event, values = window.read()

output_list = []

command_ran = False

while True:
    '''
    event, values = window.read(timeout=100)

    print ("values is: " + str(values))

    print ("output of multiline: " + str(window['-OUTPUT-'].update(values['-INPUT-'])))

    if event is None or event == 'Exit' or event == 'Cancel':
        break

    '''

    event, values = window.read(timeout=1000)
    print (event, values)

    # Run command here:
    #output = subprocess.check_output(['/usr/bin/tail', '-n', '10', '/var/log/syslog'], universal_newlines=True)
    #process = subprocess.Popen(['/usr/bin/vmstat', '1', '5'], universal_newlines=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    #pipe = Popen(['/usr/bin/vmstat', '1', '5'], stdout=PIPE, universal_newlines=True, shell=True)

    #if not command_ran:
        #pipe = Popen([ '/mnt/backups/anki/IBCP/applications/number_guesser/number_guesser.py', '-c', '/mnt/backups/anki/IBCP/ibcp.cfg', '--p1', 'vector:0060100c', '--p2', 'vector:0060689b' ], stdout=PIPE, universal_newlines=True, shell=True)
        #pipe = Popen("/mnt/backups/anki/IBCP/applications/number_guesser/number_guesser.py -c /mnt/backups/anki/IBCP/ibcp.cfg --p1 vector:0060100c --p2 vector:0060689b", stdout=PIPE, universal_newlines=True, shell=False)
        #pipe = Popen("/mnt/backups/anki/IBCP/psimple/app1/wrapper.sh", stdout=PIPE, universal_newlines=True, shell=True)

    p = subprocess.Popen("/mnt/backups/anki/IBCP/applications/number_guesser/number_guesser.py -c /mnt/backups/anki/IBCP/ibcp.cfg --p1 vector:00508a44 --p2 vector:0060689b", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)

    while True:
        out = p.stdout.read(1)
        if out == '' and p.poll() != None:
            break
        if out != '':
            #sys.stdout.write(out)
            #sys.stdout.flush()
            window['-OUTPUT-'].update(out, append=True)
            window.Refresh()



        '''
        while True:
            data = nonblock_read(pipe.stdout, 1, 't')

            print ("What is data: ***" + str(data) + "***")

            if data is None:
                print ("If data is None")
                pipe.wait()
                break

            elif data:
                print ("elif data")
                window['-OUTPUT-'].update(data, append=True)
                window.Refresh()

            else:
                print ("else pass")
                time.sleep(1)
                pass
        '''
    #output_splitlines = output.stdout.splitlines()

    #for record in output_splitlines:
    #    window['-OUTPUT-'].update(record + "\n", append=True)


    #output_splitlines = output.split("\n")

    #for record in output_splitlines:
    #    window['-OUTPUT-'].update(record)

    if event is None or event == 'Exit' or event == 'Cancel':
        break

    #command_ran = True


window.close()
