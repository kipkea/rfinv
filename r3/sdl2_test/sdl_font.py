import sys
import sdl2
import sdl2.ext
import sdl2.ttf
from sdl2 import SDL_UnicodeToUTF8

WINDOW_WIDTH = 800
WINDOW_HEIGHT = 480

IMAGE_PATH = "assets/sample.jpg"
FONT_PATH = "assets/THSarabun.ttf"  # ฟอนต์ภาษาไทยที่ดาวน์โหลด

class DashboardApp:
    def __init__(self):
        sdl2.ext.init()
        sdl2.ttf.init()

        self.window = sdl2.ext.Window("SDL2 Dashboard", size=(WINDOW_WIDTH, WINDOW_HEIGHT))
        self.window.show()

        self.renderer = sdl2.ext.Renderer(self.window)
        self.factory = sdl2.ext.SpriteFactory(sdl2.ext.TEXTURE, renderer=self.renderer)
        self.running = True

        self.load_resources()

    def load_resources(self):
        self.image = self.factory.from_image(IMAGE_PATH)
        self.button_rect = sdl2.SDL_Rect(WINDOW_WIDTH - 160, 20, 140, 50)
        
        # โหลดฟอนต์ภาษาไทย
        self.font = sdl2.ttf.TTF_OpenFont(FONT_PATH, 24)  # ขนาดฟอนต์ 24

    def handle_events(self):
        events = sdl2.ext.get_events()
        for event in events:
            if event.type == sdl2.SDL_QUIT:
                self.running = False
            elif event.type == sdl2.SDL_MOUSEBUTTONDOWN:
                x, y = event.button.x, event.button.y
                if self.is_in_rect(x, y, self.button_rect):
                    print("ปุ่มถูกกด!")

    def is_in_rect(self, x, y, rect):
        return rect.x <= x <= rect.x + rect.w and rect.y <= y <= rect.y + rect.h

    def render(self):
        self.renderer.clear()

        # วาดภาพ
        self.renderer.copy(self.image, dstrect=sdl2.SDL_Rect(20, 20, 640, 360))

        # วาดปุ่ม
        sdl2.SDL_SetRenderDrawColor(self.renderer.sdlrenderer, 0, 122, 204, 255)
        sdl2.SDL_RenderFillRect(self.renderer.sdlrenderer, self.button_rect)

        # วาดข้อความบนปุ่ม (ใช้ฟอนต์ไทย)
        text_surface = sdl2.ttf.TTF_RenderText_Blended(self.font, "คลิกที่นี่", sdl2.SDL_Color(255, 255, 255))  # ข้อความในปุ่ม
        text_texture = sdl2.SDL_CreateTextureFromSurface(self.renderer.sdlrenderer, text_surface)
        text_rect = sdl2.SDL_Rect(self.button_rect.x + 20, self.button_rect.y + 10, text_surface.w, text_surface.h)
        sdl2.SDL_RenderCopy(self.renderer.sdlrenderer, text_texture, None, text_rect)
        sdl2.SDL_FreeSurface(text_surface)
        sdl2.SDL_DestroyTexture(text_texture)

        # วาดข้อความ label
        label_surface = sdl2.ttf.TTF_RenderText_Blended(self.font, "ข้อความภาษาไทยบน UI", sdl2.SDL_Color(255, 255, 255))
        label_texture = sdl2.SDL_CreateTextureFromSurface(self.renderer.sdlrenderer, label_surface)
        label_rect = sdl2.SDL_Rect(20, 400, label_surface.w, label_surface.h)
        sdl2.SDL_RenderCopy(self.renderer.sdlrenderer, label_texture, None, label_rect)
        sdl2.SDL_FreeSurface(label_surface)
        sdl2.SDL_DestroyTexture(label_texture)

        self.renderer.present()

    def run(self):
        while self.running:
            self.handle_events()
            self.render()
        sdl2.ext.quit()

if __name__ == "__main__":
    app = DashboardApp()
    app.run()
