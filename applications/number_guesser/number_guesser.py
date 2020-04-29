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
        global robot_message_queue
        global human_message_queue

        match_object = re.search('(.*?)(:)(.*?)(:)(.*?)(:)(.*)', message)

        if match_object:
            if match_object.group(1) == "human":
                human_message_queue.append(match_object)

            else:
                robot_message_queue.append(match_object)


# Handle ctrl-c, not currently working, will fix later.
def handler(signal_received, frame):
    print ('ctrl-c caught, cleaning up.')

    exit(0)

def gui_output(two_bots_same_computer, message, player_one_serial, player_two_serial):
    if two_bots_same_computer:
        stomp_conn.send(body=player_one_serial + ":" + player_one_serial + ":" + "output" + ":" +
            message, destination="/queue/" + 'ng_output_' + player_one_serial)

    else:
        if player_one_serial:
            stomp_conn.send(body=player_one_serial + ":" + player_one_serial + ":" + "output" + ":" +
                message, destination="/queue/" + 'ng_output_' + player_one_serial)

        if player_two_serial:
            stomp_conn.send(body=player_two_serial + ":" + player_two_serial + ":" + "output" + ":" +
                message, destination="/queue/" + 'ng_output_' + player_two_serial)

# This is the actual application code.  If we get to here, we have 1 or 2 robot objects defined.
# If you are interested in writing your own game with IBCP, and don't want to mess with the details
# of defining cozmo or vector, this is the function you would want to modify.  This is essentailly
# the last thing that is called in this overall script.

