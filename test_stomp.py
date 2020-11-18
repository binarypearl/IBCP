#!/usr/bin/python3

import stomp

def connect_to_mq_server(conn):
    # Create connection to MQ server.
    try:

        stomp_conn.connect('admin', 'admin', wait=True)

    except Exception as e:

        print ("Will try connecting to mq server in 1 second...")
        time.sleep(1)

class MyListener(stomp.ConnectionListener):
    def on_error(self, headers, message):
        print('received an error "%s"' % message)

    def on_message(self, headers, message):
        pass

    def on_disconnected(self, headres, message):
        print ('disconnected from Apache MQ server')
        connect_to_mq_server(self.conn)

stomp_conn = stomp.Connection([("192.168.1.153", 61613)])
stomp_conn.set_listener('', MyListener())
connect_to_mq_server(stomp_conn)
