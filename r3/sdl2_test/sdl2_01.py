import sys
import sdl2
import sdl2.ext

WINDOW_WIDTH = 800
WINDOW_HEIGHT = 480

IMAGE_PATH = "assets/sample.jpg"

class DashboardApp:
    def __init__(self):
        sdl2.ext.init()

        self.window = sdl2.ext.Window("SDL2 Dashboard", size=(WINDOW_WIDTH, WINDOW_HEIGHT))
        self.window.show()

        self.renderer = sdl2.ext.Renderer(self.window)
        self.factory = sdl2.ext.SpriteFactory(sdl2.ext.TEXTURE, renderer=self.renderer)
        self.running = True

        self.load_resources()

    def load_resources(self):
        self.image = self.factory.from_image(IMAGE_PATH)
        self.button_rect = sdl2.SDL_Rect(WINDOW_WIDTH - 160, 20, 140, 50)

    def handle_events(self):
        events = sdl2.ext.get_events()
        for event in events:
            if event.type == sdl2.SDL_QUIT:
                self.running = False
            elif event.type == sdl2.SDL_MOUSEBUTTONDOWN:
                x, y = event.button.x, event.button.y
                if self.is_in_rect(x, y, self.button_rect):
                    print("ปุ่มถูกกด! (ยังไม่ได้ทำอะไร)")

    def is_in_rect(self, x, y, rect):
        return rect.x <= x <= rect.x + rect.w and rect.y <= y <= rect.y + rect.h

    def render(self):
        self.renderer.clear()

        # วาดภาพ
        self.renderer.copy(self.image, dstrect=sdl2.SDL_Rect(20, 20, 640, 360))

        # วาดปุ่ม
        sdl2.SDL_SetRenderDrawColor(self.renderer.sdlrenderer, 0, 122, 204, 255)
        sdl2.SDL_RenderFillRect(self.renderer.sdlrenderer, self.button_rect)

        # วาดข้อความบนปุ่ม
        # (สำหรับ demo นี้ใช้สีเฉยๆ แทน label; ถ้าต้องการใส่ฟอนต์ต้องใช้ SDL_ttf)

        self.renderer.present()

    def run(self):
        while self.running:
            self.handle_events()
            self.render()
        sdl2.ext.quit()

if __name__ == "__main__":
    app = DashboardApp()
    app.run()