# robot1 and robot2 could be a Cozmo or Vector robot object.  the robotN_model parameters are
# either cozmo or vector, depending on what was passed in at the command line.  The serial numbers
# are well, the robots serial number.  Vector's is written on the bottom of the physical robot.
# Cozmo serial number can be found in the Cozmo app when connected to said robot.
def the_application(robot1, robot1_model, robot2, robot2_model, player_one_serial, player_two_serial, mq_server, mq_port, stomp_conn):
    # This is our number guesser engine object:
    engine_object = number_guesser_engine()

    play_yes = False                                # Player 1 sends a request.  If player 2 responds, set to True
    game_complete = False                           # Loop and receive messages until we get an ENDAPP message
    initial_send = False                            # Player 1 starts, but after that set to true and go through game loop.
    player_one_serial_saved = player_one_serial     # Make sure Player 1 starts...might be a better way to handle this.
    number_to_guess = 0                             # Store players 2 guess

    gui_output(two_bots_same_computer, "WELCOME TO NUMBER GUESSER USING IBCP VERSION 0.2!\n", player_one_serial, player_two_serial)

    gui_output(two_bots_same_computer, "Might be waking up robots, please wait...", player_one_serial, player_two_serial)

    gui_output(two_bots_same_computer, "player_one_serial is: " + player_one_serial, player_one_serial, player_two_serial)
    gui_output(two_bots_same_computer, "player_two_serial is: " + player_two_serial, player_one_serial, player_two_serial)

    print ("player_one_serial is: " + player_one_serial)
    print ("player_two_serial is: " + player_two_serial)

    # Call initialize_game() and get the magic number (if we are player1).  This code allows us to re-run the game and get
    # a new magic number if we want to play again (although play again not currently supported).
    engine_object.initialize_game()

    print ("WTF 0: what is robot1_model: " + robot1_model)

    if player_one_serial_saved == player_one_serial and robot1_model != 'human':
        magic_number = engine_object.get_magic_number()

        print ("The magic number is: " + str(magic_number))

    elif player_one_serial_saved == player_one_serial and robot1_model == 'human':
        # we need to get input first from human:
        dont_have_human_magic_number = True
        stomp_conn.subscribe(destination='/queue/' + 'human', id=7, ack='auto')
        stomp_conn.subscribe(destination='/queue/' + player_one_serial, id=9, ack='auto')


        gui_output(two_bots_same_computer, "player_one_serial just subscribed to /queue/" + player_one_serial, player_one_serial, player_two_serial)
        print ("player_one_serial just subscribed to /queue/" + player_one_serial)

        gui_output(two_bots_same_computer, "waiting for human to set a magic number...", player_one_serial, player_two_serial)

        while dont_have_human_magic_number:
            for message in human_message_queue:
                gui_output(two_bots_same_computer, "I have a message in human queue...", player_one_serial, player_two_serial)

                to_robot = message.group(1)
                from_robot = message.group(3)
                command = message.group(5)
                payload = message.group(7)

                if robot1_model == "human" and command == "set_magic_number":
                    magic_number = int(payload)
                    dont_have_human_magic_number = False

                    human_message_queue.remove(message)

            time.sleep(1)


    # subscribe to our queue if we have a robot object.
    # Each robot has theire own queue with a name like:  /queue/robot_serial_number
    # There is also a queue for game itself, think of it like a chat root.

    # Overall design:  Player 1 sends a "play_request" message to the /queue/number_guesser queue.
    # Player 1 waits until another robot repsonds and says "play_yes".  Then the game begins,
    # but each robot will be sending messages to each other's own queue, and not the number_guesser
    # queue.  The reason is that when both robots are subscribed to the same queue, they will both
    # try to take messages off of it.  So the number_guesser queue works so that any robot
    # can send a request and another can respond, but for talking back and forth we use their
    # individual queues so a robot only retrives messages intended for itself.

    if player_one_serial:
        if player_one_model != "human":
            stomp_conn.subscribe(destination='/queue/' + player_one_serial, id=1, ack='auto')

            gui_output(two_bots_same_computer, "player_one_serial just subscribed to /queue/" + player_one_serial, player_one_serial, player_two_serial)
            print ("player_one_serial just subscribed to /queue/" + player_one_serial)

        stomp_conn.send(body='anyone' + ":" + player_one_serial + ':' + "play_request" + ":" +
                    "number_guesser", destination="/queue/" + "number_guesser")

        gui_output(two_bots_same_computer, player_one_serial + " just send a message to: " + "anyone" +
                " with comand=play_request and payload=number_guesser to /queue/" + "number_guesser",
                player_one_serial, player_two_serial)

        print (player_one_serial + " just send a message to: " + "anyone" +
                " with comand=play_request and payload=number_guesser to /queue/" + "number_guesser")

    if player_two_serial:
        stomp_conn.subscribe(destination='/queue/' + player_two_serial, id=2, ack='auto')
        stomp_conn.subscribe(destination='/queue/' + 'number_guesser', id=3, ack='auto')

        gui_output(two_bots_same_computer, "player_two_serial: " + player_two_serial + " just subscribed to /queue/" + player_two_serial +
                " and " + "/queue/" + "number_guesser",
                player_one_serial, player_two_serial)

        print ("player_two_serial: " + player_two_serial + " just subscribed to /queue/" + player_two_serial +
                " and " + "/queue/" + "number_guesser")

    while not game_complete:
        # Now we enter the main game loop.  We don't exit here until the game is over.

        print ("game loop begin: ")
        print ("game_complete: " + str(game_complete))
        print ("what is player_one_serial: " + player_one_serial)
        print ("what is player_two_serial: " + player_two_serial)
        print ("what is play_yes: " + str(play_yes))
        print ("Now looking at our robot_message_queue: ")
        print ("\n")

        # This is where we look at the messages that came on to our queue.
        # What actually happened is that the Stomp callback routine on_message()
        # already happened.  We don't have access to a robot object in on_message(),
        # so we add the contents of the message on to the python list message_queue[]
        # and then process them here, where do have a robot object.
        for message in robot_message_queue:
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

            # First we need to send a message to /queue/number_guesser and wait for another robot
            # to respond.  We won't go into the actual game until then, so play_yes will be False
            # until robot2 responds.
            if not play_yes:
                print ("We are in if not play_yes code")
                print ("player_one_serial: " + player_one_serial)
                print ("player_two_serial: " + player_two_serial)
                print ("Now we test if command == play_request: ")

                if two_bots_same_computer:
                    play_yes = True
                    gui_output(two_bots_same_computer, "player 1 agrees to play", player_one_serial, player_two_serial)
                    gui_output(two_bots_same_computer, "player 2 agrees to play", player_one_serial, player_two_serial)

                    stomp_conn.send(body=player_two_serial + ":" + from_robot + ':' + "play_request" + ":" +
                                "number_guesser", destination="/queue/" + from_robot)

                    print ("because we are player_two_serial, we just sent a message: " +
                            "from_robot: " + player_two_serial + " to: " + from_robot +
                            " with the command play_request with the payload number_guesser" +
                            " to the destination /queue/" + from_robot)

                else:
                    if command == "play_request" and player_one_serial:
                        play_yes = True

                        gui_output(two_bots_same_computer, "player 1 agrees to play", player_one_serial, player_two_serial)

                        print ("command does = play_request and player_one_serial has something.")

                    elif command == "play_request" and player_two_serial:
                        play_yes = True

                        gui_output(two_bots_same_computer, "player 2 agrees to play", player_one_serial, player_two_serial)

                        print ("command does = play_request and player_two_serial has something.")

                        conn.send(body=player_two_serial + ":" + from_robot + ':' + "play_request" + ":" +
                                    "number_guesser", destination="/queue/" + from_robot)

                        print ("because we are player_two_serial, we just sent a message: " +
                                "from_robot: " + player_two_serial + " to: " + from_robot +
                                " with the command play_request with the payload number_guesser" +
                                " to the destination /queue/" + from_robot)

                # This handles the situation if player1 and player2 are being ran from 2 different computers.
                # If we run this script on the same computer with both player1 and player2, we know their
                # serial numbers already.  However if we ran this from 2 different instances, we don't
                # know what the other players serial number is.  So if it's null, get the unknown
                # serial number from the MQ message.
                if not player_one_serial:
                    player_one_serial = from_robot

                if not player_two_serial:
                    player_two_serial = to_robot

                print ("What is modified player_one_serial: " + player_one_serial)
                print ("What is modified player_two_serial: " + player_two_serial)

            elif play_yes:
                # If we got here, now we play the actual game.  Perhaps I over complicated this
                # inital part, but I use a boolean to kick off the inital send to get things going.

                if not initial_send:
                    print ("player_one_serial_saved: " + player_one_serial_saved)
                    print ("player_one_serial: " + player_one_serial)

                    # We only want player one to get things started:
                    if player_one_serial_saved == player_one_serial:
                        # Send a MQ message to the player1 robot to "say" "Guess a number..."
                        stomp_conn.send(body=player_one_serial + ":" + player_two_serial + ":" + "say" + ":" +
                            "Guess a number between " + str(engine_object.get_current_min()) + " and " +
                            str(engine_object.get_current_max()), destination="/queue/" + player_one_serial)

                        gui_output(two_bots_same_computer, "<Player 1> Guess a number between " + str(engine_object.get_current_min()) + " and " +
                            str(engine_object.get_current_max()), player_one_serial, player_two_serial)

                        initial_send = True
                    else:
                        initial_send = True

                    print ("initial_send is now: " + str(initial_send))

                # Now we start looking at the contents of each MQ message.
                # Each if/elif block represents a possible MQ message.

                # This block handles the first inital message from player 1 to get things going:
                if command == "say" and re.search('Guess a number', payload):
                    if robot1_model == "comzo":
                        robot1.drive_straight(distance_mm(20), speed_mmps(200)).wait_for_completed()
                        robot1.say_text(payload, duration_scalar=0.6).wait_for_completed()
                        robot1.drive_straight(distance_mm(-20), speed_mmps(200)).wait_for_completed()

                    elif robot1_model == "vector":
                        robot1.behavior.drive_straight(distance_mm(20), speed_mmps(200))
                        robot1.behavior.say_text(payload, duration_scalar=0.8)
                        robot1.behavior.drive_straight(distance_mm(-20), speed_mmps(200))

                    elif robot1_model == "human" and robot2_model == "cozmo":
                        robot2.say_text(player_one_serial + " says " + payload, duration_scalar=0.6).wait_for_completed()

                    elif robot1_model == "human" and robot2_model == "vector":
                        robot2.behavior.say_text(player_one_serial + " says " + payload, duration_scalar=0.8)

                    # don't think human needs to do anything here

                    stomp_conn.send(body=player_two_serial + ":" + player_one_serial + ":" + "said" + ":"
                                + payload  + ":" + str(engine_object.get_current_min()) +
                                ":" + str(engine_object.get_current_max()), destination="/queue/" + player_two_serial)

                # This block handles player2 receiving the message to guess a number.
                elif command == "said" and re.search('Guess a number', payload):
                    gui_output(two_bots_same_computer, "[D0]: P2 begin with message said-guess a number", player_one_serial, player_two_serial)

                    number_to_guess = 0

                    print ("Did we get here and what is player_two_model: " + player_two_model)

                    if player_two_model == "human":
                        gui_output(two_bots_same_computer, "[D1]: P2 said-guess a number P2 is human", player_one_serial, player_two_serial)

                        stomp_conn.subscribe(destination='/queue/' + 'human', id=11, ack='auto')
                        dont_have_human_guess = True

                        # if player2 is a human, we need to scan the human queue for messages,
                        # which will put in an indefinte delay here.
                        # Well, indefinte until the human responds.
                        while dont_have_human_guess:
                            for human_message in human_message_queue:
                                gui_output(two_bots_same_computer, "I have a message in human queue...", player_one_serial, player_two_serial)

                                to_robot = human_message.group(1)
                                from_robot = human_message.group(3)
                                command = human_message.group(5)
                                payload = human_message.group(7)

                                if robot2_model == "human" and command == "human_guess":
                                    number_to_guess = payload
                                    dont_have_human_guess = False

                                    human_message_queue.remove(human_message)

                            time.sleep(1)

                    # This is the non-human message from robot player 1.
                    # It contains the cur min and cur max, so we need this
                    # info regardless if player2 is a robot or human.
                    match_object = re.search('(.*?)(:)(.*?)(:)(.*)', payload)

                    if match_object:
                        gui_output(two_bots_same_computer, "[D2]: P2 said-guess a number we matched object", player_one_serial, player_two_serial)
                        # If this script is ran on two different computers, player2 wouldn't know the
                        # current min and current max possibilities.  player1 sends
                        # this in the message, and then player2 sets it's so we are consistent among both player.
                        # If if it's ran on the same computer, I think we are just issuing a redundant set_current_min and _max() call.
                        # but that's ok.
                        cur_min_from_p1 = int(match_object.group(3))
                        cur_max_from_p1 = int(match_object.group(5))

                        engine_object.set_current_min(cur_min_from_p1)
                        engine_object.set_current_max(cur_max_from_p1)

                    else:
                        gui_output(two_bots_same_computer, "[D2a]: P2 said-guess a number we did not match object", player_one_serial, player_two_serial)

                    # BREAKPOINT Here...

                    # Call the algorithm to guess a number:

                    # If we are a human, the guess already came in from the human queue
                    if robot2_model != "human":
                        number_to_guess = engine_object.guess_a_number(engine_object.get_current_min(), engine_object.get_current_max())

                        gui_output(two_bots_same_computer, "[D3]: P2 said-guess a number and we are not human and number_to_guess is: " + str(number_to_guess), player_one_serial, player_two_serial)

                    else:
                        gui_output(two_bots_same_computer, "[D3a]: P2 said-guess a number and we are human", player_one_serial, player_two_serial)

                    gui_output(two_bots_same_computer, "<Player 2> I guess: " + str(number_to_guess), player_one_serial, player_two_serial)
                    print ("player 2 is guesing: " + str(number_to_guess))

                    print ("DEBUG D10: What is robot2_model: " + robot2_model)

                    if robot2_model == "cozmo":
                        robot2.drive_straight(distance_mm(20), speed_mmps(200)).wait_for_completed()
                        robot2.say_text("I guess " + str(number_to_guess), duration_scalar=0.6).wait_for_completed()
                        robot2.drive_straight(distance_mm(-20), speed_mmps(200)).wait_for_completed()

                    elif robot2_model == "vector":
                        gui_output(two_bots_same_computer, "[D4]: P2 said-guess a number and robot2 model is Vector", player_one_serial, player_two_serial)
                        robot2.behavior.drive_straight(distance_mm(20), speed_mmps(200))
                        robot2.behavior.say_text("I guess " + str(number_to_guess), duration_scalar=0.8)
                        robot2.behavior.drive_straight(distance_mm(-20), speed_mmps(200))

                    elif robot2_model == "human":
                        if robot1_model == "cozmo":
                            robot1.say_text(player_two_serial + " guessed " + str(number_to_guess), duration_scalar=0.6).wait_for_completed()

                        elif robot1_model == "vector":
                            robot1.behavior.say_text(player_two_serial + " guessed " + str(number_to_guess), duration_scalar=0.8)

                    # Send a message to player1 with player2's guess.
                    stomp_conn.send(body=player_one_serial + ":" + player_two_serial + ":" + "said" + ":"
                                + "guess:" + str(number_to_guess), destination="/queue/" + player_one_serial)

                # player1 compares the guess to see if was out of range, too low, too high, or just right
                elif command == "said" and re.search('(.*?)(:)(.*)', payload):
                    gui_output(two_bots_same_computer, "[E0]: P1 said-guess a number begin", player_one_serial, player_two_serial)

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
                        gui_output(two_bots_same_computer, "<Player 1> " + text_to_say, player_one_serial, player_two_serial)
                        robot1.say_text(text_to_say, duration_scalar=0.6).wait_for_completed()

                    elif robot1_model == "vector":
                        gui_output(two_bots_same_computer, "<Player 1> " + text_to_say, player_one_serial, player_two_serial)
                        robot1.behavior.say_text(text_to_say, duration_scalar=0.8)

                    elif robot1_model == "human" and robot2_model == "cozmo":
                        gui_output(two_bots_same_computer, "<Player 1> " + text_to_say, player_one_serial, player_two_serial)
                        robot2.say_text(player_one_serial + " says " + text_to_say, duration_scalar=0.6).wait_for_completed()

                    elif robot1_model == "human" and robot2_model == "vector":
                        gui_output(two_bots_same_computer, "<Player 1> " + text_to_say, player_one_serial, player_two_serial)
                        robot2.behavior.say_text(player_one_serial + " says " + text_to_say, duration_scalar=0.8)

                    # Since the number was guessed, we send a ENDAPP IBCP command to say we are done and exit the program.
                    if number_guessed == magic_number:
                        stomp_conn.send(body=player_one_serial + ":" + player_one_serial + ":" + "ENDAPP" + ":" + "NULL", destination="/queue/" + player_one_serial)
                        stomp_conn.send(body=player_two_serial + ":" + player_two_serial + ":" + "ENDAPP" + ":" + "NULL", destination="/queue/" + player_two_serial)

                        gui_output(two_bots_same_computer, "ENDAPP received, game is done.", player_one_serial, player_two_serial)

                    # Guess again!  Also passing in the current_min and current_max values for player 2 to process
                    else:
                        gui_output(two_bots_same_computer, "[E1]: P1 said-guess a number send message to P2", player_one_serial, player_two_serial)

                        gui_output(two_bots_same_computer,
                            player_two_serial + ":" + player_one_serial + ":" + "say" + ":" +
                                "Guess a number between " + str(engine_object.get_current_min()) + " and " +
                                str(engine_object.get_current_max()),

                            player_one_serial, player_two_serial
                        )

                        stomp_conn.send(body=player_two_serial + ":" + player_one_serial + ":" + "say" + ":" +
                            "Guess a number between " + str(engine_object.get_current_min()) + " and " +
                            str(engine_object.get_current_max()), destination="/queue/" + player_two_serial)

                        gui_output(two_bots_same_computer, "<Player 1> " + "Guess a number between " + str(engine_object.get_current_min()) + " and " +
                            str(engine_object.get_current_max()),
                            player_one_serial, player_two_serial)

                # If we get an ENDAPP message, set our boolean to true to our game loop exits
                elif command == "ENDAPP":
                    game_complete = True

                    # This is probably bad and vector isn't really doing the animation, but cozmo does.
                    # This probably needs some re-thinking.
                    if from_robot == player_two_serial and player_two_model == "cozmo":
                        robot2.play_anim(name="anim_speedtap_wingame_intensity02_01").wait_for_completed()

                    elif from_robot == player_two_serial and player_two_model == "vector":
                        robot2.anim.play_animation('anim_pounce_success_01')

                # Remove the MQ message from the message_queue[] list now that we have processed it.
                robot_message_queue.remove(message)

        # This message is wrong, rather only applicable when play_yes = False.  Will fix later maybe,
        # but probably not until the next application.
        # We also wait 1 second so we don't go in a repaid loop and spike the cpu.  Basically every 1 second, we
        # check for new MQ messages.
        print ("Waiting for another player...")
        time.sleep(1)

