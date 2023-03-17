"""
Simulate multi-channel EEG streams, and send these signals through LSL.
"""

from pylsl import StreamInfo, StreamOutlet, local_clock
import random as rnd
import time

channel_names = ['AF3', 'F7', 'F3', 'FC5', 'T7','P7', 'O1', 
                 'O2', 'P8', 'T8', 'FC6', 'F4','F8', 'AF4']  

n_channel = len(channel_names)
sample_rate = 128

def main():
    
    # Simulation of emotiv streaming using 14 channels and 128 Hz as sample rate
    info = StreamInfo('emotiv', 'EEG', n_channel, sample_rate, 'float32', 'myuid34234')
    
    info.desc().append_child_value("manufacturer", "LSLTestAmp")
    eeg_channels = info.desc().append_child("channels")
    
    for c in channel_names:
        eeg_channels.append_child("channel") \
                    .append_child_value("label", c) \
                    .append_child_value("unit", "microvolts") \
                    .append_child_value("type", "EEG")
                
    outlet = StreamOutlet(info)

    input('Start recording via Lab Recorder and press enter...')
    print('Streaming EEG data...')

    while True:
        
        # Randomize some EEG sample
        eeg_sample = [rnd.random() for i in range(n_channel)]

        # Now send it and wait for a bit
        outlet.push_sample(eeg_sample, local_clock())
        time.sleep(1 / sample_rate)

if __name__ == '__main__':
    
    main()
