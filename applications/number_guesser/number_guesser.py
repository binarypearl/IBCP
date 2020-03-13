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

import sys                  # exit(), possibly other stuff
import re                   # Regular expressions, my favorite
import os                   # Dunno...might not be using this
import getopt               # Command line processing
import stomp                # For Apache MQ messaging
import time                 # For sleeping.  I use a 1 second delay before polling for MQ messages
import traceback            # Gives stack trace in non normal situations
from sys import platform    # Determine if we are Linux Windows or Mac

# This gets our number_guesser_engine class so we can create an object from it
from number_guesser_engine import number_guesser_engine

# Trapping ctrl-c, which I'm pretty sure is broken and not quite working yet.
from signal import signal, SIGINT

# This is the code for receiving MQ messages.  I belive it comes from the author who wrote
# Stomp.  Basically we have a callback routine called on_message() when we get a message.
# But, we don't have access to a robot object here.  So I add the contents of the message to a
# python list called message_queue[].  When I'm ready and have a robot object, then I process
# the messsages in the message_queue.  It's a global list, which by all modern computer science
# theory is a bad idea.  There may be better ways, but it's a matter of getting something working
# and improving on it later.  The biggest risk is it's almost certainly not thread safe.
# The most practical limitation would be running 2+ versions of this script on the same computer
# would almost certainly have issues.  But running this script on 2 different computers is
# fine and works.
class MyListener(stomp.ConnectionListener):
    def on_error(self, headers, message):
        print('received an error "%s"' % message)

    def on_message(self, headers, message):
        print('received a message "%s"' % message)
        global message_queue

        match_object = re.search('(.*?)(:)(.*?)(:)(.*?)(:)(.*)', message)

        if match_object:
            message_queue.append(match_object)

# Handle ctrl-c, not currently working, will fix later.
def handler(signal_received, frame):
    print ('ctrl-c caught, cleaning up.')

    #conn.disconnect()
    exit(0)

# This is the actual application code.  If we get to here, we have 1 or 2 robot objects defined.
# If you are interested in writing your own game with IBCP, and don't want to mess with the details
# of defining cozmo or vector, this is the function you would want to modify.  This is essentailly
# the last thing that is called in this overall script.

