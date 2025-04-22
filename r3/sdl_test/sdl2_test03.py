import sys
import sdl2
import sdl2.ext

def run():
    sdl2.ext.init()

    window = sdl2.ext.Window("SDL2 Console Mode", size=(800, 480))
    window.show()

    renderer = sdl2.ext.Renderer(window)
    factory = sdl2.ext.SpriteFactory(sdl2.ext.TEXTURE, renderer=renderer)
    white = sdl2.ext.Color(255, 255, 255)
    black = sdl2.ext.Color(0, 0, 0)

    running = True
    while running:
        events = sdl2.ext.get_events()
        for event in events:
            if event.type == sdl2.SDL_QUIT:
                running = False

        renderer.clear(black)

        rect = sdl2.SDL_Rect(100, 100, 600, 280)
        sdl2.SDL_SetRenderDrawColor(renderer.sdlrenderer, 0, 255, 0, 255)
        sdl2.SDL_RenderFillRect(renderer.sdlrenderer, rect)

        renderer.present()
        sdl2.SDL_Delay(5000)
        
        running = False
    sdl2.ext.quit()
    return 0

if __name__ == "__main__":
    sys.exit(run())
