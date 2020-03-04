#!/usr/bin/python3

import getopt
import sys
import re
import stomp

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

def the_application(the_robot, serial_number):
    list_of_robots_in_game = []
    enough_players = False

    conn.subscribe(destination='/queue/' + serial_number, id=1, ack='auto')

    while not enough_players:
        # subscribe and get message of queue if command==room,payload=room_name

        for message in message_queue:
            to_robot = msg.group(1)
            from_robot = msg.group(3)
            command = msg.group(5)
            payload = msg.group(7)

            #if command == "join_room":
                #fjdksl


            #if (len(list_robots_to_play) == 2):
            #enough_players = True

    # now start real game:

    if cozmo_supported:
        the_robot.say_text("SYN").wait_for_completed()

    elif vector_supported:
        the_robot.behavior.say_text("SYN")

# Begin main code:
cozmo_supported = False
vector_supported = False

serial_number_robot = ""

opts, args = getopt.getopt(sys.argv[1:], 's:')

for opt, arg in opts:
    if opt == "-s":
        serial_number_robot = arg

if not serial_number_robot:
    print ("Usage: conversation_multi_backend.py -s serial_number")
    exit(1)

try:
    import cozmo
    cozmo_supported = True
    import cozmo
    print ("cozmo sdk found")

    def cozmo_program(robot: cozmo.robot.Robot):
        the_application(robot, serial_number_robot)
        #robot.say_text("Hello World").wait_for_completed()

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
    except:
        print ("Trouble running cozmo code")

elif vector_supported:
    try:
        def vector_code():
            args = anki_vector.util.parse_command_args()
            with anki_vector.Robot(args.serial) as robot:

                #robot.behavior.say_text("Hello World")
                the_application(robot, serial_number_robot)
    except:
        print ("Trouble running vector code")
else:
    print ("No supported robots found!")


if __name__ == '__main__':
    if vector_supported:
        vector_code()
