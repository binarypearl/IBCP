#!/usr/bin/python3

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License in the file LICENSE.txt or at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import PySimpleGUI as sg
import subprocess
import os
import time
import sys
import stomp                # For Apache MQ messaging
import re
import sqlite3
import platform

def connect_to_mq_server(conn):
    if mq_server != '':
        # Create connection to MQ server.
        try:
            # This is weird, when apps try to create their own username/password mechanims and it's just
            # like, what were they thinking?  ActiveMQ defaults to admin/admin in here and it works.
            # Really secure, but...at least it works.
            # Should paramerize this at some point so people can change it to whatever they want.
            stomp_conn.connect('admin', 'admin', wait=True)

            print ("Just connected to stomp")

        except Exception as e:
            # This case needs to be handled better.  If we got here, we have a configured MQ server but
            # it can't connect to it (eg service down or firewall).
            # IBCP will more-or-less hang, but you can still get to preferences to change server ip/port
            # if needed.  But it will be slow, and the rest of the operations (like selecting a game)
            # still look like they are available to be selected.
            print ("Will try connecting to mq server in 1 second...")
            time.sleep(1)

class MyListener(stomp.ConnectionListener):
    def on_error(self, headers, message):
        print('received an error "%s"' % message)

    def on_message(self, headers, message):
        global message_queue

        match_object = re.search('(.*?)(:)(.*?)(:)(.*?)(:)(.*)', message)

        if match_object:
            message_queue.append(match_object)

    def on_disconnected(self, headres, message):
        print ('disconnected from Apache MQ server')
        connect_to_mq_server(self.conn)


def create_initial_tables(db_connection):
    db_cursor = db_connection.cursor()

    db_cursor.execute('create table ibcp_config (config_item TEXT primary key, key TEXT, value TEXT)')
    db_cursor.execute('create table ibcp_robots (serial_number TEXT PRIMARY KEY, model TEXT, model_and_serial_number TEXT)')

    db_connection.commit()

# Begin main code:
message_queue = []

initial_instructions = "Welcome to IBCP!  To get started, do 2 things:\n\n" + "Edit -> Preferences and:\n1. Set the MQ server\n" + "2. Register at least 2 players"

player_one_serial = ""
player_two_serial = ""
mq_server = ""
mq_port = ""
mq_connected = False
list_of_applications = []
p = ""  # subprocess....
counter = 0

# Get the current directory regardless of how ibcp.py was called.
current_directory = os.path.dirname(os.path.realpath(sys.argv[0]))

# DB:
db_connection = sqlite3.connect(current_directory + "/ibcp.db")
db_cursor = db_connection.cursor()

if (os.stat(current_directory + "/ibcp.db").st_size == 0):
    print ("Initial run, need to create tables")
    create_initial_tables(db_connection)

sg.theme('Dark Blue 3')

# ------ Menu Definition ------ #
menu_def = [['&File', ['E&xit']],
            ['&Edit', ['Preferences'] ],
            ['&Help', '&About...'], ]

frame_layout_output_main = [
    [sg.Multiline(default_text='', size=(190, 40), autoscroll=True, do_not_clear=True, enter_submits=True, key='-OUTPUT-')]
]

frame_layout_apps_main = [
    [sg.Listbox(default_values='', values='', size=(60, 38), key='-APPS-', enable_events=True)],
]

frame_layout_player_select_main = [
    [sg.Text('Player 1', size=(8, 1), key='-P1LABEL-'), sg.Combo('', key='-P1CHOICE-', size=(15, 1), enable_events=True, readonly=True)],
    [sg.Text('Player 2', size=(8, 1), key='-P2LABEL-'), sg.Combo('', key='-P2CHOICE-', size=(15, 1), enable_events=True, readonly=True)],
    [sg.Button('Play')],
]

frame_layout_actions_main = [
    [sg.Multiline(default_text=initial_instructions, size=(64, 5), autoscroll=True, do_not_clear=True, enter_submits=True, key='-INSTRUCTIONS-')],
    [sg.Text('', size=(40, 1), key='-HUMANINPUTTEXT-', auto_size_text=False, justification='left', visible=False)],
    [sg.InputText('', key='-HUMANINPUTFIELD-', size=(9, 1), visible=False)],
    [sg.Button('Submit', key='-HUMANINPUTSUBMITBUTTON-', visible=False)]
]

frame_layout_status_main = [
    [sg.Text('MQ server info: ', size=(16, 1), key='-MQSERVERINFOLABEL-')],
    [sg.Text('', size=(20, 1), key='-MQSERVERINFODATA-')]
]

frame_layout_operations_main = [
    [sg.Exit()]
]

