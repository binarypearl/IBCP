#!/usr/bin/python3

import sys
import re
import getopt
import stomp
import time
import requests
from sys import platform

from subprocess import Popen, PIPE, STDOUT
from signal import signal, SIGINT

class MyListener(stomp.ConnectionListener):
    def on_error(self, headers, message):
        print('received an error "%s"' % message)

    def on_message(self, headers, message):
        print('received a message "%s"' % message)
        global message_queue
        global ack_info

        print ("DEBUG message-id: " + str(headers['message-id']))
        print ("DEBUG subscription: " + str(headers['subscription']))

        match_object = re.search('(.*?)(:)(.*?)(:)(.*?)(:)(.*)', message)

        if match_object:
            message_queue.append(match_object)
            ack_info['message-id'] = headers['message-id']
            ack_info['subscription'] = headers['subscription']

def handler(signal_received, frame):
    print ('ctrl-c caught, cleaning up.')

    conn.disconnect()
    exit(0)

# main code:
message_queue = []
string_robot_to_start_play = ""
list_robots_to_play = []
request_confirmed = False
ack_info = {}
list_of_potential_robots = []
config_file = ""
linux_path = ""
windows_path = ""
mac_path = ""
final_path = ""
slash_char = ''

opts, args = getopt.getopt(sys.argv[1:], 's:c:')

for opt, arg in opts:
    if opt == "-s":
        string_robot_to_start_play = arg

    elif opt == "-c":
        config_file = arg

if not string_robot_to_start_play or not config_file:
    print ("Usage: conversation_multi.py -s comma_separated_list_of_serial -c config_file")
    exit(1)

# Solve this hard coded path later:
print ("What is config_file: " + config_file)

try:
    config_file_object = open(config_file, "r")

except:
    print ("Couldn't open config file")
    exit(1)

config_file_lines = config_file_object.readlines()

for record in config_file_lines:
    match_object = re.search('(.*?)(=)(.*)', record)

    if match_object.group(1) == "linux_application_path":
        linux_path = match_object.group(3)
        linux_path = linux_path.replace('\'', '')
        slash_char = '/'

    elif match_object.group(1) == "windows_application_path":
        windows_path = match_object.group(3)
        windows_path = windows_path.replace('\'', '')
        slash_char = '\\'

    elif match_object.group(1) == "mac_path":
        mac_path = match_object.group(3)
        mac_path = mac_path.replace('\'', '')
        slash_char = '/'

if sys.platform.startswith('linux'):
    final_path = linux_path

elif sys.platform.startswith('win32'):
    final_path = windows_path

elif sys.platform.startswith('darwin'):
    final_path = mac_path

else:
    print ("Unsupported platform: " + platform)
    exit(2)

print ("what is final_path: " + final_path)

# Lets see if we can get list of availiable robots from file:
file_object = open(final_path + "bots.txt", "r")

records = file_object.readlines()

for record in records:
    record = record.rstrip('\n')
    list_of_potential_robots.append(record)

try:
    conn = stomp.Connection([('192.168.1.153', 61613)])
    conn.set_listener('', MyListener())

    conn.connect('admin', 'admin', wait=True)

except Exception as e:
    print ("error: " + str(e))

# Convert csv into python list (This for passed in comma separated values):
#list_robots_to_play = list(string_robots_to_play.split(","))
# string_robot_to_start_play

for potential_robot in list_of_potential_robots:
    #conn.send(body=to_robot + ':' + "system" + ':' + "join_room" + ':' + room, destination='/queue/' + room)

    # Send a message to all other robots that might be able to play.  Don't send a message to ourselves.
    if not potential_robot == string_robot_to_start_play:
        conn.send(body=potential_robot + ":" + string_robot_to_start_play + ':' + "play_request" + ":" + "conversation_multi", destination="/queue/" + potential_robot)

        #process_robot = Popen(['/mnt/backups/anki/IBCP/applications/conversation_multi/conversation_multi_backend.py', '-s', to_robot],
        #                        stdout=PIPE, stderr=PIPE)

        #stdout, stderr = process_robot.communicate()

    elif potential_robot == string_robot_to_start_play:
        print ("Staring backend for initial robot...")
        process_robot = Popen([final_path + slash_char + 'applications' + slash_char + 'conversation_multi' + slash_char +
                                'conversation_multi_backend.py', '-s', string_robot_to_start_play], stdout=PIPE, stderr=PIPE)

        stdout, stderr = process_robot.communicate()

    for message in message_queue:
        to_robot = message.group(1)
        from_robot = message.group(3)
        command = message.group(5)
        payload = message.group(7)

        if command == "play_response" and payload == "yes":
            print ("We send message to robot saying we want to play game")

            process_robot = Popen([final_path + slash_char + 'applications' + slash_char + 'conversation_multi' + slash_char +
                                    'conversation_multi_backend.py', '-s', to_robot], stdout=PIPE, stderr=PIPE)

            stdout, stderr = process_robot.communicate()
            conn.send(body=from_robot + ":" + to_robot + ':' + "play_yes" + ":" + "conversation_multi", destination="/queue/" + from_robot)

        else:
            print ("Waiting for another robot who wants to play...")

            time.sleep(1)



    #print ("stdout is: " + stdout.decode('utf-8'))
