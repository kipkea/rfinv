import ctypes

sdl = ctypes.CDLL("/usr/local/lib/libSDL3.so")

# ประกาศ constants และ types ที่จำเป็น
SDL_INIT_VIDEO = 0x00000020
SDL_WINDOW_FULLSCREEN = 0x00000001

def init_sdl():
    sdl.SDL_Init(SDL_INIT_VIDEO)
    window = sdl.SDL_CreateWindow(b"Touch RFID", 0, 0, 800, 480, SDL_WINDOW_FULLSCREEN)
    renderer = sdl.SDL_CreateRenderer(window, None, 0)
    return window, renderer

def draw_button(renderer, x, y, w, h, r, g, b):
    sdl.SDL_SetRenderDrawColor(renderer, r, g, b, 255)
    rect = ctypes.c_int * 4
    sdl.SDL_RenderFillRect(renderer, ctypes.byref(rect(x, y, w, h)))

def draw_screen(renderer):
    sdl.SDL_SetRenderDrawColor(renderer, 0, 0, 0, 255)
    sdl.SDL_RenderClear(renderer)

    draw_button(renderer, 100, 100, 600, 80, 50, 150, 250)  # ปุ่ม "Check RFID"
    draw_button(renderer, 100, 200, 600, 80, 100, 100, 100)  # ปุ่ม "Settings"
    draw_button(renderer, 100, 300, 600, 80, 200, 0, 0)      # ปุ่ม "Exit"

    sdl.SDL_RenderPresent(renderer)

def quit_sdl():
    sdl.SDL_Quit()
