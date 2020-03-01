#!/usr/bin/python3

import time
import sys
import stomp
import re
import anki_vector
from signal import signal, SIGINT

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

def robot_code():
    message_queue = []

    args = anki_vector.util.parse_command_args()
    with anki_vector.Robot(args.serial) as robot:

        conn = stomp.Connection()
        conn.set_listener('', MyListener())
        conn.start()
        conn.connect('admin', 'admin', wait=True)

        conn.subscribe(destination='/queue/' + args.serial, id=1, ack='auto')

        #initial_run_complete = False

        print ("robot queue script running...")

        while 1:
            #if not initial_run_complete:
            #print("robot 2 waiting to say hi back to robot 1...")
            #robot.behavior.say_text("Hello robot2!")

            for msg in message_queue:
                to_robot = msg.group(1)
                from_robot = msg.group(3)
                command = msg.group(5)
                payload = msg.group(7)

                #print ("DEBUG from_robot: " + from_robot)
                #print ("DEBUG to_robot: " + to_robot)
                #print ("DEBUG command: " + command)
                #print ("DEBUG payload: " + payload)

                #if (command == "say"):
                #    if (re.search("hello", payload, re.IGNORECASE)):
                #        robot.behavior.say_text("Hello " + from_robot)



                message_queue.remove(msg)

            time.sleep(1)


# Actual main code...
if __name__ == '__main__':
    signal(SIGINT, handler)
    robot_code()