# robot1 and robot2 could be a Cozmo or Vector robot object.  the robotN_model parameters are
# either cozmo or vector, depending on what was passed in at the command line.  The serial numbers
# are well, the robots serial number.  Vector's is written on the bottom of the physical robot.
# Cozmo serial number can be found in the Cozmo app when connected to said robot.
def the_application(robot1, robot1_model, robot2, robot2_model, player_one_serial, player_two_serial):
    try:
        # This IP needs to go into config file...
        # But this is the IP and port of Apache MQ.  61613 is the port for Stomp
        conn = stomp.Connection([('192.168.1.153', 61613)])
        conn.set_listener('', MyListener())

        # This is weird, when apps try to create their own username/password mechanims and it's just
        # like, what were they thinking?  I think I just created admin/admin in here and it works.
        # Really secure, but...at least it works.
        conn.connect('admin', 'admin', wait=True)

    except Exception as e:
        print ("error: " + str(e))

    # This is our number guesser engine object:
    engine_object = number_guesser_engine()

    # Call initialize_game() and get the magic number.  This code allows us to re-run the game and get
    # a new magic number if we want to play again.
    engine_object.initialize_game()
    magic_number = engine_object.get_magic_number()

    print ("The magic number is: " + str(magic_number))

    play_yes = False                                # Player 1 sends a request.  If player 2 responds, set to True
    game_complete = False                           # Loop and receive messages until we get an ENDAPP message
    initial_send = False                            # Player 1 starts, but after that set to true and go through game loop.
    player_one_serial_saved = player_one_serial     # Make sure Player 1 starts...might be a better way to handle this.
    number_to_guess = 0                             # Store players 2 guess

    print ("player_one_serial is: " + player_one_serial)
    print ("player_two_serial is: " + player_two_serial)

    # subscribe to our queue if we have a robot object:
    if player_one_serial:
        conn.subscribe(destination='/queue/' + player_one_serial, id=1, ack='auto')

        print ("player_one_serial just subscribed to /queue/" + player_one_serial)

        conn.send(body='anyone' + ":" + player_one_serial + ':' + "play_request" + ":" +
                    "number_guesser", destination="/queue/" + "number_guesser")

        print (player_one_serial + " just send a message to: " + "anyone" +
                " with comand=play_request and payload=number_guesser to /queue/" + "number_guesser")

    if player_two_serial:
        conn.subscribe(destination='/queue/' + player_two_serial, id=2, ack='auto')
        conn.subscribe(destination='/queue/' + 'number_guesser', id=3, ack='auto')

        print ("player_two_serial: " + player_two_serial + " just subscribed to /queue/" + player_two_serial +
                " and " + "/queue/" + "number_guesser")

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
            print ("command: ***" + command + "***")
            print ("payload: ***" + payload + "***")
            #print ("number_to_guess: ***" + str(number_to_guess) + "***")
            print ("magic number is: " + str(magic_number))

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
                                "number_guesser", destination="/queue/" + from_robot)

                    print ("because we are player_two_serial, we just sent a message: " +
                            "from_robot: " + player_two_serial + " to: " + from_robot +
                            " with the command play_request with the payload number_guesser" +
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
                        conn.send(body=player_one_serial + ":" + player_two_serial + ":" + "say" + ":" +
                            "Guess a number between " + str(engine_object.get_current_min()) + " and " +
                            str(engine_object.get_current_max()), destination="/queue/" + player_one_serial)
                        initial_send = True
                    else:
                        initial_send = True

                    print ("initial_send is now: " + str(initial_send))

                if command == "say" and re.search('Guess a number', payload):
                    if robot1_model == "comzo":
                        robot1.drive_straight(distance_mm(100), speed_mmps(200)).wait_for_completed()
                        robot1.say_text(payload, duration_scalar=0.6).wait_for_completed()
                        robot1.drive_straight(distance_mm(-100), speed_mmps(200)).wait_for_completed()

                    elif robot1_model == "vector":
                        robot1.behavior.drive_straight(distance_mm(100), speed_mmps(200))
                        robot1.behavior.say_text(payload, duration_scalar=0.8)
                        robot1.behavior.drive_straight(distance_mm(-100), speed_mmps(200))

                    conn.send(body=player_two_serial + ":" + player_one_serial + ":" + "said" + ":"
                                + payload  + ":" + str(engine_object.get_current_min()) +
                                ":" + str(engine_object.get_current_max()), destination="/queue/" + player_two_serial)

                elif command == "said" and re.search('Guess a number', payload):
                    #print ("OK: WHAT IS engine_object.get_current_min(): " + str(engine_object.get_current_min()))
                    #print ("OK: WHAT IS engine_object.get_current_max(): " + str(engine_object.get_current_max()))
                    match_object = re.search('(.*?)(:)(.*?)(:)(.*)', payload)

                    if match_object:
                        cur_min_from_p1 = int(match_object.group(3))
                        cur_max_from_p1 = int(match_object.group(5))

                        engine_object.set_current_min(cur_min_from_p1)
                        engine_object.set_current_max(cur_max_from_p1)

                    number_to_guess = engine_object.guess_a_number(engine_object.get_current_min(), engine_object.get_current_max())

                    print ("player 2 is guesing: " + str(number_to_guess))

                    if robot2_model == "cozmo":
                        robot2.drive_straight(distance_mm(100), speed_mmps(200)).wait_for_completed()
                        robot2.say_text(str(number_to_guess), duration_scalar=0.6).wait_for_completed()
                        robot2.drive_straight(distance_mm(-100), speed_mmps(200)).wait_for_completed()

                    elif robot2_model == "vector":
                        robot2.behavior.drive_straight(distance_mm(100), speed_mmps(200))
                        robot2.behavior.say_text(str(number_to_guess), duration_scalar=0.8)
                        robot2.behavior.drive_straight(distance_mm(-100), speed_mmps(200))

                    conn.send(body=player_one_serial + ":" + player_two_serial + ":" + "said" + ":"
                                + "guess:" + str(number_to_guess), destination="/queue/" + player_one_serial)

                # This is where I'm current at
                elif command == "said" and re.search('(.*?)(:)(.*)', payload):
                    match_object = re.search('(.*?)(:)(.*)', payload)
                    if match_object:
                        number_guessed = int(match_object.group(3))

                    if number_guessed < engine_object.get_current_min() or number_guessed > engine_object.get_current_max():
                        text_to_say = "Number out of range!"

                    elif number_guessed < magic_number:
                        text_to_say = "Number too low!"
                        engine_object.set_current_min(number_guessed)
                        engine_object.increase_user_guess_count(1)

                    elif number_guessed > magic_number:
                        text_to_say = "Number too high!"
                        engine_object.set_current_max(number_guessed)
                        engine_object.increase_user_guess_count(1)

                    elif number_guessed == magic_number:
                        engine_object.increase_user_guess_count(1)

                        if engine_object.get_user_guess_count() == 1:
                            text_to_say = "You guessed it!  The magic number was " + str(magic_number) + " and it took you " + str(engine_object.get_user_guess_count()) + " guess!"
                        else:
                            text_to_say = "You guessed it!  The magic number was " + str(magic_number) + " and it took you " + str(engine_object.get_user_guess_count()) + " guesses!"

                    if robot1_model == "cozmo":
                        #robot1.drive_straight(distance_mm(100), speed_mmps(200)).wait_for_completed()
                        robot1.say_text(text_to_say, duration_scalar=0.6).wait_for_completed()
                        #robot1.drive_straight(distance_mm(-100), speed_mmps(200)).wait_for_completed()

                    elif robot1_model == "vector":
                        #robot1.behavior.drive_straight(distance_mm(100), speed_mmps(200))
                        robot1.behavior.say_text(text_to_say, duration_scalar=0.8)
                        #robot1.behavior.drive_straight(distance_mm(-100), speed_mmps(200))

                    if number_guessed == magic_number:
                        conn.send(body=player_one_serial + ":" + player_one_serial + ":" + "ENDAPP" + ":" + "NULL", destination="/queue/" + player_one_serial)
                        conn.send(body=player_two_serial + ":" + player_two_serial + ":" + "ENDAPP" + ":" + "NULL", destination="/queue/" + player_two_serial)

                    else:
                        conn.send(body=player_one_serial + ":" + player_two_serial + ":" + "say" + ":" +
                            "Guess a number between " + str(engine_object.get_current_min()) + " and " +
                            str(engine_object.get_current_max()), destination="/queue/" + player_one_serial)

                elif command == "ENDAPP":
                    game_complete = True

                    if from_robot == player_two_serial and player_two_model == "cozmo":
                        robot2.play_anim(name="anim_speedtap_wingame_intensity02_01").wait_for_completed()

                    elif from_robot == player_two_serial and player_two_model == "vector":
                        robot2.anim.play_animation('anim_pounce_success_02')

                message_queue.remove(message)

        print ("Waiting for another player...")
        time.sleep(1)

# main code:
message_queue = []
cozmo_supported = False
vector_supported = False
final_path = ""
player_one_model_and_serial = ""
player_two_model_and_serial = ""
player_one_model = ""
player_two_model = ""
player_one_serial = ""
player_two_serial = ""

opts, args = getopt.getopt(sys.argv[1:], 'c:', ['p1=', 'p2='])

for opt, arg in opts:
    if opt == "--p1":
        player_one_model_and_serial = arg

    elif opt == "--p2":
        player_two_model_and_serial = arg

    elif opt == "-c":
        config_file = arg

try:
    config_file_object = open(config_file, "r")

except:
    print ("Couldn't open config file")
    exit(1)

# parse out model and serial number:
mo1 = re.search('(.*?)(:)(.*)', player_one_model_and_serial)
mo2 = re.search('(.*?)(:)(.*)', player_two_model_and_serial)

if mo1:
    player_one_model = mo1.group(1)
    player_one_serial = mo1.group(3)

if mo2:
    player_two_model = mo2.group(1)
    player_two_serial = mo2.group(3)

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
    from cozmo.util import degrees, distance_mm, speed_mmps
    cozmo_supported = True
    print ("cozmo sdk found")

    def cozmo_program(robot: cozmo.robot.Robot):
        print ("p1m: " + player_one_model)
        print ("p2m: " + player_two_model)
        print ("p1: " + player_one_serial)
        print ("p2: " + player_two_serial)

        # two cozmo's not yet supported...have to figure out what that looks like
        #if player_one_model == "vector" and player_two_model == "vector":
        #    the_application(robot1, player_one_model, robot2, player_two_model, player_one_serial, player_two_serial)

        if player_one_model == "cozmo" and player_two_model != "cozmo":
            the_application(robot, player_one_model, "", "", player_one_serial, player_two_serial)

        elif player_one_model != "cozmo" and player_two_model == "cozmo":
            the_application("", "", robot, player_two_model, player_one_serial, player_two_serial)

except ModuleNotFoundError:
    print ("cozmo sdk not found, cozmo robots are not supported on this computer.")

try:
    import anki_vector
    from anki_vector.util import degrees, distance_mm, speed_mmps
    vector_supported = True
    print ("vector sdk found")

except ModuleNotFoundError:
    print ("vector sdk not found, vector robots are not supported on this computer.")

if cozmo_supported:
    try:
        cozmo.run_program(cozmo_program)
    except Exception as e:
        print ("Trouble running cozmo code: ")
        print (traceback.format_exc())

if vector_supported:
    try:
        def vector_code():
            print ("p1m: " + player_one_model)
            print ("p2m: " + player_two_model)
            print ("p1: " + player_one_serial)
            print ("p2: " + player_two_serial)

            if player_one_model == "vector" and player_two_model == "vector":
                with anki_vector.Robot(player_one_serial) as robot1:
                    with anki_vector.Robot(player_two_serial) as robot2:
                        the_application(robot1, player_one_model, robot2, player_two_model, player_one_serial, player_two_serial)

            elif player_one_model == "vector" and player_two_model != "vector":
                with anki_vector.Robot(player_one_serial) as robot1:
                    the_application(robot1, player_one_model, "", "", player_one_serial, player_two_serial)

            elif player_one_model != "vector" and player_two_model == "vector":
                with anki_vector.Robot(player_two_serial) as robot2:
                    the_application("", "", robot2, player_two_model, player_one_serial, player_two_serial)

    except:
        print ("Trouble running vector code")
else:
    print ("No supported robots found!")

if __name__ == '__main__':
    if vector_supported:
        vector_code()
