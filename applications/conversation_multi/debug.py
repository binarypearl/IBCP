#!/usr/bin/python3

import stomp

class MyListener(stomp.ConnectionListener):
    def on_error(self, headers, message):
        print('received an error "%s"' % message)

    def on_message(self, headers, message):
        print('received a message "%s"' % message)
        global message_queue
        global ack_info

        print ("DEBUG message-id: " + str(headers['message-id']))
        print ("DEBUG subscription: " + str(headers['subscription']))

try:
    conn = stomp.Connection([('192.168.1.153', 61613)])

    print ("What is conn: " + str(conn))

    conn.set_listener('', MyListener())
    conn.connect('admin', 'admin', wait=True)

    print ("We got connected to mq")

except Exception as e:
    print ("error: " + str(e))
