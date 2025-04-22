import sys
import sdl2
import sdl2.ext
import sdl2.sdlttf

def main():
    sdl2.ext.init()
    sdl2.sdlttf.TTF_Init()

    window = sdl2.ext.Window("RFID Display", size=(800, 480))
    window.show()

    renderer = sdl2.ext.Renderer(window)
    renderer.color = sdl2.ext.Color(0, 0, 0)
    renderer.clear()
    renderer.present()

    # โหลดฟอนต์ (ใช้ฟอนต์ FreeSans)
    font_path = "assets/THSarabun.ttf"
    font = sdl2.sdlttf.TTF_OpenFont(font_path.encode(), 48)
    if not font:
        print("โหลดฟอนต์ไม่ได้!")
        sys.exit(1)

    running = True
    tag_text = "Waiting for RFID..."

    while running:
        events = sdl2.ext.get_events()
        for event in events:
            if event.type == sdl2.SDL_QUIT:
                running = False

        # เปลี่ยนข้อความทดสอบ (แทนการอ่าน RFID)
        #tag_text = "RFID TAG: 1234-5678"
        tag_text = "สวัสดีเมืองไทยจาก Raspberry Pi 3"

        renderer.color = sdl2.ext.Color(0, 0, 0)  # พื้นหลังดำ
        renderer.clear()

        # Render ข้อความใหม่
        color = sdl2.SDL_Color(255, 255, 0)  # สีเหลือง
        surface = sdl2.sdlttf.TTF_RenderUTF8_Solid(font, tag_text.encode(), color)

        if surface:
            texture = sdl2.SDL_CreateTextureFromSurface(renderer.sdlrenderer, surface.contents)
            rect = sdl2.SDL_Rect(100, 200, surface.contents.w, surface.contents.h)
            sdl2.SDL_RenderCopy(renderer.sdlrenderer, texture, None, rect)
            sdl2.SDL_FreeSurface(surface)
            sdl2.SDL_DestroyTexture(texture)

        renderer.present()
        sdl2.SDL_Delay(5000)

        running = False

    sdl2.sdlttf.TTF_CloseFont(font)
    sdl2.sdlttf.TTF_Quit()
    sdl2.ext.quit()


if __name__ == "__main__":
    sys.exit(main())
