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

        match_object = re.search('(.*?)(:)(.*?)(:)(.*?)(:)(.*)', message)

        if match_object:
            message_queue.append(match_object)

def handler(signal_received, frame):
    print ('ctrl-c caught, cleaning up.')

    #conn.disconnect()
    exit(0)

def the_application(robot1, robot1_model, robot2, robot2_model, player_one_serial, player_two_serial):
    try:
        conn = stomp.Connection([('192.168.1.153', 61613)])
        conn.set_listener('', MyListener())

        conn.connect('admin', 'admin', wait=True)

    except Exception as e:
        print ("error: " + str(e))

    play_yes = False
    game_complete = False
    initial_send = False
    player_one_serial_saved = player_one_serial

    print ("player_one_serial is: " + player_one_serial)
    print ("player_two_serial is: " + player_two_serial)

    # subscribe to our queue if we have a robot object:
    if player_one_serial:
        conn.subscribe(destination='/queue/' + player_one_serial, id=1, ack='auto')
        #conn.subscribe(destination='/queue/' + conversation_multi, id=3, ack='auto')

        print ("player_one_serial just subscribed to /queue/" + player_one_serial)

        conn.send(body='anyone' + ":" + player_one_serial + ':' + "play_request" + ":" +
                    "conversation_multi", destination="/queue/" + "conversation_multi")

        print (player_one_serial + " just send a message to: " + "anyone" +
                " with comand=play_request and payload=conversation_multi to /queue/" + "conversation_multi")

    if player_two_serial:
        conn.subscribe(destination='/queue/' + player_two_serial, id=2, ack='auto')
        conn.subscribe(destination='/queue/' + 'conversation_multi', id=3, ack='auto')

        print ("player_two_serial: " + player_two_serial + " just subscribed to /queue/" + player_two_serial +
                " and " + "/queue/" + "conversation_multi")

    while not game_complete:
        print ("game loop begin: ")
        print ("game_complete: " + str(game_complete))
        print ("what is player_one_serial: " + player_one_serial)
        print ("what is player_two_serial: " + player_two_serial)
        print ("what is play_yes: " + str(play_yes))
        print ("Now looking at our message_queue: ")
        print ("\n")

        for message in message_queue:
            print ("We have a message: " + str(message))
            to_robot = message.group(1)
            from_robot = message.group(3)
            command = message.group(5)
            payload = message.group(7)

            print ("to_robot: " + to_robot)
            print ("from_robot: " + from_robot)
            print ("command: " + command)
            print ("payload: " + payload)

            if not play_yes:
                print ("We are in if not play_yes code")
                print ("player_one_serial: " + player_one_serial)
                print ("player_two_serial: " + player_two_serial)
                print ("Now we test if command == play_request: ")

                if command == "play_request" and player_one_serial:
                    play_yes = True
                    print ("command does = play_request and player_one_serial has something.")

                elif command == "play_request" and player_two_serial:
                    play_yes = True
                    print ("command does = play_request and player_two_serial has something.")

                    conn.send(body=player_two_serial + ":" + from_robot + ':' + "play_request" + ":" +
                                "conversation_multi", destination="/queue/" + from_robot)

                    print ("because we are player_two_serial, we just sent a message: " +
                            "from_robot: " + player_two_serial + " to: " + from_robot +
                            " with the command play_request with the payload conversation_multi" +
                            " to the destination /queue/" + from_robot)

                if not player_one_serial:
                    player_one_serial = from_robot

                if not player_two_serial:
                    player_two_serial = to_robot

                print ("What is modified player_one_serial: " + player_one_serial)
                print ("What is modified player_two_serial: " + player_two_serial)

            elif play_yes:
                # I guess now we play game:
                if not initial_send:
                    print ("player_one_serial_saved: " + player_one_serial_saved)
                    print ("player_one_serial: " + player_one_serial)

                    if player_one_serial_saved == player_one_serial:
                        conn.send(body=player_one_serial + ":" + player_two_serial + ":" + "say" + ":" + "SYN", destination="/queue/" + player_one_serial)
                        initial_send = True
                    else:
                        initial_send = True

                    print ("initial_send is now: " + str(initial_send))

                if command == "say" and payload == "SYN":
                    if robot1_model == "comzo":
                        robot1.say_text("SYN", duration_scalar=0.6).wait_for_completed()
                    elif robot1_model == "vector":
                        robot1.behavior.say_text("SYN")

                    conn.send(body=player_two_serial + ":" + player_one_serial + ":" + "said" + ":" + "SYN", destination="/queue/" + player_two_serial)

                elif command == "said" and payload == "SYN":
                    if robot2_model == "cozmo":
                        robot2.say_text("SYNACK", duration_scalar=0.6).wait_for_completed()
                    elif robot2_model == "vector":
                        robot2.behavior.say_text("SYNACK")

                    #print ("exit for examination...")
                    #exit(3)

                    conn.send(body=player_one_serial + ":" + player_two_serial + ":" + "say" + ":" + "SYNACK", destination="/queue/" + player_one_serial)

                elif command == "say" and payload == "SYNACK":
                    if robot1_model == "cozmo":
                        robot1.say_text("ACK", duration_scalar=0.6).wait_for_completed()
                    elif robot1_model == "vector":
                        robot1.behavior.say_text("ACK")

                    conn.send(body=player_two_serial + ":" + player_one_serial + ":" + "said" + ":" + "ACK", destination="/queue/" + player_two_serial)

                elif command == "said" and payload == "ACK":
                    if robot2_model == "cozmo":
                        robot2.say_text("Three way handshake complete!", duration_scalar=0.6).wait_for_completed()
                    elif robot2_model == "vector":
                        robot2.behavior.say_text("Three way handshake complete!")

                    conn.send(body=player_one_serial + ":" + player_two_serial + ":" + "ENDAPP" + ":" + "NULL", destination="/queue/" + player_one_serial)
                    conn.send(body=player_two_serial + ":" + player_one_serial + ":" + "ENDAPP" + ":" + "NULL", destination="/queue/" + player_two_serial)

                elif command == "ENDAPP":
                    game_complete = True

                message_queue.remove(message)

        print ("Waiting for another player...")
        time.sleep(1)

