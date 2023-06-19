import sys
import serial
import struct
import threading
import time

#################### Serial Port ####################
serialPort = 'COM6'  # 'COM5', 'COM6'
baudRate = 115200

data_bytes = bytearray()
is_exit = False
stop_threads1 = False

class SerialPort():
    def __init__(self, port, buandrate):
        self.port = serial.Serial(port, buandrate)
        self.port.close()
        if not self.port.isOpen():
            self.port.open()

    def port_open(self):
        if not self.port.isOpen():
            self.port.open()

    def port_close(self):
        self.port.close()

    def send_data(self, data):
        self.port.write(data)

    def read_data(self):
        global is_exit
        global data_bytes
        global stop_threads1
        while not is_exit:
            count = self.port.inWaiting()
            if count > 0:
                rec_str = self.port.read(count)
                data_bytes = data_bytes + rec_str
                # print('Receive:', rec_str.decode())
            elif stop_threads1:
                # self.port.write(b'\x63\x6d\x64\x42\x00\x00\x00\x00\x00\x0d')
                # self.port.close()
                break

def exit_all():
    global stop_threads1
        
    stop_threads1 = True
    t1.join()
        
    sys.exit()
    
# open serial port
mSerial = SerialPort(serialPort, baudRate)

# start the data reading thread
t1 = threading.Thread(target=mSerial.read_data)
t1.setDaemon(True)
t1.start()

# 1. detect mac_address
mac_address = b''
mac_address_detected = False
while not mac_address_detected:
    # print('............................................')
    # print('data_bytes:', data_bytes)
    data_len = len(data_bytes)
    # print('data_len:', data_len)
    i = 0
    while i < data_len-1:
        if (data_bytes[i] == 0xA5) and (data_bytes[i+1] == 0xA5):
            # print('i:', i)           
            if len(data_bytes[i+2:i+4])==2 & len(data_bytes[i+4:i+6])==2:
                frame_len = struct.unpack('<H', data_bytes[i+2:i+4])[0]
                frame_type = struct.unpack('<H', data_bytes[i+4:i+6])[0]
                # print('frame_len:', frame_len)
                # print('frame_type:', frame_type)
                if frame_type == 0x11:
                    # mac_address = b'_\x18\xc1\xab>\xf9'
                    # mac_address = b'\x9f\xf7\xda|\xb8\xd9'
                    # mac_address = b'h\xa9F\xb6\x7f\xf4'
                    mac_address = data_bytes[i+6:i+12] 
                    if mac_address.endswith(b'\xf4'):  # b'\xf9', b'\xd9', b'\xf4'
                        mac_address_detected = True
                        print('Mac address：', mac_address)    
                        print('Mac address detected.')
                        
                        mSerial.send_data(b'\x63\x6d\x64\x41' + mac_address + b'\x0d')                   
                        mSerial.send_data(b'\x63\x6d\x64\x44\x01\x30\x30\x30\x30\x0d')
                        
                        print('Send data for connection')
                        break
                i = i + frame_len
        else:
            i += 1
    data_bytes[:i] = b''
    
# 2. set fast upload mode
fast_mode_setted = False
while not fast_mode_setted:
    # print('............................................')
    # print('data_bytes:', data_bytes)
    data_len = len(data_bytes)
    # print('data_len:', data_len)
    i = 0
    while i < data_len-1:
        if (data_bytes[i] == 0xA5) and (data_bytes[i+1] == 0xA5):
            # print('i:', i)           
            if len(data_bytes[i+2:i+4])==2 & len(data_bytes[i+4:i+6])==2:
                frame_len = struct.unpack('<H', data_bytes[i+2:i+4])[0]
                frame_type = struct.unpack('<H', data_bytes[i+4:i+6])[0]
                # print('frame_len:', frame_len)
                # print('frame_type:', frame_type)
                if frame_type == 0x17:
                    if len(data_bytes[i+20:i+22]) == 2:
                        con_inf = struct.unpack('<H', data_bytes[i+20:i+22])[0]
                        print('Connection information: ', con_inf, data_bytes[i+20:i+22])
                        if con_inf != 'f':                            
                            print('Connection success')
                            
                            mSerial.send_data(b'\x63\x6d\x64\x47' + mac_address + b'\x0d')
                            fast_mode_setted = True
                            print('Set fast upload mode')
                            
                            mSerial.send_data(b'\x63\x6d\x64\x4A' + mac_address + b'\x0d')     
                            print('Stop collecting signal')
                            
                            mSerial.send_data(b'\x63\x6d\x64\x49' + mac_address + b'\x0d')     
                            print('Start collecting signal')
                            break
              
                        else:
                            print('Connection fail')
                i = i + frame_len
        else:
            i += 1
    data_bytes[:i] = b''
    
# collect EEG data
total_length = 0
eeg_buffer = []
start_time = time.time()
while not is_exit:
    try:
        # print('............................................')
        # print('data_bytes:', data_bytes)
        data_len = len(data_bytes)
        # print('data_len:', data_len)
        i = 0
        while i < data_len-1:
            if (data_bytes[i] == 0xA5) and (data_bytes[i+1] == 0xA5):
                # print('i:', i)           
                if len(data_bytes[i+2:i+4])==2 & len(data_bytes[i+4:i+6])==2:
                    frame_len = struct.unpack('<H', data_bytes[i+2:i+4])[0]
                    frame_type = struct.unpack('<H', data_bytes[i+4:i+6])[0]
                    # print('frame_len:', frame_len)
                    # print('frame_type:', frame_type)
                    if frame_type == 0x22:                       
                        eeg_raw = data_bytes[i+20:i+70]
                        eeg_len = len(eeg_raw)
                        if eeg_len == 50:
                            print('............................................')
                            print('acquire EEG signals (80 bits)')
                            total_length += 25
                            print('time:', round(time.time()-start_time, 2), 'total length:', total_length)
                            for j in range(25):
                                eeg = (struct.unpack('<H', eeg_raw[2*j:2*j+2])[0] -32768)*0.4
                                eeg_buffer.append(round(eeg,2))
                                # print(round(time.time()-start_time, 2), eeg)
                            # print('eeg buffer:', eeg_buffer[-5:])
                        else:
                            # print('length:', eeg_len)
                            # print(data_bytes[i:])
                            break
                            
                    elif frame_type == 0x18:                        
                        eeg_raw = data_bytes[i+20:i+260]
                        eeg_len = len(eeg_raw)
                        if eeg_len == 240:
                            print('............................................')
                            print('acquire EEG signals (240 bits)')
                            total_length += 120
                            print('time:', round(time.time()-start_time, 2), 'total length:', total_length)
                            for j in range(120):
                                eeg = (struct.unpack('<H', eeg_raw[2*j:2*j+2])[0] -32768)*0.4
                                eeg_buffer.append(round(eeg,2))
                                # print(round(time.time()-start_time, 2), eeg)
                            # print('eeg buffer:', eeg_buffer[-5:])
                        else:
                            # print('length:', eeg_len)
                            # print(data_bytes[i:])
                            break
                            
                                
                    i = i + frame_len
            else:
                i += 1
                
        data_bytes[:i] = b''    
        
    except KeyboardInterrupt:
        exit_all()
        