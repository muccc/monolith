import requests

class MilightHandler:
    MILIGHT_GATEWAY = "10.83.11.29"
    COLORS = {
        'down':   12,  # red
        'closed': 50,  # orange
        'member': 112, # green
        'public': 281, # violet
    }

    def __init__(self, message_queue):
        threading.Thread.__init__(self)
        self.message_queue = message_queue

    def set_color(self, hue):
        r = requests.put('http://' + self.MILIGHT_GATEWAY + '/gateways/13166/rgbw/3', json={"status":"on","hue":hue,"level":50}) 
        print(r.status_code)

    def run(self):
        old_status = None
        i = 0
        while True:
            # wait until a new message is in queue
            status, addr = self.message_queue.get()
            status = status.strip()
            
            if status != old_status or i > 100:
                if status in self.COLORS:
                    print('Milight: set color for ' + status)
                    self.set_color(self.COLORS[status])
                i = 0

            i += 1
            old_status = status