# This is the start of the actual main code.

# First a bunch of variables:
robot_message_queue = []
human_message_queue = []
cozmo_supported = False
vector_supported = False
final_path = ""
player_one_model_and_serial = ""
player_two_model_and_serial = ""
player_one_model = ""
player_two_model = ""
player_one_serial = ""
player_two_serial = ""
mq_server = ""
mq_port = ""
two_bots_same_computer = False

# This is for getting command line arguments.

# Note:  If you have ever used Anki's Vector SDK examples, you may be faimilar with
# needing to pass a -s serial.  To get around that I don't use Anki's
# parse_command_args().  If you use this function, it will only allow -s and not anything else.
# Instead I get the args I want, and then pass the serial number in question to anki_vector.Robot().

# The format here is that I need the absolute path to the ibcp.cfg file with the -c arg.
# -c /path/to/ibcp.cfg
# I need the absolute path at least for the time being.

# The player arguments have a very specific format:
# --p1 vector:NNNNNNNN
# --p2 cozmo:NNNNNNNN
#
# You MUST use a double dash for --p1 and --p2.  A single dash will not work.
# The argument to --p1 and --p2 must be in the format:  robot_model:serial_number
# I don't have a good way to tell if a robot is a cozmo or vector.  There might
# be ways but I ran into issues trying it programatically, so I have you tell
# me what he model is and everything works fine.

