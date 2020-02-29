import threading
import socket
import paho.mqtt.client as mqtt

class SchleuseUdpReceiver(threading.Thread):
    UDP_IP = "0.0.0.0"
    UDP_PORT = 2080

    def __init__(self, consumers):
        threading.Thread.__init__(self)
        self.consumers = consumers

    def run(self):
        sock = socket.socket(socket.AF_INET, # Internet
                socket.SOCK_DGRAM) # UDP
        sock.bind((self.UDP_IP, self.UDP_PORT))

        old_data = None
        while True:
            data, addr = sock.recvfrom(1024) # buffer size is 1024 bytes
            if data != old_data:    
                print("received changed message:", data)
            for consumer in self.consumers:
                try:
                    consumer.put((data, addr), False)
                except:
                    pass
            old_data = data



if __name__ == "__main__":
    print('connecting to mqtt server...')
    client = mqtt.Client(client_id='SchleuseUdpReceiver')
    client.connect('uberbus.club.muc.ccc.de')

    class MqttConsumer:
        global client
        def put(self, input, foo):
            print('new message', input)
            client.publish('club/status', input[0])


    # connect consumers with Schleuse UDP receiver
    # Attention: only one process can listen per UDP port per device
    print('starting UDP receiver...')
    SchleuseUdpReceiver([MqttConsumer]).start()

