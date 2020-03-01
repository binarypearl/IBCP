# IBCP
Inner Bot Communication Protocol (IBCP) - Communication protocol to allow Cozmo and Vector robots to play games and communicate with each other

I found a way for both Cozmo and Vector robots to communicate with each other.

This project is incomplete, but the core architecture is working.  This will be updated once I get a fully functional
game involving both Cozmo and Vector together.

In a nutshell:
We use Apache MQ 5 as a message broker for the robots.  If you aren't familiar with Apache MQ, MQ stand for Message Queue.
A message queue is like a printer queue, but it uses text messages instead of print jobs in a typical printer queue.

The problem I am solving here is:  The DDL/Anki robots more or less don't communicate with each other.  
There is a small amount of pre-programmed human interaction (examples:  Quick Tap with Cozmo and BlackJack with Vector).
I have seen Vector try to wake up Cozmo's.  Whether that was intentional foreshadowing from Anki, I don't know.

But what I do know, is that I can form a higher level protocol that both robots can understand.  Behind the scenes, Cozmo and Vector
are very different.  However both robots can 'say' words.  Both robots can 'move'.  Both robots can do 'animations.'

The higher level concepts of say, move, and animate are the same.  The implementation details are different.

The way it works is that each robot has a queue.  If the robot receives a message, it acts on that message appropriately.

For example, lets say robot1 sends a message "Hello robot2! to robot2.  robot1 will send a MQ message to robot2.  
Robot2 will see the message and respond "Hello robot1!".

The inner guts of the code has to determine if the robot to perform the action is Cozmo or Vector.
But basically:  if we are a cozmo robot, use appropriate code, else if we are vector use appropriate code.

The end result:  We have a method for:
Cozmo to Cozmo interaction   

Vector to Vector interaction  

and even more cool:  

Cozmo to Vector interaction  

and even more even more cool interaction:  

multiplayer action of both Cozmo and Vector over both LAN and WAN.

Soon over time I plan to introduce a NumberGuesser game where a robot picks a random number between 1 and 100,
and another robot tries to guess that number in as few guesses as possible.  Once this is working,
the possibilities are endless.

--binarypearl