# main code:
message_queue = []
cozmo_supported = False
vector_supported = False
final_path = ""
player_one_serial = ""
player_two_serial = ""

opts, args = getopt.getopt(sys.argv[1:], 'c:', ['p1=', 'p2='])

for opt, arg in opts:
    if opt == "--p1":
        player_one_serial = arg

    elif opt == "--p2":
        player_two_serial = arg

    elif opt == "-c":
        config_file = arg

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


try:
    import cozmo
    cozmo_supported = True
    import cozmo
    print ("cozmo sdk found")

    def cozmo_program(robot: cozmo.robot.Robot):
        # ***NOTE***!  At a minimum, test if p1 or p2 and pass in appropriate robot object
        if player_one_serial:
            the_application(robot, "cozmo", "", "", player_one_serial, player_two_serial)

        elif player_two_serial:
            the_application("", "", robot, "cozmo", player_one_serial, player_two_serial)


except ModuleNotFoundError:
    print ("cozmo sdk not found, cozmo robots are not supported on this computer.")

try:
    import anki_vector
    vector_supported = True
    print ("vector sdk found")

except ModuleNotFoundError:
    print ("vector sdk not found, vector robots are not supported on this computer.")

if cozmo_supported:
    try:
        cozmo.run_program(cozmo_program)
    except Exception as e:
        print ("Trouble running cozmo code: " + str(e))

elif vector_supported:
    try:
        def vector_code():
            print ("p1: " + player_one_serial)
            print ("p2: " + player_two_serial)

            if player_one_serial and player_two_serial:
                with anki_vector.Robot(player_one_serial) as robot1:
                    with anki_vector.Robot(player_two_serial) as robot2:
                        the_application(robot1, "vector", robot2, "vector", player_one_serial, player_two_serial)

            elif player_one_serial and not player_two_serial:
                with anki_vector.Robot(player_one_serial) as robot1:
                    the_application(robot1, "vector", "", "", player_one_serial, player_two_serial)

            elif not player_one_serial and player_two_serial:
                with anki_vector.Robot(player_two_serial) as robot2:
                    the_application("", "", robot2, "vector" ,player_one_serial, player_two_serial)

    except:
        print ("Trouble running vector code")
else:
    print ("No supported robots found!")

if __name__ == '__main__':
    if vector_supported:
        vector_code()
