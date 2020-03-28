import PySimpleGUI as sg
import subprocess
from nonblock import nonblock_read
import os
import time
import sys
import stomp                # For Apache MQ messaging
import re

class MyListener(stomp.ConnectionListener):
    def on_error(self, headers, message):
        print('received an error "%s"' % message)

    def on_message(self, headers, message):
        print('received a message "%s"' % message)
        global message_queue

        match_object = re.search('(.*?)(:)(.*?)(:)(.*?)(:)(.*)', message)

        if match_object:
            message_queue.append(match_object)

message_queue = []

player_one_serial = "00508a44"
player_two_serial = "0060689b"
mq_server = "192.168.1.153"
mq_port = "61613"

# Create connection to MQ server.
try:
    # IP and port of MQ server.  Defined in ibcp.cfg.
    stomp_conn = stomp.Connection([(mq_server, mq_port)])
    stomp_conn.set_listener('', MyListener())

    # This is weird, when apps try to create their own username/password mechanims and it's just
    # like, what were they thinking?  I think I just created admin/admin in here and it works.
    # Really secure, but...at least it works.
    stomp_conn.connect('admin', 'admin', wait=True)

except Exception as e:
    print ("error: " + str(e))

if player_one_serial:
    stomp_conn.subscribe(destination='/queue/' + 'ng_output_' + player_one_serial, id=5, ack='auto')

if player_two_serial:
    stomp_conn.subscribe(destination='/queue/' + 'ng_output_' + player_two_serial, id=6, ack='auto')

sg.theme('Dark Blue 3')

layout =    [
            [sg.Text('Welcome to IBCP huamn interface!', size=(50, 1))],
            [sg.Multiline(default_text='', size=(200,20), autoscroll=True, do_not_clear=True, enter_submits=True, key='-OUTPUT-')],
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

    print ("I am doing a read here.")

    if event is None or event == 'Exit' or event == 'Cancel':
        break

    event, values = window.read(timeout=1000)
    print (event, values)

    if not command_ran:
        p = subprocess.Popen("/mnt/backups/anki/IBCP/applications/number_guesser/number_guesser.py -c /mnt/backups/anki/IBCP/ibcp.cfg --p1 vector:00508a44 --p2 vector:0060689b", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        command_ran = True

    if command_ran:
        print ("COMMAND HAS BEEN RAN")

    for message in message_queue:
        # IBCP message format:  to_robot:from_robot:command:payload
        # where:
        # to_robot is the serial number of the robot that is the intended receiver of the message
        #
        # from_robot is the serial number of the robot that sent the message
        #
        # command is a high level command like "say", "move", "animate".  I'm really only using
        #    'say' and 'said' at the moment.  IBCP (at least at the moment) doesn't define specific
        #     commands.  It's a field where you put in a command that makes sense and then
        #     process it as needed.
        #
        # payload is whatever information that is needed to go along with the command.  For example
        #     if the command was "say", the payload could be "Hello robot".  We can overload payload as well.
        #     For example, robot 1 needs to pass in the current_min and current max values to robot 2.
        #     So the payload might be like:  guess:25:1:50  where the guess was 25, the current min is 1 and
        #     the current_max is 50.

        print ("We have a message: " + str(message))
        to_robot = message.group(1)
        from_robot = message.group(3)
        command = message.group(5)
        payload = message.group(7)

        window['-OUTPUT-'].update(payload + "\n", append=True)

        # Remove the MQ message from the message_queue[] list now that we have processed it.
        message_queue.remove(message)



    # Run command here:
    #output = subprocess.check_output(['/usr/bin/tail', '-n', '10', '/var/log/syslog'], universal_newlines=True)
    #process = subprocess.Popen(['/usr/bin/vmstat', '1', '5'], universal_newlines=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    #pipe = Popen(['/usr/bin/vmstat', '1', '5'], stdout=PIPE, universal_newlines=True, shell=True)

    #if not command_ran:
        #pipe = Popen([ '/mnt/backups/anki/IBCP/applications/number_guesser/number_guesser.py', '-c', '/mnt/backups/anki/IBCP/ibcp.cfg', '--p1', 'vector:0060100c', '--p2', 'vector:0060689b' ], stdout=PIPE, universal_newlines=True, shell=True)
        #pipe = Popen("/mnt/backups/anki/IBCP/applications/number_guesser/number_guesser.py -c /mnt/backups/anki/IBCP/ibcp.cfg --p1 vector:0060100c --p2 vector:0060689b", stdout=PIPE, universal_newlines=True, shell=False)
        #pipe = Popen("/mnt/backups/anki/IBCP/psimple/app1/wrapper.sh", stdout=PIPE, universal_newlines=True, shell=True)



    #window['-OUTPUT-'].update(payload, append=True)
    #window.Refresh()

    #output_splitlines = output.stdout.splitlines()

    #for record in output_splitlines:
    #    window['-OUTPUT-'].update(record + "\n", append=True)


    #output_splitlines = output.split("\n")

    #for record in output_splitlines:
    #    window['-OUTPUT-'].update(record)



    #command_ran = True
    time.sleep(0.1)

window.close()
