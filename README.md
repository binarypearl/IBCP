# IBCP
Inner Bot Communication Protocol (IBCP) - Give Cozmo and Vector robots the ability to play games and communicate with each other

We use Apache MQ 5 as a message broker for the robots.  If you aren't familiar with Apache MQ, MQ stand for Message Queue.
A message queue is like a printer queue, but it uses text messages instead of print jobs in a typical printer queue.

The problem I am solving here is:  The DDL/Anki robots more or less don't communicate with each other.  
There is a small amount of pre-programmed human interaction (examples:  Quick Tap with Cozmo and BlackJack with Vector).

Behind the scenes, Cozmo and Vector are very different.  However both robots can 'say' phrases.  Both robots can 'move'.  
Both robots can do 'animations.'.  But the implementation details are different for each robot.

The way it works is that each robot has a queue.  If the robot receives a message, it acts on that message appropriately.

General message format is:  
>  to_robot:from_robot:command:payload  

Example:  
"robot2:robot1:say:Hello robot 1!"  

In this case, robot1 will send a MQ message to robot2, and robot2 can respond with:  
"robot1:robot2:say:Hello robot 2!"  

The end result:  We have a way to have:  
Cozmo to Cozmo interaction   

Vector to Vector interaction  

Cozmo to Vector interaction

multiplayer action of both Cozmo and Vector over both LAN and WAN.

**Installation, Configuration and Usage:**  
At a high level 3 things are needed:

**Installation:**
1.  Apache MQ 5:  
    https://activemq.apache.org/components/classic/download/
    Make sure you DON'T get Apache MQ Artemis.  That doesn't work with IBCP.

2.  IBCP itself:  
    git clone https://github.com/binarypearl/IBCP.git

3.  Python 3 modules:  
    One module for sure that you need is stomp.py:  
    > pip3 install install stomp.py  

    Your pip3 command may be slightly different than the command above.  The package is actually called stomp.py (with the .py extension)
    I had another version of stomp I think from system repository that worked in Linux but didn't with Mac and Windows.  Get the version
    from pip3 instead.

    Other modules will be listed later, eventually with a pre-check script that will tell you what is missing.

**Configuration:**  
Apache MQ should just need to be started.  If in Linux, go to your Apache MQ downloaded directory and run:  
> ./bin/activemq start  

Windows is probably similar, but not sure off the top of my head.  All you need is 1 instance of Apache MQ running for your network.

Modify IBCP/ibcp.cfg:  
The only thing we need to change is the mq_server.  Change the IP address here to the the IP address of the computer running Active MQ.
Leave the port alone as 61613 unless you really know what you are doing and changed it for some reason in Apache MQ.  
Leave the paths to the install directory commented out, they are not needed at the moment.

**Usage:**  
The only fully functioning application is number_guesser.  The other application conversation and conversation_multi work to some
degree, but they were early prototypes.

number_guesser is a 2 player game.  Both robots can be connected to one computer, or the robots can be on separate computers.
Only 1 computer needs Apache MQ running.

If running both robots on the same computer:

> cd IBCP/applications/number_guesser  
> ./number_guesser.py -c /path/to/ibcp.cfg --p1 vector:NNNNNNNN --p2 cozmo:NNNNNNNN  

Notes:  The --p1 and --p2 flags MUST have the double dash.  A single dash will not work.
The format is robot_model:serial_number

robot_model is either 'cozmo' or 'vector'.  The ':' is the separator and the NNNNNNNN is the serial number of the robot in question.

If running on different computers:
> On Computer 1:  
> cd IBCP/applications/number_guesser  
> ./number_guesser -c /path/to/ibcp.cfg --p1 vector:NNNNNNNN  

> On Computer 2:  
> cd IBCP/applications/number_guesser  
> ./number_guesser -c /path/to/ibcp.cfg --p2 cozmo:NNNNNNNN  

They can be started in any order.  

The only currently unsupported configuration is two Cozmo's on the same computer.  But have 2 Cozmo's play the game on different
computers should be supported.

--binarypearl
