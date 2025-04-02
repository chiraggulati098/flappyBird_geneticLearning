import pygame
import time
import os
import random
import math

WIN_WIDTH = 600
WIN_HEIGHT = 800

# Initialize pygame display first
pygame.init()
win = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))

# Load images after display initialization
BIRD_IMGS = [pygame.transform.scale2x(pygame.image.load(os.path.join("assets", "bird1.png"))),
            pygame.transform.scale2x(pygame.image.load(os.path.join("assets", "bird2.png"))),
            pygame.transform.scale2x(pygame.image.load(os.path.join("assets", "bird3.png")))
            ]
PIPE_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join("assets", "pipe.png")))
BASE_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join("assets", "base.png")))
BG_IMG = pygame.transform.scale(pygame.image.load(os.path.join("assets", "bg.png")).convert_alpha(), (600, 900))

CONCURRENT_PIPES = 3

# Works for maximum 60
FRAMERATE = 30

# TODO: Implement score, collision detection and game abortion
class Game:
    score = 0

    # still a WIP, have to work with sprites
    def collide_mask_rect(left, right):
        xoffset = right.rect[0] - left.rect[0]
        yoffset = right.rect[1] - left.rect[1]
        try:
            leftmask = left.mask
        except AttributeError:
            leftmask = pygame.mask.Mask(left.size, True)
        try:
            rightmask = right.mask
        except AttributeError:
            rightmask = pygame.mask.Mask(right.size, True)
        return leftmask.overlap(rightmask, (xoffset, yoffset))

    def collision_detected(Bird, ActivePipe):
        return pygame.sprite.collide_mask(Bird, ActivePipe) == None

class Pipes:
    PIPELOW = PIPE_IMG
    PIPEHIGH = pygame.transform.rotate(PIPE_IMG, 180)
    WINDOW = 200

    def __init__(self, pipe_no):
        # Pipes have to be initialized from 0 indexing
        self.height = self.randomize_height()
        self.x = 600 + 400 * pipe_no

    def reloc(self):
        self.x -= 450 / FRAMERATE
        if self.x < -10:
            Game.score += 1
            self.x = 1200
            self.randomize_height()

    def randomize_height(self):
        # Randomization appears to be skewed, to look into later
        return 300 + 600 * random.random()

    def draw(self, win):
        self.rect_down = Pipes.PIPELOW.get_rect(center = Pipes.PIPELOW.get_rect(topleft = (self.x, self.height + self.WINDOW // 2 )).center)
        self.rect_up = Pipes.PIPEHIGH.get_rect(center = Pipes.PIPEHIGH.get_rect(bottomleft = (self.x, self.height - self.WINDOW // 2 )).center)

        win.blit(Pipes.PIPELOW, self.rect_down.topleft)
        win.blit(Pipes.PIPEHIGH, self.rect_up.topleft)

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
        self.x_vel = 450 / FRAMERATE
        self.height = y
        self.img_count = 0
        self.img = self.IMGS[0]
    
    def jump(self):
        # possible issue with this
        self.y_vel = -960 / FRAMERATE

        self.tick_count = 0
        self.height = self.y

    def move(self):
        self.tick_count += 1
        
        # possible issue with this
        self.y_vel += 4500 / FRAMERATE**2

        if self.y_vel >= 600 / FRAMERATE:
            self.y_vel = 600 / FRAMERATE
        
        if self.y_vel < -960 / FRAMERATE:
            self.y_vel = -960 / FRAMERATE
        
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

        self.tilt = -math.atan(self.y_vel/self.x_vel)
        
        rotated_image = pygame.transform.rotate(self.img, self.tilt * 180 / 3.1416)
        new_rect = rotated_image.get_rect(center = self.img.get_rect(topleft = (self.x, self.y)).center)
        win.blit(rotated_image, new_rect.topleft)
    
    def get_mask(self):
        return pygame.mask.from_surface(self.img)

class Base:
    VEL = 450 / FRAMERATE
    WIDTH = BASE_IMG.get_width()
    IMG = BASE_IMG

    def __init__(self, y):
        self.y = y
        self.x1 = 0
        self.x2 = self.WIDTH

    def move(self):
        self.x1 -= self.VEL
        self.x2 -= self.VEL
        if self.x1 + self.WIDTH < 0:
            self.x1 = self.x2 + self.WIDTH

        if self.x2 + self.WIDTH < 0:
            self.x2 = self.x1 + self.WIDTH

    def draw(self, win):
        win.blit(self.IMG, (self.x1, self.y))
        win.blit(self.IMG, (self.x2, self.y))

def draw_window(win, bird, pipes, base):
    win.blit(BG_IMG, (0, 0))
    bird.draw(win)
    for i in pipes:
        i.draw(win)
    base.draw(win)
    pygame.display.update()


def main():
    bird = Bird(50, 200)
    pipes = []
    base = Base(730)  
    active_index = 0

    for i in range(CONCURRENT_PIPES):
        pipes.append(Pipes(i))

    clock = pygame.time.Clock()

    run = True
    while run:
        clock.tick(FRAMERATE)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE or event.key == pygame.K_UP:
                    bird.jump()

        bird.move()
        base.move()
        for i in pipes:
            i.reloc()

        draw_window(win, bird, pipes, base)

    pygame.quit()
    quit()

main()
