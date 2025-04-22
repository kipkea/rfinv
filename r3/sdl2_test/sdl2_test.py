import pygame
import sys

pygame.init()

# สร้างหน้าต่าง
screen = pygame.display.set_mode((640, 480))
pygame.display.set_caption("Hello SDL2 via pygame on Raspberry Pi!")

# สีพื้นหลัง
color = (100, 149, 237)  # Cornflower Blue

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    screen.fill(color)
    pygame.display.flip()

pygame.quit()
sys.exit()
