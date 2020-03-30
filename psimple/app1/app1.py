import PySimpleGUI as sg
import subprocess
from nonblock import nonblock_read
import os
import time
import sys
import stomp                # For Apache MQ messaging
import re
import sqlite3

class MyListener(stomp.ConnectionListener):
    def on_error(self, headers, message):
        print('received an error "%s"' % message)

    def on_message(self, headers, message):
        print('received a message "%s"' % message)
        global message_queue

        match_object = re.search('(.*?)(:)(.*?)(:)(.*?)(:)(.*)', message)

        if match_object:
            message_queue.append(match_object)

def create_initial_tables(db_connection):
    db_cursor = db_connection.cursor()

    db_cursor.execute('create table ibcp_config (config_item TEXT primary key, key TEXT, value TEXT)')
    db_cursor.execute('create table ibcp_robots (serial_number TEXT PRIMARY KEY)')

    db_connection.commit()
    #db_connection.close()

# Begin main code:
message_queue = []

player_one_serial = "00508a44"
player_two_serial = "0060689b"
mq_server = "192.168.1.153"
mq_port = "61613"

# DB:
current_directory = os.getcwd()

db_connection = sqlite3.connect(current_directory + "/ibcp.db")
db_cursor = db_connection.cursor()

if (os.stat(current_directory + "/ibcp.db").st_size == 0):
    print ("Need to create tables")
    create_initial_tables(db_connection)

else:
    print ("ibcp.db exists, no need to create")

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

# ------ Menu Definition ------ #
menu_def = [['&File', ['E&xit']],
            ['&Edit', ['Preferences'] ],
            ['&Help', '&About...'], ]

layout_main =    [
            [sg.Menu(menu_def, tearoff=True)],
            [sg.Text('Welcome to IBCP huamn interface!', size=(50, 1))],
            [sg.Multiline(default_text='', size=(199, 40), autoscroll=True, do_not_clear=True, enter_submits=True, key='-OUTPUT-')],
            [
                sg.Multiline(default_text='Instructions go here', size=(64, 10), autoscroll=True, do_not_clear=True, enter_submits=True, key='-INSTRUCTIONS-'),
                sg.Listbox(default_values='', values='', size=(64, 10), key='-ROBOTS-'),
                sg.Listbox(default_values='', values='', size=(64, 10), key='-APPS-')
            ],
            [
                sg.Text('Enter some input', size=(66, 1)),
                sg.Text('MQ server info: ', size=(16, 1), key='-MQSERVERINFOLABEL-'),
                sg.Text('', size=(20, 1), key='-MQSERVERINFODATA-')
            ],
            [
                sg.Text('Guess a number', size=(15, 1)), sg.InputText('', key='-INPUT-', size=(10, 1)),

            ],
            [sg.Submit(), sg.Cancel()]
            ]

print ("STEP 0")
window = sg.Window('IBCP version 0.2', layout_main, resizable=True)
window.Finalize()
print ("STEP 1")

# Lets try to populate mq server data here:
db_cursor.execute("select * from ibcp_config where config_item='mq_config'")

rows = db_cursor.fetchall()

for row in rows:
    #print ("row is: " + str(row))

    mq_server = row[1]
    mq_port = row[2]

mq_server_port = mq_server + ":" + mq_port

print ("What is mq_server_port: " + mq_server_port)

window['-MQSERVERINFODATA-'].update(mq_server_port)

#event, values = window.read()

print ("STEP 2")

output_list = []

command_ran = False

while True:
    event, values = window.read()
    print ("Are we in True loop?")

    if event == "Preferences":

        # We need layout_preferences here, because PySimpleGUI complains up a storm
        # if you don't.  It want's a clean layout upon creation of window.  So we define it
        # here before the create so it always gets it's clean slate.  I populate the fields
        # from the database before the user see's it, so that works for me.
        layout_preferences = [
            [sg.Text('MQ Server:', size=(9, 1)), sg.InputText(default_text='', key='-MQSERVER-', size=(16, 1))],
            [sg.Text('MQ port:', size=(10, 1)), sg.InputText(default_text='61613', key='-MQPORT-', size=(7, 1))],
            [sg.Button('Set'), sg.Button('Close')]
        ]

        preferences_window = sg.Window('Preferences', layout_preferences, resizable=True, location=[800,400])

        preferences_window.Finalize()

        # I think here we do a select to get the current mq_server and mq_port values and populate
        # the fields with the data.
        #db_connection = sqlite3.connect(current_directory + "/ibcp.db")
        #db_cursor = db_connection.cursor()
        db_cursor.execute("select * from ibcp_config where config_item='mq_config'")

        rows = db_cursor.fetchall()

        for row in rows:
            if row[0] == "mq_config":
                preferences_window['-MQSERVER-'].update(row[1])
                preferences_window['-MQPORT-'].update(row[2])


        event_preferences, event_values = preferences_window.read()

        while True:
            print ("What is event_preferences before read: " + str(event_preferences))
            print ("What is event_values before read: " + str(event_values))

            if event_preferences == 'Set':
                mq_server = event_values['-MQSERVER-']
                mq_port = event_values['-MQPORT-']

                # First we have to see if the record exists:
                db_connection = sqlite3.connect(current_directory + "/ibcp.db")
                db_cursor = db_connection.cursor()
                db_cursor.execute("select count(*) from ibcp_config")

                rows = db_cursor.fetchall()

                row_count = rows[0]

                print ("what is row_count: ***" + str(row_count[0]) + "***")

                if row_count[0] == 0:
                    #insert
                    print ("insert statement is: " + "insert into ibcp_config values ('mq_config', '" + mq_server + "', '" + mq_port + "')")
                    db_cursor.execute("insert into ibcp_config values ('mq_config', '" + mq_server + "', '" + mq_port + "')")
                else:
                    print ("update code here")
                    db_cursor.execute("update ibcp_config set key='" + mq_server + "',value='" + mq_port + "' where config_item='mq_config'")


                db_connection.commit()

            if event_preferences is None or event_preferences == 'Exit' or event_preferences == 'Cancel' or event_preferences == 'Close':
                preferences_window.close()
                break

            event_preferences, event_values = preferences_window.read(timeout=1000)



    print ("What is event before read: " + str(event))
    print ("What is values before read: " + str(values))

    # Lets try to populate mq server data here:
    db_cursor.execute("select * from ibcp_config where config_item='mq_config'")

    rows = db_cursor.fetchall()

    for row in rows:
        #print ("row is: " + str(row))

        mq_server = row[1]
        mq_port = row[2]

    mq_server_port = mq_server + ":" + mq_port

    print ("What is mq_server_port: " + mq_server_port)

    window['-MQSERVERINFODATA-'].update(mq_server_port)

    if event is None or event == 'Exit' or event == 'Cancel':
        break

    if not command_ran:
        print ("number guesser being called here...")
        #p = subprocess.Popen("/mnt/backups/anki/IBCP/applications/number_guesser/number_guesser.py -c /mnt/backups/anki/IBCP/ibcp.cfg --p1 vector:00508a44 --p2 vector:0060689b", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
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

    time.sleep(0.1)

    event, values = window.read(timeout=1000)

window.close()
