import os
import sys
import serial
import time
import pygame
import numpy as np
from collections import deque

# EEG
sf = 512              # sampling frequency of EEG
buffer_sec = 4        # EEG buffer in seconds
eeg_buffer= deque(maxlen=sf*buffer_sec)

# pygame
size = (1920, 1080)     # pygame screen size
pygame.init()
screen = pygame.display.set_mode(size)
# pygame.mouse.set_visible(False)

# save file
path = 'data/'
if not os.path.exists(path):
    os.mkdir(path)   
file_name = 'test.txt'
file = open(path + file_name, 'w')
   
class thinkGear(object):
    def __init__(self, port, baudrate=57600):
        self.ser = serial.Serial(port, baudrate)  #initialize serial communication
        self.data = {}

    def fetch_data(self):
        self.data = {}   #reset values
        while True:
            self.ser.read_until(b'\xaa\xaa')        # wait for sync bytes
            payload = []
            checksum = 0
            packet_length = self.ser.read(1)
            payload_length = packet_length[0]
            for i in range(payload_length):
                packet_code = self.ser.read(1)
                tempPacket = packet_code[0]
                payload.append(packet_code)
                checksum += tempPacket                
            checksum = ~checksum & 0xff
            check = self.ser.read(1)
            if checksum == check[0]:
                break      
            else: 
                print('ERROR: Checksum mismatch!')                  
        i = 0
        while i < payload_length:
            packet = payload[i]
            if packet == b'\x80':     # raw EEG value
                i += 1
                i += 1
                val0 = payload[i]
                i += 1
                val1 = payload[i]
                raw_value = val0[0] * 256 + val1[0]	
                if raw_value > 32768: 	
                    raw_value -= 65536				               
                self.data['eeg_raw'] = raw_value   
            elif packet == b'\x02':    # signal quality
                i += 1
                self.data['quality'] = payload[i][0]
            elif packet == b'\x04':    # attention
                i += 1
                self.data['attention'] = payload[i][0]
            elif packet == b'\x05':    # meditation
                i += 1
                self.data['meditation'] = payload[i][0]
            elif packet == b'\x16':    # eye blink (send only when blink event occurs)
                i += 1
                self.data['blink'] = payload[i][0] 
            else:
                pass                   
            i += 1                        
            
    def close(self):
        self.ser.close()

def exit_all():
    eeg_device.close()
    pygame.quit()
    sys.exit()
    
# start
eeg_device = thinkGear('COM3')

start_time = time.time()
while time.time() - start_time < 120:
    try:
        # update EEG raw data
        data = {}
        current_time = time.time() 
        eeg_device.fetch_data()
        data = eeg_device.data
        # print(str(current_time - start_time), str(data))
        if 'eeg_raw' in data:
            eeg_buffer.append(data['eeg_raw'])
            file.write(','.join([str(current_time - start_time), 
                                 str(data['eeg_raw']), '\n']))            
            # print(str(current_time - start_time), str(data['eeg_raw'])) 
            
            # plot
            if len(eeg_buffer) >= buffer_sec*sf:
                y = size[1]/2 + size[1]*np.array(list(eeg_buffer))/2000
                x = range(len(y))
                points = list(zip(x, y))
                                        
                screen.fill((255,255,255))
                pygame.draw.lines(screen, (0,0,0), False, points)
                
                pygame.display.flip()
                
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                exit_all()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    exit_all()
            
    except KeyboardInterrupt:
        break
              
exit_all()               
