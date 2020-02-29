
import paho.mqtt.client as mqtt
import time
import sys


def write(x):
    sys.stdout.write(x)
    sys.stdout.flush()

class MqttConsumer:
    client = None
    connected = False

    def __init__(self, client_id='SchleuseMqttConsumer'):
        self.client = mqtt.Client(client_id)

        def on_connect(client, userdata, flags, rc):
            if rc == 0:
                print("Connected to broker")
                self.connected = True
            else:
                print("Connection failed")
        self.client.on_connect = on_connect

        def on_message(client, userdata, message):
            print("Message received: ", message.payload)
            print(message)
        self.client.on_message = on_message

        print('connecting to mqtt server...')
        #self.client.username_pw_set("user", "password") 
        self.client.subscribe('club/status')

        #Wait for connection
        while self.connected != True:
            write('.')
            time.sleep(0.5)

        self.client.subscribe('club/status')

    def start(self):
        self.client.loop_start()
        return self

    def stop(self):
        self.client.disconnect()
        self.client.loop_stop()




if __name__ == "__main__":
    c = None
    try:
        c = MqttConsumer()
        c.start()

    except KeyboardInterrupt:
        print('exiting')
        if c is not None:
            c.stop()