opts, args = getopt.getopt(sys.argv[1:], 's:p:', ['p1=', 'p2='])

for opt, arg in opts:
    if opt == "--p1":
        player_one_model_and_serial = arg

    elif opt == "--p2":
        player_two_model_and_serial = arg

    elif opt == "-s":
        mq_server = arg

    elif opt == "-p":
        mq_port = arg

if player_one_model_and_serial and player_two_model_and_serial:
    two_bots_same_computer = True

# parse out model and serial number:
# mo stands for 'model object'
mo1 = re.search('(.*?)(:)(.*)', player_one_model_and_serial)
mo2 = re.search('(.*?)(:)(.*)', player_two_model_and_serial)

if mo1:
    player_one_model = mo1.group(1)
    player_one_serial = mo1.group(3)

if mo2:
    player_two_model = mo2.group(1)
    player_two_serial = mo2.group(3)

# Create connection to MQ server.
try:
    # IP and port of MQ server.  Defined in ibcp.cfg.
    stomp_conn = stomp.Connection([(mq_server, mq_port)])
    stomp_conn.set_listener('', MyListener())

    # This is weird, when apps try to create their own username/password mechanims and it's just
    # like, what were they thinking?  I think I just created admin/admin in here and it works.
    # Really secure, but...at least it works.
    stomp_conn.connect('admin', 'admin', wait=True)

