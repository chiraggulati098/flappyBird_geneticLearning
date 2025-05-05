import neat.population
import pygame
import neat
import os
import random
import math
from collections import deque

WIN_WIDTH = 600
WIN_HEIGHT = 800
CONCURRENT_PIPES = 3  

pygame.init()
pygame.font.init()  
win = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))
STAT_FONT = pygame.font.SysFont("comicsans", 50)

# Load images after display initialization
BIRD_IMGS = [pygame.transform.scale2x(pygame.image.load(os.path.join("assets", "bird1.png"))),
            pygame.transform.scale2x(pygame.image.load(os.path.join("assets", "bird2.png"))),
            pygame.transform.scale2x(pygame.image.load(os.path.join("assets", "bird3.png")))
            ]
PIPE_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join("assets", "pipe.png")))
BASE_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join("assets", "base.png")))
BG_IMG = pygame.transform.scale(pygame.image.load(os.path.join("assets", "bg.png")).convert_alpha(), (600, 900))

gen = 0

class Game:
    score = 0
    max_score = 0  

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
    VEL = 450 / 60  # Match base game speed (450/FRAMERATE)
    PIPE_DISTANCE = 400  # Distance between pipes

    def __init__(self, x):
        self.x = x
        self.height = 0
        self.top = 0
        self.bottom = 0
        self.passed = False
        self.set_height()

    def set_height(self):
        self.height = random.randrange(50, 450)
        self.top = self.height - self.PIPEHIGH.get_height()
        self.bottom = self.height + self.WINDOW

    def move(self):
        self.x -= self.VEL

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
        self.x_vel = 450 / 60  # Match base game speed
        self.height = y
        self.img_count = 0
        self.img = self.IMGS[0]
    
    def jump(self):
        self.y_vel = -960 / 60  # Match base game jump velocity
        self.tick_count = 0
        self.height = self.y

    def move(self):
        self.tick_count += 1
        
        # Match base game physics
        self.y_vel += 4500 / 60**2

        if self.y_vel >= 600 / 60:
            self.y_vel = 600 / 60
        
        if self.y_vel < -960 / 60:
            self.y_vel = -960 / 60
        
        self.y = self.y + self.y_vel

    def draw(self, win):
        self.img_count += 1

        # For animation of bird, loop through three images
        if self.img_count <= self.ANIMATION_TIME:
            self.img = self.IMGS[0]
        elif self.img_count <= self.ANIMATION_TIME*2:
            self.img = self.IMGS[1]
        elif self.img_count <= self.ANIMATION_TIME*3:
            self.img = self.IMGS[2]
        elif self.img_count <= self.ANIMATION_TIME*4:
            self.img = self.IMGS[1]
        elif self.img_count == self.ANIMATION_TIME*4 + 1:
            self.img = self.IMGS[0]
            self.img_count = 0

        # so when bird is nose diving it isn't flapping
        if self.tilt <= -80:
            self.img = self.IMGS[1]
            self.img_count = self.ANIMATION_TIME*2

        # Calculate tilt based on velocity ratio like in base game
        self.tilt = -math.atan(self.y_vel/self.x_vel)
        
        rotated_image = pygame.transform.rotate(self.img, self.tilt * 180 / 3.1416)
        new_rect = rotated_image.get_rect(center = self.img.get_rect(topleft = (self.x, self.y)).center)
        win.blit(rotated_image, new_rect.topleft)

    def get_mask(self):
        return pygame.mask.from_surface(self.img)

class Base:
    VEL = 450 / 60  # Match base game speed (450/FRAMERATE)
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

def draw_window(win, birds, pipes, base, score, gen):
    win.blit(BG_IMG, (0,0))

    for pipe in pipes:
        pipe.draw(win)

    base.draw(win)
    for bird in birds:
        # Draw lines from bird to next pipe
        if len(pipes) > 0:
            next_pipe = None
            for pipe in pipes:
                if pipe.x > bird.x:
                    next_pipe = pipe
                    break
            if next_pipe:
                # Draw line to top pipe
                pygame.draw.line(win, (255,0,0), 
                    (bird.x + bird.img.get_width()/2, bird.y + bird.img.get_height()/2),
                    (next_pipe.x + next_pipe.PIPELOW.get_width()/2, next_pipe.top + next_pipe.PIPEHIGH.get_height()),
                    2)
                # Draw line to bottom pipe
                pygame.draw.line(win, (255,0,0),
                    (bird.x + bird.img.get_width()/2, bird.y + bird.img.get_height()/2),
                    (next_pipe.x + next_pipe.PIPELOW.get_width()/2, next_pipe.bottom),
                    2)
        bird.draw(win)

    # score
    score_label = STAT_FONT.render("Score: " + str(score),1,(255,255,255))
    win.blit(score_label, (WIN_WIDTH - score_label.get_width() - 15, 10))
    
    # max score - add these lines
    Game.max_score = max(Game.max_score, score)
    max_score_label = STAT_FONT.render("Max: " + str(Game.max_score),1,(255,255,255))
    win.blit(max_score_label, (WIN_WIDTH - max_score_label.get_width() - 15, 50))
    
    # generations
    gen_label = STAT_FONT.render("Gen: " + str(gen),1,(255,255,255))
    win.blit(gen_label, (10, 10))

    # alive
    alive_label = STAT_FONT.render("Alive: " + str(len(birds)),1,(255,255,255))
    win.blit(alive_label, (10, 50))

    pygame.display.update()

