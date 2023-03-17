from muselsl import stream
from pylsl import StreamInlet, resolve_byprop
from scipy.signal import butter, sosfilt
import os
import sys
import time
import pygame
import numpy as np

# functions
def butter_bandpass(lowcut, highcut, fs, order=5):
    nyq = 0.5 * fs
    low = lowcut / nyq
    high = highcut / nyq
    sos = butter(order, [low, high], analog=False, btype='band', output='sos')
    return sos

def butter_bandpass_filter(data, lowcut, highcut, fs, order=5):
    sos = butter_bandpass(lowcut, highcut, fs, order=order)
    y = sosfilt(sos, data)
    return y

# save file
path = 'data/'
if not os.path.exists(path):
    os.mkdir(path)   
file_name = 'test.txt'
file = open(path + file_name, 'w')

# muse device
name = 'Muse-8B5C'
mac_address = '00:55:da:b7:8b:5c'

stream(mac_address) # start stream

# initial inlet to get EEG stream
print('Looking for an EEG stream...')
streams = resolve_byprop('type', 'EEG', timeout=2)
if len(streams) == 0:
    raise(RuntimeError('Can\'t find EEG stream.'))
print('Start acquiring data.')

inlet = StreamInlet(streams[0], max_chunklen=1)
info = inlet.info()
sfreq = int(info.nominal_srate())
n_chans = info.channel_count()

description = info.desc()
ch = description.child('channels').first_child()
ch_names = [ch.child_value('label')]
for i in range(n_chans-1):
    ch = ch.next_sibling()
    ch_names.append(ch.child_value('label'))
    
file.write(','.join(['time'] + \
                    [ch_name for ch_name in ch_names] + \
                    ['\n']))

# EEG stream params
buffer_sec = 4    # EEG buffer in seconds
eeg = np.zeros((sfreq*buffer_sec, n_chans))
eeg_filtered = np.zeros((sfreq*buffer_sec, n_chans))
eeg_scale = 5

# pygame
size = (1920, 1080)               # pygame screen size
background_color = (255,255,255)  # white
line_color = (0,0,0)              # black
text_color = (0,0,0)              # black
pygame.init()
screen = pygame.display.set_mode(size)
font = pygame.font.SysFont(None, 24)
# pygame.mouse.set_visible(False)

y_line = np.linspace(0,size[1],n_chans+4)

# start EEG stream
start_time = time.time()
while time.time() - start_time < 120:
    try:
        current_time = time.time() 
        samples, timestamp = inlet.pull_chunk(timeout=0)
        # print(str(current_time - start_time), str(samples))
        if timestamp:        
            samples = np.array(samples)
            for sample in samples:
                file.write(','.join([str(current_time - start_time)] + \
                                    [str(i) for i in sample] + \
                                    ['\n']))                   
                # print(','.join([str(current_time - start_time)] + \
                #                [str(i) for i in sample] + \
                #                ['\n']))
            
            eeg = np.vstack([eeg, samples])
            eeg = eeg[-sfreq*buffer_sec:,:]
            
            for i in range(n_chans):
                eeg_filtered[:,i] = butter_bandpass_filter(eeg[:,i], lowcut=0.5, highcut=30.0, fs = sfreq, order=3)
            
            # plot
            x = [size[0]/(sfreq*buffer_sec)*i for i in range(sfreq*buffer_sec)]
            y = []
            for i in range(n_chans):
                y.append(y_line[i+2]+ + np.array(list(eeg_filtered[:,i]))/eeg_scale)
                       
            points = []
            for i in range(n_chans):
                points.append(list(zip(x, y[i])))
                                            
            screen.fill(background_color)
            
            for i in range(n_chans):
                pygame.draw.lines(screen, line_color, False, points[i])
                
                text = font.render(ch_names[i], True, text_color)
                screen.blit(text, (350,y_line[i+2]))
            
            pygame.display.flip()
            
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
                    
    except KeyboardInterrupt:
        break

pygame.quit()
sys.exit()        
                