import pygame
import time
import os
import random
import math

WIN_WIDTH = 500
WIN_HEIGHT = 800

BIRD_IMGS = [pygame.transform.scale2x(pygame.image.load(os.path.join("assets", "bird1.png"))),
            pygame.transform.scale2x(pygame.image.load(os.path.join("assets", "bird2.png"))),
            pygame.transform.scale2x(pygame.image.load(os.path.join("assets", "bird3.png")))
            ]
PIPE_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join("assets", "pipe.png")))
BASE_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join("assets", "base.png")))
BG_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join("assets", "bg.png")))

class Bird:
    IMGS = BIRD_IMGS
    MAX_ROTATION = 25
    ROT_VEL = 20
    ANIMATION_TIME = 5

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.tilt = 0
        self.tick_count = 0
        self.y_vel = 0
        self.x_vel = 15
        self.height = y
        self.img_count = 0
        self.img = self.IMGS[0]
    
    def jump(self):
        self.y_vel = -32
        self.tick_count = 0
        self.height = self.y

    def move(self):
        self.tick_count += 1
        
        self.y_vel += 5

        if self.y_vel >= 20:
            self.y_vel = 20
        
        if self.y_vel < -32:
            self.y_vel = -52
        
        self.y = self.y + self.y_vel

    def draw(self, win):
        self.img_count += 1

        if self.img_count < self.ANIMATION_TIME:
            self.img = self.IMGS[0]
        elif self.img_count < self.ANIMATION_TIME * 2:
            self.img = self.IMGS[1]
        elif self.img_count < self.ANIMATION_TIME * 3:
            self.img = self.IMGS[2]
        elif self.img_count < self.ANIMATION_TIME * 4:
            self.img = self.IMGS[1]
        elif self.img_count == self.ANIMATION_TIME * 4 + 1:
            self.img = self.IMGS[0]
            self.img_count = 0

        self.tilt = - math.atan(self.y_vel/self.x_vel)
        print(self.y_vel, self.x_vel, self.tilt)
        
        rotated_image = pygame.transform.rotate(self.img, self.tilt * 180 / 3.1416)
        new_rect = rotated_image.get_rect(center = self.img.get_rect(topleft = (self.x, self.y)).center)
        win.blit(rotated_image, new_rect.topleft)
    
    def get_mask(self):
        return pygame.mask.from_surface(self.img)


def draw_window(win, bird):
    win.blit(BG_IMG, (0, 0))
    bird.draw(win)
    pygame.display.update()


def main():
    bird = Bird(200, 200)
    win = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))
    clock = pygame.time.Clock()

    run = True
    while run:
        clock.tick(30)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE or event.key == pygame.K_UP:
                    bird.jump()

        bird.move()
        draw_window(win, bird)
    
    pygame.quit()
    quit()

main()
