#!/usr/bin/python3

import time
import sys
import stomp
import re
from signal import signal, SIGINT

class MyListener(stomp.ConnectionListener):
    def on_error(self, headers, message):
        print('received an error "%s"' % message)

    def on_message(self, headers, message):
        print('received a message "%s"' % message)

        to = ""
        command = ""
        payload = ""

        match_object = re.search('(.*?)(:)(.*?)(:)(.*?)(:)(.*)', message)

        if match_object:
            to_robot = match_object.group(1)
            from_robot = match_object.group(3)
            command = match_object.group(5)
            payload = match_object.group(7)

            conn.send(body=to_robot + ':' + from_robot + ':' + command + ':' + payload, destination='/queue/' + to_robot)


def handler(signal_received, frame):
    print ('ctrl-c caught, cleaning up.')

    conn.disconnect()
    exit(0)

if __name__ == '__main__':
    signal(SIGINT, handler)

conn = stomp.Connection()
conn.set_listener('', MyListener())
conn.start()
conn.connect('admin', 'admin', wait=True)

conn.subscribe(destination='/queue/dispatcher', id=1, ack='auto')

initial_run_complete = False

#conn.send(body='robot3 here', destination='/queue/robot3')

print ("IBCP dispatcher running...")

while 1:


    time.sleep(1)
