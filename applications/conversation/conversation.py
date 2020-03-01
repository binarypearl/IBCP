#!/usr/bin/python3

from subprocess import Popen, PIPE, STDOUT
from signal import signal, SIGINT

def handler(signal_received, frame):
    print ('ctrl-c caught, cleaning up.')

    conn.disconnect()
    exit(0)

if __name__ == '__main__':
    signal(SIGINT, handler)

first_robot = "0060100c"
#second_robot = "0060689b"
second_robot = "45a28d52"

list_of_child_pids = []
list_of_active_robots = []

list_of_active_robots.append(first_robot)
list_of_active_robots.append(second_robot)

# Start a conversion_receive.py for each robot:
for active_robot in list_of_active_robots:
     process_robot = Popen(['/mnt/backups/anki/ibcp/applications/conversation/conversation_receive.py', '-s', active_robot])
     #stdout,stderr = process_robot.communicate()

     print ("If this worked, we just started conversion_receive for robot: " + active_robot)
     #print ("pid is: " + str(process_robot.pid))

     # Add each pid to a list.  upon ctrl-c or any other exit, kill -9 these pid's.
     list_of_child_pids.append(process_robot.pid)

# Lets just call conversation_send.py with no parameters for now.
process = Popen(['/mnt/backups/anki/ibcp/applications/conversation/conversation_send.py'], stdout=PIPE, stderr=PIPE)
stdout, stderr = process.communicate()

print ("stdout is: " + stdout.decode('utf-8'))


# first_robot send ACK to second_robot:
# use subprocess to send relavant information to conversion_send.py.

# Message to send would be like:
# to_robot:from_robot:command:payload
# first_robot:second_robot:say:ACK

#for pid in list_of_child_pids:
#    process_kill = Popen(['kill', '-9', str(pid)], stdout=PIPE, stderr=PIPE)
#    stdout, stderr = process_kill.communicate()

#    print ("I should have killed pid: " + str(pid))
#    print ("stdout of kill -9 should be empty: " + stdout.decode('utf-8'))
