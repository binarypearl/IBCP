#!/usr/bin/python3

import sys
import re
import getopt
from subprocess import Popen, PIPE, STDOUT
from signal import signal, SIGINT

def handler(signal_received, frame):
    print ('ctrl-c caught, cleaning up.')

    conn.disconnect()
    exit(0)

# main code:
string_robots_to_play = ""
list_robots_to_play = []

opts, args = getopt.getopt(sys.argv[1:], 's:')

for opt, arg in opts:
    if opt == "-s":
        string_robots_to_play = arg

if not string_robots_to_play:
    print ("Usage: conversation_multi.py -s comma_separated_list_of_serial")
    exit(1)

# Convert csv into python list:
list_robots_to_play = list(string_robots_to_play.split(","))

for robot in list_robots_to_play:
    process_robot = Popen(['/mnt/backups/anki/ibcp/applications/conversation_multi/conversation_multi_backend.py', '-s', robot],
                            stdout=PIPE, stderr=PIPE)

    stdout, stderr = process_robot.communicate()

    #print ("stdout is: " + stdout.decode('utf-8'))