frame_layout_main = [
    [sg.Menu(menu_def, tearoff=True)],
    [sg.Frame('Output Viewer', frame_layout_output_main, key='-OUTPUTFRAME-'), sg.Frame('Applications', frame_layout_apps_main, key='-APPLICATIONSFRAME-')],
    [sg.Frame('Player Select', frame_layout_player_select_main, key='-PLAYERSELECTFRAME-'), sg.Frame('Actions', frame_layout_actions_main, key='-ACTIONSFRAME-'), sg.Frame('Status', frame_layout_status_main, key='-STATUSFRAME-')],
    [sg.Frame('Operations', frame_layout_operations_main, key='-OPERATIONSFRAME-')]
]

window = sg.Window('IBCP version 0.2', frame_layout_main, resizable=True)
window.Finalize()

window['-OUTPUTFRAME-'].expand(expand_x=True, expand_y=True)
window['-APPLICATIONSFRAME-'].expand(expand_x=True, expand_y=True)
window['-PLAYERSELECTFRAME-'].expand(expand_x=True, expand_y=True)
window['-ACTIONSFRAME-'].expand(expand_x=True, expand_y=True)
window['-STATUSFRAME-'].expand(expand_x=True, expand_y=True)
window['-OPERATIONSFRAME-'].expand(expand_x=True)

# Lets try to populate mq server data here:
db_cursor.execute("select * from ibcp_config where config_item='mq_config'")

rows = db_cursor.fetchall()

for row in rows:
    mq_server = row[1]
    mq_port = row[2]

mq_server_port = mq_server + ":" + mq_port

window['-MQSERVERINFODATA-'].update(mq_server_port)

output_list = []

command_ran = False

# Get list of available applications:
dir_object_list = os.scandir(current_directory + "/applications")

for dir_object in dir_object_list:
    if dir_object.is_dir():
        list_of_applications.append(dir_object.name)

window['-APPS-'].update(list_of_applications)

event_main, values_main = window.read()

p = "" # hold suprocess return object

connected_to_mq_server = False

# I think what's happening here...is that we are constantly issuing new connections to MQ
# However when I change the logic to just to connect once, the program exits or crashes.
# Re-look at the logic here.  If with luck, maybe this solves are windows hanging issue.

# Initial connection attempt:
stomp_conn = stomp.Connection([(mq_server, mq_port)])
stomp_conn.set_listener('', MyListener())
stomp_conn.connect('admin', 'admin', wait=True)
#connect_to_mq_server(stomp_conn)

# temp...space after is intentional
python3_executable = "oops_python_executable_not_set "

