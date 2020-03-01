#!/usr/bin/python3

# NO robot code here.
# Use getopt to take parameters.

import time
import sys
import stomp
import re
import anki_vector
from signal import signal, SIGINT

first_robot = "0060100c"
second_robot = "0060689b"

# This class may or may not be needed in send...
class MyListener(stomp.ConnectionListener):
    def on_error(self, headers, message):
        print('received an error "%s"' % message)

    def on_message(self, headers, message):
        print('received a message "%s"' % message)
        global message_queue

        match_object = re.search('(.*?)(:)(.*?)(:)(.*?)(:)(.*)', message)

        if match_object:
            message_queue.append(match_object)


def handler(signal_received, frame):
    print ('ctrl-c caught, cleaning up.')

    conn.disconnect()
    exit(0)

# create connection to MQ server...
conn = stomp.Connection()
conn.set_listener('', MyListener())
conn.start()
conn.connect('admin', 'admin', wait=True)

# SYN

# template:
#conn.send(body=to_robot + ':' + from_robot + ':' + command + ':' + payload, destination='/queue/' + to_robot)
conn.send(body=second_robot + ':' + first_robot + ':' + "say" + ':' + "SYN", destination='/queue/' + first_robot)
#conn.send(body=second_robot + ":" + first_robot + ':' + "say" + ':' + "SYN", destination='/queue/' + second_robot)

# SYNACK


# ACK