except Exception as e:
    print ("error: " + str(e))

#if player_one_serial:
#    stomp_conn.subscribe(destination='/queue/' + 'ng_output_' + player_one_serial, id=5, ack='auto')

#if player_two_serial:
#    stomp_conn.subscribe(destination='/queue/' + 'ng_output_' + player_two_serial, id=6, ack='auto')

# See if we are a human:
#if player_one_model == "human" and player_two_model == "human":
#    the_application("", player_one_model, "", player_two_model, player_one_serial, player_two_serial, mq_server, mq_port, stomp_conn)

#elif player_one_model == "human" and player_two_model != "human":
#    the_application("", player_one_model, "", "", player_one_serial, player_two_serial, mq_server, mq_port, stomp_conn)

#elif player_one_model != "human" and player_two_model == "human":
#    the_application("", "", "", player_two_model, player_one_serial, player_two_serial, mq_server, mq_port, stomp_conn)

# I THINK WE NEED TO HANDLE THE CASE OF 2 HUMANS HERE...


# Now we see if cozmo sdk is installed.  If so we define the function cozmo_program()
# which will actually call the application.
# Note that 2 player cozmo on the same computer is not supported.  2 player cozmo on differnt computers
# should be supported, but don't have the hardware to test that at the moment.
try:
    import cozmo
    from cozmo.util import degrees, distance_mm, speed_mmps
    cozmo_supported = True

    gui_output(two_bots_same_computer, "cozmo sdk found", player_one_serial, player_two_serial)

    print ("cozmo sdk found")

    def cozmo_program(robot: cozmo.robot.Robot):
        #print ("p1m: " + player_one_model)
        #print ("p2m: " + player_two_model)
        #print ("p1: " + player_one_serial)
        #print ("p2: " + player_two_serial)

        # two cozmo's not yet supported...have to figure out what that looks like
        #if player_one_model == "vector" and player_two_model == "vector":
        #    the_application(robot1, player_one_model, robot2, player_two_model, player_one_serial, player_two_serial)

        if player_one_model == "cozmo" and player_two_model != "cozmo":
            the_application(robot, player_one_model, "", "", player_one_serial, player_two_serial, mq_server, mq_port, stomp_conn)

        elif player_one_model != "cozmo" and player_two_model == "cozmo":
            the_application("", "", robot, player_two_model, player_one_serial, player_two_serial, mq_server, mq_port, stomp_conn)

