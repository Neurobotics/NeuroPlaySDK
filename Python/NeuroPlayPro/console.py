from model.neuroplay import NeuroPlay
import time
import requests

np = NeuroPlay()

time_limit = 0.5 # Every half second
start_time = time.time() 

while True:
    current_time = time.time()
    elapsed_time = current_time - start_time 

    if elapsed_time >= time_limit:
        try:
            response = np.get('rhythms')
            if 'rhythms' in response:
                rhythms = response['rhythms']
                print(rhythms)
            else:
                print('No connection')
        except requests.exceptions.RequestException as e:
            print('Connection error')
        start_time = current_time
        

