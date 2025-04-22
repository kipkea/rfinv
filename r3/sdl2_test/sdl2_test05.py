import sys
import sdl2
import sdl2.ext

def point_in_rect(x, y, rect):
    return rect.x <= x <= rect.x + rect.w and rect.y <= y <= rect.y + rect.h

def render_button(renderer, rect, text, font, text_color, bg_color):
    sdl2.SDL_SetRenderDrawColor(renderer.sdlrenderer, *bg_color, 255)
    sdl2.SDL_RenderFillRect(renderer.sdlrenderer, rect)

    surface = sdl2.sdlttf.TTF_RenderUTF8_Solid(font, text.encode(), sdl2.SDL_Color(*text_color))
    texture = sdl2.SDL_CreateTextureFromSurface(renderer.sdlrenderer, surface.contents)

    text_rect = sdl2.SDL_Rect(
        rect.x + (rect.w - surface.contents.w) // 2,
        rect.y + (rect.h - surface.contents.h) // 2,
        surface.contents.w,
        surface.contents.h
    )

    sdl2.SDL_RenderCopy(renderer.sdlrenderer, texture, None, text_rect)
    sdl2.SDL_FreeSurface(surface)
    sdl2.SDL_DestroyTexture(texture)

def main():
    sdl2.ext.init()
    sdl2.sdlttf.TTF_Init()

    window = sdl2.ext.Window("Touch Screen Menu", size=(800, 480))
    window.show()

    renderer = sdl2.ext.Renderer(window)

    font_path = "assets/THSarabun.ttf"
    font = sdl2.sdlttf.TTF_OpenFont(font_path.encode(), 36)
    if not font:
        print("โหลดฟอนต์ไม่ได้!")
        sys.exit(1)

    current_page = 1

    button_rect = sdl2.SDL_Rect(300, 200, 200, 80)  # กำหนดตำแหน่งปุ่ม

    running = True
    while running:
        renderer.color = sdl2.ext.Color(30, 30, 30)  # พื้นหลังสีเทาเข้ม
        renderer.clear()

        if current_page == 1:
            render_button(renderer, button_rect, "ไปหน้า 2", font, (255, 255, 255), (0, 128, 255))
        else:
            render_button(renderer, button_rect, "กลับหน้า 1", font, (255, 255, 255), (0, 200, 100))

            # วาดข้อความเพิ่มเติมในหน้า 2
            info_surface = sdl2.sdlttf.TTF_RenderUTF8_Solid(
                font, "หน้านี้: Page 2".encode(), sdl2.SDL_Color(255, 255, 0)
            )
            info_texture = sdl2.SDL_CreateTextureFromSurface(renderer.sdlrenderer, info_surface.contents)
            info_rect = sdl2.SDL_Rect(280, 100, info_surface.contents.w, info_surface.contents.h)
            sdl2.SDL_RenderCopy(renderer.sdlrenderer, info_texture, None, info_rect)
            sdl2.SDL_FreeSurface(info_surface)
            sdl2.SDL_DestroyTexture(info_texture)

        renderer.present()

        events = sdl2.ext.get_events()
        for event in events:
            if event.type == sdl2.SDL_QUIT:
                running = False

            if event.type == sdl2.SDL_MOUSEBUTTONDOWN:
                x, y = event.button.x, event.button.y
                if point_in_rect(x, y, button_rect):
                    current_page = 2 if current_page == 1 else 1

        sdl2.SDL_Delay(50)

    sdl2.sdlttf.TTF_CloseFont(font)
    sdl2.sdlttf.TTF_Quit()
    sdl2.ext.quit()


if __name__ == "__main__":
    sys.exit(main())