except ModuleNotFoundError:
    gui_output(two_bots_same_computer, "cozmo sdk not found, cozmo robots are not supported on this computer.", player_one_serial, player_two_serial)

    print ("cozmo sdk not found, cozmo robots are not supported on this computer.")

# Now we see if Vector is supported.
try:
    import anki_vector
    from anki_vector.util import degrees, distance_mm, speed_mmps
    vector_supported = True

    gui_output(two_bots_same_computer, "vector sdk found", player_one_serial, player_two_serial)

    print ("vector sdk found")

except ModuleNotFoundError:
    gui_output(two_bots_same_computer, "vector sdk not found, vector robots are not supported on this computer.", player_one_serial, player_two_serial)

    print ("vector sdk not found, vector robots are not supported on this computer.")

# Call Cozmo program if one of robots is Cozmo.  Otherwise don't call it.
if cozmo_supported and (player_one_model == "cozmo" or player_two_model == "cozmo"):
    try:
        cozmo.run_program(cozmo_program)
    except Exception as e:
        gui_output(two_bots_same_computer, "Trouble running cozmo code:\n" + traceback.format_exc(), player_one_serial, player_two_serial)

        print ("Trouble running cozmo code: ")
        print (traceback.format_exc())

# If Vector is supported define our function to call the_application().  Since vector SDK works in serial numbers,
# any combination of vectors are supported.
if vector_supported:
    try:
        def vector_code():
            #print ("p1m: " + player_one_model)
            #print ("p2m: " + player_two_model)
            #print ("p1: " + player_one_serial)
            #print ("p2: " + player_two_serial)

            if player_one_model == "vector" and player_two_model == "vector":
                with anki_vector.Robot(player_one_serial) as robot1:
                    with anki_vector.Robot(player_two_serial) as robot2:
                        the_application(robot1, player_one_model, robot2, player_two_model, player_one_serial, player_two_serial, mq_server, mq_port, stomp_conn)

            elif player_one_model == "vector" and player_two_model != "vector":
                with anki_vector.Robot(player_one_serial) as robot1:
                    the_application(robot1, player_one_model, "", player_two_model, player_one_serial, player_two_serial, mq_server, mq_port, stomp_conn)

            elif player_one_model != "vector" and player_two_model == "vector":
                with anki_vector.Robot(player_two_serial) as robot2:
                    the_application("", player_one_model, robot2, player_two_model, player_one_serial, player_two_serial, mq_server, mq_port, stomp_conn)

    except:
        gui_output(two_bots_same_computer, "Trouble running vector code", player_one_serial, player_two_serial)
        print ("Trouble running vector code")
else:
    gui_output(two_bots_same_computer, "No supported robots found!", player_one_serial, player_two_serial)
    print ("No supported robots found!")

if __name__ == '__main__':
    if vector_supported:
        vector_code()
