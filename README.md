# IBCP
Inner Bot Communication Protocol (IBCP) - Communication protocol to allow Cozmo and Vector robots to play games and communicate with each other

This project is incomplete, but the core architecture is working.  This will be updated once I get a fully functional
game involving both Cozmo and Vector together.

In a nutshell:
We use Apache MQ 5 as a message broker for the robots.  If you aren't familiar with Apache MQ, MQ stand for Message Queue.
A message queue is like a printer queue, but it uses text messages instead of print jobs in a typical printer queue.

The problem I am solving here is:  The DDL/Anki robots more or less don't communicate with each other.  
There is a small amount of pre-programmed human interaction (examples:  Quick Tap with Cozmo and BlackJack with Vector).

Behind the scenes, Cozmo and Vector are very different.  However both robots can 'say' words.  Both robots can 'move'.  
Both robots can do 'animations.'.  But the implementation details are different for each robot.

The way it works is that each robot has a queue.  If the robot receives a message, it acts on that message appropriately.

General message format is:  to_robot:from_robot:command:payload

Example:  
"robot2:robot1:say:Hello robot 1!"

In this case, robot1 will send a MQ message to robot2.  

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
