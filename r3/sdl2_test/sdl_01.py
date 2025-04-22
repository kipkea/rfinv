import ctypes
import time
from ctypes import c_int, c_char_p, c_void_p, byref

# โหลด SDL3 (หากติดตั้งไว้ใน /usr/local/lib)
sdl = ctypes.CDLL("libSDL3.so")

# กำหนด prototype เบื้องต้น
sdl.SDL_Init.argtypes = [c_int]
sdl.SDL_Init.restype = c_int

sdl.SDL_Quit.argtypes = []
sdl.SDL_Quit.restype = None

sdl.SDL_CreateWindow.restype = c_void_p
sdl.SDL_CreateWindow.argtypes = [c_char_p, c_int, c_int, c_int, c_int, c_int]

sdl.SDL_CreateRenderer.restype = c_void_p
sdl.SDL_CreateRenderer.argtypes = [c_void_p, c_void_p, c_int]

sdl.SDL_SetRenderDrawColor.argtypes = [c_void_p, c_int, c_int, c_int, c_int]
sdl.SDL_RenderClear.argtypes = [c_void_p]
sdl.SDL_RenderPresent.argtypes = [c_void_p]

sdl.SDL_Delay.argtypes = [c_int]

# Initialize SDL
SDL_INIT_VIDEO = 0x00000020
sdl.SDL_Init(SDL_INIT_VIDEO)

# สร้างหน้าต่างแบบเต็มจอ (800x480)
SDL_WINDOW_FULLSCREEN = 0x00000001
window = sdl.SDL_CreateWindow(b"Touch UI", 0, 0, 800, 480, SDL_WINDOW_FULLSCREEN)
renderer = sdl.SDL_CreateRenderer(window, None, 0)

# วาดพื้นหลัง
sdl.SDL_SetRenderDrawColor(renderer, 0, 0, 0, 255)
sdl.SDL_RenderClear(renderer)

# วาดปุ่มสีน้ำเงิน
sdl.SDL_SetRenderDrawColor(renderer, 50, 100, 255, 255)
sdl.SDL_RenderClear(renderer)

# แสดงหน้าจอ
sdl.SDL_RenderPresent(renderer)

# หน่วงเวลา 5 วินาที
time.sleep(5)

# จบโปรแกรม
sdl.SDL_Quit()
