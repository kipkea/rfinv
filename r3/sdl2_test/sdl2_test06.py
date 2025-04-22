import sys
import sdl2
import sdl2.ext
import sdl2.sdlttf
import sdl2.sdlimage

def point_in_rect(x, y, rect):
    return rect.x <= x <= rect.x + rect.w and rect.y <= y <= rect.y + rect.h

def render_button(renderer, rect, text, font, text_color, bg_color):
    sdl2.SDL_SetRenderDrawColor(renderer.sdlrenderer, *bg_color, 255)
    sdl2.SDL_RenderFillRect(renderer.sdlrenderer, rect)
    surface = sdl2.sdlttf.TTF_RenderUTF8_Solid(font, text.encode(), sdl2.SDL_Color(*text_color))
    texture = sdl2.SDL_CreateTextureFromSurface(renderer.sdlrenderer, surface.contents)
    text_rect = sdl2.SDL_Rect(rect.x + (rect.w - surface.contents.w)//2,
                              rect.y + (rect.h - surface.contents.h)//2,
                              surface.contents.w, surface.contents.h)
    sdl2.SDL_RenderCopy(renderer.sdlrenderer, texture, None, text_rect)
    sdl2.SDL_FreeSurface(surface)
    sdl2.SDL_DestroyTexture(texture)

def render_slider(renderer, slider_rect, value):
    # พื้น slider
    sdl2.SDL_SetRenderDrawColor(renderer.sdlrenderer, 180, 180, 180, 255)
    sdl2.SDL_RenderFillRect(renderer.sdlrenderer, slider_rect)

    # ตัวเลื่อน slider
    knob_x = slider_rect.x + int(value * slider_rect.w) - 10
    knob = sdl2.SDL_Rect(knob_x, slider_rect.y-5, 20, slider_rect.h+10)
    sdl2.SDL_SetRenderDrawColor(renderer.sdlrenderer, 0, 150, 255, 255)
    sdl2.SDL_RenderFillRect(renderer.sdlrenderer, knob)

def render_combobox(renderer, rect, options, selected, font):
    sdl2.SDL_SetRenderDrawColor(renderer.sdlrenderer, 50, 50, 50, 255)
    sdl2.SDL_RenderFillRect(renderer.sdlrenderer, rect)
    text = options[selected]
    surface = sdl2.sdlttf.TTF_RenderUTF8_Solid(font, text.encode(), sdl2.SDL_Color(255, 255, 255))
    texture = sdl2.SDL_CreateTextureFromSurface(renderer.sdlrenderer, surface.contents)
    text_rect = sdl2.SDL_Rect(rect.x+10, rect.y + (rect.h - surface.contents.h)//2,
                              surface.contents.w, surface.contents.h)
    sdl2.SDL_RenderCopy(renderer.sdlrenderer, texture, None, text_rect)
    sdl2.SDL_FreeSurface(surface)
    sdl2.SDL_DestroyTexture(texture)

def main():
    sdl2.ext.init()
    sdl2.sdlttf.TTF_Init()
    sdl2.sdlimage.IMG_Init(sdl2.sdlimage.IMG_INIT_JPG | sdl2.sdlimage.IMG_INIT_PNG)

    window = sdl2.ext.Window("Touch Screen UI", size=(800, 480))
    window.show()
    renderer = sdl2.ext.Renderer(window)

    font = sdl2.sdlttf.TTF_OpenFont(b"assets/THSarabun.ttf", 32)

    # โหลดรูปภาพ
    img_surface = sdl2.sdlimage.IMG_Load(b"assets/sample.jpg")
    img_texture = sdl2.SDL_CreateTextureFromSurface(renderer.sdlrenderer, img_surface)
    img_rect = sdl2.SDL_Rect(200, 100, img_surface.contents.w, img_surface.contents.h)
    sdl2.SDL_FreeSurface(img_surface)

    current_page = 1
    slider_value = 0.5
    combo_options = ["Option A", "Option B", "Option C"]
    selected_option = 0
    slider_dragging = False

    button_rect = sdl2.SDL_Rect(300, 350, 200, 60)
    slider_rect = sdl2.SDL_Rect(150, 180, 500, 20)
    combo_rect = sdl2.SDL_Rect(250, 250, 300, 60)

    running = True
    while running:
        renderer.color = sdl2.ext.Color(30, 30, 30)
        renderer.clear()

        if current_page == 1:
            render_button(renderer, button_rect, "ไปหน้า 2", font, (255, 255, 255), (70, 130, 180))
            sdl2.SDL_RenderCopy(renderer.sdlrenderer, img_texture, None, img_rect)
        else:
            render_slider(renderer, slider_rect, slider_value)
            render_combobox(renderer, combo_rect, combo_options, selected_option, font)
            render_button(renderer, button_rect, "กลับหน้า 1", font, (255, 255, 255), (34, 139, 34))

        renderer.present()

        for event in sdl2.ext.get_events():
            if event.type == sdl2.SDL_QUIT:
                running = False

            if event.type == sdl2.SDL_MOUSEBUTTONDOWN:
                x, y = event.button.x, event.button.y
                if point_in_rect(x, y, button_rect):
                    current_page = 2 if current_page == 1 else 1
                if current_page == 2 and point_in_rect(x, y, slider_rect):
                    slider_dragging = True
                if current_page == 2 and point_in_rect(x, y, combo_rect):
                    selected_option = (selected_option + 1) % len(combo_options)

            if event.type == sdl2.SDL_MOUSEBUTTONUP:
                slider_dragging = False

            if event.type == sdl2.SDL_MOUSEMOTION and slider_dragging:
                x = event.motion.x
                slider_value = min(max((x - slider_rect.x) / slider_rect.w, 0.0), 1.0)

        sdl2.SDL_Delay(16)

    sdl2.SDL_DestroyTexture(img_texture)
    sdl2.sdlttf.TTF_CloseFont(font)
    sdl2.sdlttf.TTF_Quit()
    sdl2.ext.quit()


if __name__ == "__main__":
    sys.exit(main())
