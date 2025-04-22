import json
import time
import requests
#from rfid_reader import read_rfid
from sdl_helper import init_sdl, draw_screen, quit_sdl

'''
with open("config.json") as f:
    config = json.load(f)

port = config['serial_port']
api_url = config['api_url']
api_key = config['api_key']
'''

window, renderer = init_sdl()
draw_screen(renderer)

print("📲 Ready for touch + RFID...")

try:
    while True:
         print(".")
         time.sleep(10)
except KeyboardInterrupt:
    print("👋 Exit by user")
finally:
    quit_sdl()
