#!/usr/bin/python3

# This is the robot code script.

import time
import sys
import stomp
import re
import anki_vector
from signal import signal, SIGINT

first_robot = "0060100c"
second_robot = "0060689b"
message_queue = []

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
    #message_queue = []

    app_active = True

    args = anki_vector.util.parse_command_args()
    with anki_vector.Robot(args.serial) as robot:

        conn = stomp.Connection()
        conn.set_listener('', MyListener())
        conn.start()
        conn.connect('admin', 'admin', wait=True)

        conn.subscribe(destination='/queue/' + args.serial, id=1, ack='auto')

        print ("robot queue script running...")

        while app_active:
            for msg in message_queue:
                to_robot = msg.group(1)
                from_robot = msg.group(3)
                command = msg.group(5)
                payload = msg.group(7)

                #print ("DEBUG from_robot: " + from_robot)
                #print ("DEBUG to_robot: " + to_robot)
                #print ("DEBUG command: " + command)
                #print ("DEBUG payload: " + payload)

                # Here is where we begin the actual application code:
                if command == "say" and payload == "SYN":
                    robot.behavior.say_text("SYN")
                    conn.send(body=second_robot + ":" + first_robot + ":" + "said" + ":" + "SYN", destination="/queue/" + second_robot)

                elif command == "said" and payload == "SYN":
                    robot.behavior.say_text("SYNACK")
                    conn.send(body=first_robot + ":" + second_robot + ":" + "say" + ":" + "SYNACK", destination="/queue/" + first_robot)

                elif command == "say" and payload == "SYNACK":
                    robot.behavior.say_text("ACK")
                    conn.send(body=second_robot + ":" + first_robot + ":" + "said" + ":" + "ACK", destination="/queue/" + second_robot)

                elif command == "said" and payload == "ACK":
                    robot.behavior.say_text("Three way handshake complete!")
                    conn.send(body=first_robot + ":" + first_robot + ":" + "ENDAPP" + ":" + "NULL", destination="/queue/" + first_robot)
                    conn.send(body=second_robot + ":" + second_robot + ":" + "ENDAPP" + ":" + "NULL", destination="/queue/" + second_robot)

                elif command == "ENDAPP":
                    app_active = False


                #else
                #    robot.behavior.say_text("SYN ACK")

                #if (command == "say"):
                #    if (re.search("hello", payload, re.IGNORECASE)):
                #        robot.behavior.say_text("Hello " + from_robot)



                message_queue.remove(msg)

            time.sleep(1)


# Actual main code...
if __name__ == '__main__':
    signal(SIGINT, handler)
    robot_code()
