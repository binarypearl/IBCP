#!/usr/bin/python3

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
    db_cursor.execute('create table ibcp_robots (serial_number TEXT PRIMARY KEY, model TEXT, model_and_serial_number TEXT)')

    db_connection.commit()

# Begin main code:
message_queue = []

initial_instructions = "Welcome to IBCP!  To get started, do 2 things:\n\n" + "1. Edit -> Preferences and set the MQ server\n" + "2. Register at least one robot serial number"

player_one_serial = ""
player_two_serial = ""
mq_server = ""
mq_port = ""
mq_connected = False

print ("Debug1: " + os.path.dirname(os.path.realpath(__file__)))
print ("Debug2: " + sys.path[0])

# DB:
current_directory = os.getcwd()

db_connection = sqlite3.connect(current_directory + "/ibcp.db")
db_cursor = db_connection.cursor()

if (os.stat(current_directory + "/ibcp.db").st_size == 0):
    print ("Need to create tables")
    create_initial_tables(db_connection)

else:
    print ("ibcp.db exists, no need to create")

sg.theme('Dark Blue 3')

# ------ Menu Definition ------ #
menu_def = [['&File', ['E&xit']],
            ['&Edit', ['Preferences'] ],
            ['&Help', '&About...'], ]

layout_main =    [
            [sg.Menu(menu_def, tearoff=True)],
            [
                sg.Text('Welcome to IBCP huamn interface!', size=(70, 1)),
                sg.Text('MQ server info: ', size=(16, 1), key='-MQSERVERINFOLABEL-'),
                sg.Text('', size=(20, 1), key='-MQSERVERINFODATA-')],
            [sg.Multiline(default_text='', size=(199, 40), autoscroll=True, do_not_clear=True, enter_submits=True, key='-OUTPUT-')],
            [
                sg.Multiline(default_text=initial_instructions, size=(64, 10), autoscroll=True, do_not_clear=True, enter_submits=True, key='-INSTRUCTIONS-'),
                sg.Listbox(default_values='', values='', size=(64, 10), key='-ROBOTS-'),
                sg.Listbox(default_values='', values='', size=(30, 10), key='-APPS-'),
                sg.Listbox(default_values='', values='', size=(30, 10), key='-APPOPTIONS')
            ],
            [
                sg.Text('Enter some input', size=(66, 1)),
                sg.Text('Model:', size=(5,1)),
                sg.Combo(['vector', 'cozmo', 'human'], default_value='vector', key='-ROBOTMODEL-', size=(6, 1)),
                sg.Text('Serial number:', size=(12, 1)),
                sg.InputText('', key='-SERIALNUMBER-', size=(9, 1)),
                sg.Button('Register'),
                sg.Button('Unregister')
            ],
            [
                sg.Text('Guess a number', size=(15, 1)), sg.InputText('', key='-INPUT-', size=(10, 1)),

            ],
            [sg.Submit(), sg.Cancel()]
            ]

window = sg.Window('IBCP version 0.2', layout_main, resizable=True)
window.Finalize()

# Lets try to populate mq server data here:
db_cursor.execute("select * from ibcp_config where config_item='mq_config'")

rows = db_cursor.fetchall()

for row in rows:
    mq_server = row[1]
    mq_port = row[2]

mq_server_port = mq_server + ":" + mq_port

print ("What is mq_server_port: " + mq_server_port)

window['-MQSERVERINFODATA-'].update(mq_server_port)

output_list = []

command_ran = False

# Upon start of app, populate the Listbox of registered robots:
db_cursor.execute("select model_and_serial_number from ibcp_robots order by rowid")
rows = db_cursor.fetchall()

window['-ROBOTS-'].update(rows)

while True:
    event_main, values_main = window.read()
    print ("Are we in True loop?")

    if mq_server != '':
        # Create connection to MQ server.
        try:
            # IP and port of MQ server.  Defined in ibcp.cfg.
            stomp_conn = stomp.Connection([(mq_server, mq_port)])
            stomp_conn.set_listener('', MyListener())
            mq_connected = True

            # This is weird, when apps try to create their own username/password mechanims and it's just
            # like, what were they thinking?  I think I just created admin/admin in here and it works.
            # Really secure, but...at least it works.
            stomp_conn.connect('admin', 'admin', wait=True)

        except Exception as e:
            #print ("error: " + str(e))
            print ("Will try connecting to mq server in 1 second...")
            time.sleep(1)

    # Look for robots to register:
    if event_main == "Register":
        # add serial number to database:
        # BREAKPOINT for now
        serial_number = values_main['-SERIALNUMBER-']
        robot_model = values_main['-ROBOTMODEL-']

        db_cursor.execute("select count(*) from ibcp_robots where serial_number='" + serial_number + "'")

        rows = db_cursor.fetchall()

        row_count = rows[0]

        print ("what is row_count: ***" + str(row_count[0]) + "***")

        if row_count[0] == 0:
            #insert
            print ("insert statement is: " + "insert into ibcp_robots values ('" + serial_number + "', '" + robot_model + "', '" + robot_model + ":" + serial_number + "')")
            db_cursor.execute("insert into ibcp_robots values ('" + serial_number + "', '" + robot_model + "', '" + robot_model + ":" + serial_number + "')")

        else:
            print ("robot serial number already registered")

        db_connection.commit()

        # Now lets update the window of registered robots.  I believe I want to clear the entire Listbox,
        # select all records, and append them.

        db_cursor.execute("select model_and_serial_number from ibcp_robots order by rowid")
        rows = db_cursor.fetchall()

        window['-ROBOTS-'].update(rows)
        window['-SERIALNUMBER-'].update('')

    if event_main == "Unregister":
        model_and_serial_number = values_main['-ROBOTS-']

        if model_and_serial_number:
            db_cursor.execute("delete from ibcp_robots where model_and_serial_number='" + model_and_serial_number[0][0] + "'")
            db_connection.commit()

            db_cursor.execute("select model_and_serial_number from ibcp_robots order by rowid")
            rows = db_cursor.fetchall()

            window['-ROBOTS-'].update(rows)
            window['-SERIALNUMBER-'].update('')

    if player_one_serial:
        stomp_conn.subscribe(destination='/queue/' + 'ng_output_' + player_one_serial, id=5, ack='auto')

    if player_two_serial:
        stomp_conn.subscribe(destination='/queue/' + 'ng_output_' + player_two_serial, id=6, ack='auto')

    if event_main == "Preferences":

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


        event_preferences, values_preferences = preferences_window.read()

        while True:
            print ("What is event_preferences before read: " + str(event_preferences))
            print ("What is values_preferences before read: " + str(values_preferences))

            if event_preferences == 'Set':
                mq_server = values_preferences['-MQSERVER-']
                mq_port = values_preferences['-MQPORT-']

                # First we have to see if the record exists:
                #db_connection = sqlite3.connect(current_directory + "/ibcp.db")
                #db_cursor = db_connection.cursor()
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

            event_preferences, values_preferences = preferences_window.read(timeout=1000)



    print ("What is event_main before read: " + str(event_main))
    print ("What is values_main before read: " + str(values_main))

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

    if event_main is None or event_main == 'Exit' or event_main == 'Cancel':
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

    event_main, values_main = window.read(timeout=1000)

window.close()
