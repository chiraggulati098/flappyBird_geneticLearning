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

CONCURRENT_PIPES = 6

# Works for maximum 60
FRAMERATE = 60

# TODO: Implement score, collision detection and game abortion
class Game:
    score = 0

    def collision_detected(bird, pipe):
        bird_mask = bird.get_mask()
        top_mask = pygame.mask.from_surface(pipe.PIPEHIGH)
        bottom_mask = pygame.mask.from_surface(pipe.PIPELOW)
        top_offset = (pipe.x - bird.x, pipe.top - round(bird.y))
        bottom_offset = (pipe.x - bird.x, pipe.bottom - round(bird.y))

        b_point = bird_mask.overlap(bottom_mask, bottom_offset)
        t_point = bird_mask.overlap(top_mask, top_offset)

        if b_point or t_point:
            return True

        return False

class Pipes:
    PIPELOW = PIPE_IMG
    PIPEHIGH = pygame.transform.rotate(PIPE_IMG, 180)
    WINDOW = 200
    PIPE_DISTANCE = 350

    def __init__(self, pipe_no):
        self.x = WIN_WIDTH + self.PIPE_DISTANCE * pipe_no
        self.height = 0
        self.top = 0
        self.bottom = 0
        self.set_height()

    def set_height(self):
        """
        set the height of the pipe, from the top of the screen
        """
        self.height = random.randrange(50, 450)
        self.top = self.height - self.PIPEHIGH.get_height()
        self.bottom = self.height + self.WINDOW

    def reloc(self, pipes_list):
        self.x -= 450 / FRAMERATE
        if self.x + self.PIPELOW.get_width() < 0:  # Only remove when pipe is completely off screen
            Game.score += 1
            rightmost_x = max(pipe.x for pipe in pipes_list)
            self.x = rightmost_x + self.PIPE_DISTANCE
            self.set_height()

    def draw(self, win):
        win.blit(self.PIPEHIGH, (self.x, self.top))
        win.blit(self.PIPELOW, (self.x, self.bottom))

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


def game_loop():
    bird = Bird(50, 200)
    pipes = []
    base = Base(730)  
    active_index = 0
    Game.score = 0  

    for i in range(CONCURRENT_PIPES):
        pipes.append(Pipes(i))

    clock = pygame.time.Clock()

    run = True
    while run:
        clock.tick(FRAMERATE)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False  
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE or event.key == pygame.K_UP:
                    bird.jump()

        bird.move()
        base.move()
        for i in pipes:
            i.reloc(pipes)
            if Game.collision_detected(bird, i):
                return True  

        draw_window(win, bird, pipes, base)

def main():
    run = True
    while run:
        run = game_loop() 

    pygame.quit()
    quit()

main()