def eval_genomes(genomes, config):
    global win, gen
    gen += 1

    nets = []
    birds = []
    ge = []
    for genome_id, genome in genomes:
        genome.fitness = 0  # start with fitness level of 0
        net = neat.nn.FeedForwardNetwork.create(genome, config)
        nets.append(net)
        birds.append(Bird(50, 200))
        ge.append(genome)

    base = Base(730)
    # Initialize pipes with proper spacing
    pipes = deque()
    for i in range(CONCURRENT_PIPES):
        pipes.append(Pipes(700 + i * Pipes.PIPE_DISTANCE))
    score = 0

    clock = pygame.time.Clock()

    run = True
    while run and len(birds) > 0:
        clock.tick(60)  # Match base game framerate

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                pygame.quit()
                quit()
                break

        # Determine which pipe to use for inputs
        pipe_ind = 0
        if len(birds) > 0:
            # Find the closest pipe ahead of any bird
            closest_dist = float('inf')
            for i, pipe in enumerate(pipes):
                # Change condition to check if bird hasn't passed the right edge of pipe
                pipe_right_edge = pipe.x + pipe.PIPELOW.get_width()
                if pipe_right_edge > birds[0].x:
                    dist = pipe_right_edge - birds[0].x
                    if dist < closest_dist:
                        closest_dist = dist
                        pipe_ind = i

        # Move birds and get neural network decisions
        for x, bird in enumerate(birds):
            ge[x].fitness += 0.1  # give small reward for staying alive
            bird.move()

            # Neural network inputs - bird's height, distances to pipe edges
            output = nets[x].activate((
                bird.y,
                abs(bird.y - pipes[pipe_ind].height),  # distance to top pipe
                abs(bird.y - pipes[pipe_ind].bottom),  # distance to bottom pipe
                pipes[pipe_ind].x - bird.x,            # distance to pipe's leading edge
                (pipes[pipe_ind].x + pipes[pipe_ind].PIPELOW.get_width()) - bird.x  # distance to pipe's trailing edge
            ))

            if output[0] > 0.5:  # tanh activation function output is between -1 and 1
                bird.jump()

        # Move pipes and handle collisions
        rem_pipes = []
        add_pipe = False
        for pipe in pipes:
            pipe.move()

            # Check for collisions
            for x, bird in enumerate(birds):
                if Game.collision_detected(bird, pipe):
                    ge[x].fitness -= 1  # penalize for collision
                    birds.pop(x)
                    nets.pop(x)
                    ge.pop(x)
                    continue

                # Check if bird passed pipe
                pipe_right_edge = pipe.x + pipe.PIPELOW.get_width()
                if not pipe.passed and pipe_right_edge < bird.x:
                    pipe.passed = True
                    add_pipe = True

            # Remove pipes that are off screen
            if pipe.x + pipe.PIPELOW.get_width() < 0:
                rem_pipes.append(pipe)            # Add new pipe and reward surviving birds
        if add_pipe:
            score += 1
            for g in ge:  # reward birds that made it through
                g.fitness += 5

        # Remove old pipes and add new ones to maintain 5 pipes
        for r in rem_pipes:
            pipes.remove(r)
            # Add new pipe at a fixed distance from the last pipe
            new_x = pipes[-1].x + Pipes.PIPE_DISTANCE
            pipes.append(Pipes(new_x))

        # Check for birds hitting ground or going too high
        for x, bird in enumerate(birds):
            if bird.y + bird.img.get_height() >= 730 or bird.y < 0:
                birds.pop(x)
                nets.pop(x)
                ge.pop(x)

        draw_window(win, birds, pipes, base, score, gen)

def run(config_file):
    config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction,
                                neat.DefaultSpeciesSet, neat.DefaultStagnation,
                                config_file)

    # Create population and add reporters
    p = neat.Population(config)
    p.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    p.add_reporter(stats)

    # Run for up to 200 generations
    winner = p.run(eval_genomes, 200)
    print('\nBest genome:\n{!s}'.format(winner))

if __name__ == '__main__':
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, 'config-feedforward.txt')
    run(config_path)