while True:
    if event_main == "-APPS-":
        temp_list = []

        db_cursor.execute("select model_and_serial_number from ibcp_robots order by rowid")
        rows = db_cursor.fetchall()

        for row in rows:
            temp_list.append(row[0])

        window['-P1CHOICE-'].update(values=temp_list)
        window['-P2CHOICE-'].update(values=temp_list)

    if event_main == "Play":
        try:
            print ("DD0")

            if values_main['-APPS-'][0] == "number_guesser":
                print ("DD1")

                db_cursor.execute("select serial_number,model from ibcp_robots where model_and_serial_number='" + values_main['-P1CHOICE-'] + "'")
                rows = db_cursor.fetchall()

                print ("DD2")

                player_one_serial = rows[0][0]
                player_one_model = rows[0][1]

                db_cursor.execute("select serial_number,model from ibcp_robots where model_and_serial_number='" + values_main['-P2CHOICE-'] + "'")
                rows = db_cursor.fetchall()

                print ("DD3")

                player_two_serial = rows[0][0]
                player_two_model = rows[0][1]

                print ("DD4")

                print ("Who is player_one_serial: " + player_one_serial)

                if player_one_serial and player_one_serial != "remote":
                    stomp_conn.subscribe(destination='/queue/' + 'ng_output_' + player_one_serial, id=5, ack='auto')

                print ("DD5")

                if player_two_serial and player_two_serial != "remote":
                    stomp_conn.subscribe(destination='/queue/' + 'ng_output_' + player_two_serial, id=6, ack='auto')

                # Gahhh...python3.8 (at least in Windows) has a bug where is throws an expception on exit with disconnecting.
                # It's throwing my stuff off in Windows I belive, so I'm going to require python3.6.  It's ugggggllyyyy
                # But if it works, then it works.

                print ("BACK END COMMAND IS sort of...: " + "python3 " + current_directory + "/applications/" + values_main['-APPS-'][0] + "/number_guesser.py -s " + mq_server + " -p " + mq_port + " --p1 " + values_main['-P1CHOICE-'] + " --p2 " + values_main['-P2CHOICE-'])

                if platform.system() == 'Windows':
                    python3_executable = "C:\\Users\\shaun\\AppData\\Local\\Programs\\Python\\Python36\\python.exe "
                    print ("Making sure this is Windows...")

                else:
                    python3_executable = "python3 "

                if player_one_model == "remote":
                    p = subprocess.Popen(python3_executable + current_directory + "/applications/" + values_main['-APPS-'][0] + "/number_guesser.py -s " + mq_server + " -p " + mq_port + " --p2 " + values_main['-P2CHOICE-'], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)

                elif player_two_model == "remote":
                    p = subprocess.Popen(python3_executable + current_directory + "/applications/" + values_main['-APPS-'][0] + "/number_guesser.py -s " + mq_server + " -p " + mq_port + " --p1 " + values_main['-P1CHOICE-'], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)

                else:
                    p = subprocess.Popen(python3_executable + current_directory + "/applications/" + values_main['-APPS-'][0] + "/number_guesser.py -s " + mq_server + " -p " + mq_port + " --p1 " + values_main['-P1CHOICE-'] + " --p2 " + values_main['-P2CHOICE-'], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)

                # Lets enable number_guesser specific controls here:
                window['-HUMANINPUTTEXT-'].update(visible=True)
                window['-HUMANINPUTFIELD-'].update(visible=True)
                window['-HUMANINPUTSUBMITBUTTON-'].update(visible=True)

                # Now lets update some parts of the gui:
                if player_one_model == "human":
                    instructions = "Human is player 1.\nEnter a number for player 2 to guess"
                    window['-INSTRUCTIONS-'].update(instructions)

                    window['-HUMANINPUTTEXT-'].update("Enter a number for player 2 to guess:")

                elif player_two_model == "human":
                    instructions = "Human is player 2.\nTry to guess the magic number"
                    window['-HUMANINPUTTEXT-'].update("Try to guess the magic number:")
                    window['-INSTRUCTIONS-'].update(instructions)
        except:
            # Just silently fail for now.  This handles if user pressed play without any bots selected.
            print ("oops play with no bots selected")

    if event_main == "-HUMANINPUTSUBMITBUTTON-":
        if values_main['-APPS-'][0] == "number_guesser":
            human_input_field = window['-HUMANINPUTFIELD-'].Get()

            if human_input_field != "":
                # Eventually do data validation here...
                if player_one_model == "human":
                    stomp_conn.send(body='human' + ":" + player_one_serial + ':' + "set_magic_number" + ":" +
                    human_input_field, destination="/queue/" + "human")

                elif player_two_model == "human":
                    stomp_conn.send(body='human' + ":" + player_two_serial + ':' + "human_guess" + ":" +
                    human_input_field, destination="/queue/" + "human")

                    window['-HUMANINPUTFIELD-'].update(value="")

    if event_main == "Preferences":
        # We need layout_preferences here, because PySimpleGUI complains up a storm
        # if you don't.  It want's a clean layout upon creation of window.  So we define it
        # here before the create so it always gets it's clean slate.  I populate the fields
        # from the database before the user see's it, so that works for me.
        frame_layout_mq_preferences = [
                [sg.Text('MQ Server:', size=(9, 1)), sg.InputText(default_text='', key='-MQSERVER-', size=(16, 1))],
                [sg.Text('MQ port:', size=(9, 1)), sg.InputText(default_text='61613', key='-MQPORT-', size=(7, 1))]
        ]

        frame_layout_register_robot_preferences = [
            [sg.Text('Model:', size=(12,1)), sg.Combo(['vector', 'cozmo', 'human', 'remote'], default_value='vector', key='-ROBOTMODEL-', size=(7, 1), readonly=True)],

            [sg.Text('Serial number:', size=(12, 1)), sg.InputText('', key='-SERIALNUMBER-', size=(9, 1)), sg.Listbox(default_values='', values='', size=(64, 5), key='-ROBOTS-', enable_events=True)],

            [sg.Button('Register'), sg.Button('Unregister')]
        ]

        frame_layout_finish_buttons_preferences = [
            [sg.Button(button_text='Save and Close', key='-SAVEANDCLOSE-'), sg.Button('Cancel')]
        ]

        frame_layout_preferences = [
            [sg.Frame('MQ Settings', frame_layout_mq_preferences)],
            [sg.Frame('Register Robots', frame_layout_register_robot_preferences)],
            [sg.Frame('Operations', frame_layout_finish_buttons_preferences)]
        ]

        preferences_window = sg.Window('Preferences', frame_layout_preferences, resizable=True, location=[800,400])

        preferences_window.Finalize()

        # We do a select to get the current mq_server and mq_port values and populate
        db_cursor.execute("select * from ibcp_config where config_item='mq_config'")

        rows = db_cursor.fetchall()

        for row in rows:
            if row[0] == "mq_config":
                preferences_window['-MQSERVER-'].update(row[1])
                preferences_window['-MQPORT-'].update(row[2])

        # Upon start of app, populate the Listbox of registered robots:
        db_cursor.execute("select model_and_serial_number from ibcp_robots order by rowid")
        rows = db_cursor.fetchall()

        preferences_window['-ROBOTS-'].update(rows)

        event_preferences, values_preferences = preferences_window.read()

        while True:
            if event_preferences == '-SAVEANDCLOSE-':
                mq_server = values_preferences['-MQSERVER-']
                mq_port = values_preferences['-MQPORT-']

                # First we have to see if the record exists:
                db_cursor.execute("select count(*) from ibcp_config")

                rows = db_cursor.fetchall()

                row_count = rows[0]

                if row_count[0] == 0:
                    #insert
                    #print ("insert statement is: " + "insert into ibcp_config values ('mq_config', '" + mq_server + "', '" + mq_port + "')")
                    db_cursor.execute("insert into ibcp_config values ('mq_config', '" + mq_server + "', '" + mq_port + "')")
                else:
                    #print ("update code here")
                    db_cursor.execute("update ibcp_config set key='" + mq_server + "',value='" + mq_port + "' where config_item='mq_config'")

                db_connection.commit()

                preferences_window.close()
                break

            # Look for robots to register:
            if event_preferences == "Register":
                # add serial number to database:
                serial_number = values_preferences['-SERIALNUMBER-']
                robot_model = values_preferences['-ROBOTMODEL-']

                db_cursor.execute("select count(*) from ibcp_robots where serial_number='" + serial_number + "'")

                rows = db_cursor.fetchall()

                row_count = rows[0]

                if row_count[0] == 0:
                    #insert
                    #print ("insert statement is: " + "insert into ibcp_robots values ('" + serial_number + "', '" + robot_model + "', '" + robot_model + ":" + serial_number + "')")
                    db_cursor.execute("insert into ibcp_robots values ('" + serial_number + "', '" + robot_model + "', '" + robot_model + ":" + serial_number + "')")

                else:
                    # Should we have some type of gui message in this case?  Probably.
                    print ("robot serial number already registered")

                db_connection.commit()

                # Now lets update the window of registered robots.  I believe I want to clear the entire Listbox,
                # select all records, and append them.

                db_cursor.execute("select model_and_serial_number from ibcp_robots order by rowid")
                rows = db_cursor.fetchall()

                preferences_window['-ROBOTS-'].update(rows)
                preferences_window['-SERIALNUMBER-'].update('')

            if event_preferences == "Unregister":
                model_and_serial_number = values_preferences['-ROBOTS-']

                if model_and_serial_number:
                    db_cursor.execute("delete from ibcp_robots where model_and_serial_number='" + model_and_serial_number[0][0] + "'")
                    db_connection.commit()

                    db_cursor.execute("select model_and_serial_number from ibcp_robots order by rowid")
                    rows = db_cursor.fetchall()

                    preferences_window['-ROBOTS-'].update(rows)
                    preferences_window['-SERIALNUMBER-'].update('')

                db_connection.commit()

            if event_preferences is None or event_preferences == 'Exit' or event_preferences == 'Cancel' or event_preferences == 'Close':
                preferences_window.close()
                break

            event_preferences, values_preferences = preferences_window.read(timeout=1000)

    # Lets try to populate mq server data here:
    db_cursor.execute("select * from ibcp_config where config_item='mq_config'")

    rows = db_cursor.fetchall()

    for row in rows:
        mq_server = row[1]
        mq_port = row[2]

    mq_server_port = mq_server + ":" + mq_port

    window['-MQSERVERINFODATA-'].update(mq_server_port)

    if event_main is None or event_main == 'Exit' or event_main == 'Cancel':
        db_connection.close()
        print ("closed DB connection")
        break

    if not command_ran:
        print ("number guesser being called here...")
        command_ran = True

    #if command_ran:
        #print ("COMMAND HAS BEEN RAN")


    # This code might not work properly...commenting out for now:
    #try:
        #if p.poll() == None:
            #print ("***************************************process still running...counter = " + counter + "***************************************")
            #counter += 1

    #except:
        #print ("-----------------------------------------process not started yet-----------------------------------------")

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

        to_robot = message.group(1)
        from_robot = message.group(3)
        command = message.group(5)
        payload = message.group(7)

        window['-OUTPUT-'].update(payload + "\n\n", append=True)

        # Remove the MQ message from the message_queue[] list now that we have processed it.
        message_queue.remove(message)

    event_main, values_main = window.read(timeout=400)

window.close()
