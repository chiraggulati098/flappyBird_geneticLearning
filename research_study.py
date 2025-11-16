import neat
import pygame
import os
import random
import math
import csv
import time
from collections import deque
from datetime import datetime
import copy
import multiprocessing as mp
import sys

# Import research configuration
try:
    from research_config import *
except ImportError:
    print("Warning: research_config.py not found, using default values")
    # Default values if config file is missing
    WINDOW_SIZES = [150, 200, 250, 300]
    PIPE_DISTANCES = [300, 400, 500, 600]
    TARGET_SCORES = [10, 20, 50, 100, 200]
    MAX_GENERATIONS = 300
    RUNS_PER_CONFIG = 3
    POPULATION_SIZE = 50
    SHOW_GRAPHICS = False
    PRINT_PROGRESS = True
    USE_MULTIPROCESSING = True
    NUM_PROCESSES = None
    RESULTS_FILENAME = None
    FRAME_LIMIT = 10000
    FITNESS_REWARD_ALIVE = 0.1
    FITNESS_REWARD_PIPE = 5
    FITNESS_PENALTY_COLLISION = 1

# Build research configuration dictionary
RESEARCH_CONFIG = {
    'window_sizes': WINDOW_SIZES,
    'pipe_distances': PIPE_DISTANCES,
    'target_scores': TARGET_SCORES,
    'max_generations': MAX_GENERATIONS,
    'runs_per_config': RUNS_PER_CONFIG,
    'results_file': RESULTS_FILENAME or f'research_results_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv',
    'show_graphics': SHOW_GRAPHICS,
    'print_progress': PRINT_PROGRESS,
    'frame_limit': FRAME_LIMIT,
    'fitness_reward_alive': FITNESS_REWARD_ALIVE,
    'fitness_reward_pipe': FITNESS_REWARD_PIPE,
    'fitness_penalty_collision': FITNESS_PENALTY_COLLISION,
    'use_multiprocessing': False,  # Disabled due to pickling issues
    'num_processes': NUM_PROCESSES or (mp.cpu_count() - 1),  # Leave one CPU free
}

# Game constants
WIN_WIDTH = 600
WIN_HEIGHT = 800
CONCURRENT_PIPES = 3

# Initialize pygame (even if not showing graphics)
pygame.init()
pygame.font.init()
if RESEARCH_CONFIG['show_graphics']:
    win = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))
    STAT_FONT = pygame.font.SysFont("comicsans", 50)
    
    # Load images
    BIRD_IMGS = [pygame.transform.scale2x(pygame.image.load(os.path.join("assets", "bird1.png"))),
                pygame.transform.scale2x(pygame.image.load(os.path.join("assets", "bird2.png"))),
                pygame.transform.scale2x(pygame.image.load(os.path.join("assets", "bird3.png")))]
    PIPE_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join("assets", "pipe.png")))
    BASE_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join("assets", "base.png")))
    BG_IMG = pygame.transform.scale(pygame.image.load(os.path.join("assets", "bg.png")).convert_alpha(), (600, 900))
else:
    win = None
    STAT_FONT = None
    # Create dummy images for collision detection
    BIRD_IMGS = [pygame.Surface((34, 24)) for _ in range(3)]
    PIPE_IMG = pygame.Surface((52, 320))
    BASE_IMG = pygame.Surface((336, 112))
    BG_IMG = pygame.Surface((600, 900))

class Game:
    score = 0
    max_score = 0
    generation_scores = []  # Track scores achieved each generation

    @staticmethod
    def collision_detected(bird, pipe):
        bird_mask = bird.get_mask()
        top_mask = pygame.mask.from_surface(pipe.PIPEHIGH)
        bottom_mask = pygame.mask.from_surface(pipe.PIPELOW)
        top_offset = (pipe.x - bird.x, pipe.top - round(bird.y))
        bottom_offset = (pipe.x - bird.x, pipe.bottom - round(bird.y))

        b_point = bird_mask.overlap(bottom_mask, bottom_offset)
        t_point = bird_mask.overlap(top_mask, top_offset)

        return b_point or t_point

class Pipes:
    PIPELOW = PIPE_IMG
    PIPEHIGH = pygame.transform.rotate(PIPE_IMG, 180)
    VEL = 450 / 60  # Match base game speed (450/FRAMERATE)
    
    # These will be set by research configuration
    WINDOW = 200
    PIPE_DISTANCE = 400

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
        if win:
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
        self.x_vel = 450 / 60
        self.height = y
        self.img_count = 0
        self.img = self.IMGS[0]
    
    def jump(self):
        self.y_vel = -960 / 60
        self.tick_count = 0
        self.height = self.y

    def move(self):
        self.tick_count += 1
        self.y_vel += 4500 / 60**2

        if self.y_vel >= 600 / 60:
            self.y_vel = 600 / 60
        
        if self.y_vel < -960 / 60:
            self.y_vel = -960 / 60
        
        self.y = self.y + self.y_vel

    def draw(self, win):
        if not win:
            return
            
        self.img_count += 1

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

        if self.tilt <= -80:
            self.img = self.IMGS[1]
            self.img_count = self.ANIMATION_TIME*2

        self.tilt = -math.atan(self.y_vel/self.x_vel)
        
        rotated_image = pygame.transform.rotate(self.img, self.tilt * 180 / 3.1416)
        new_rect = rotated_image.get_rect(center = self.img.get_rect(topleft = (self.x, self.y)).center)
        win.blit(rotated_image, new_rect.topleft)

    def get_mask(self):
        return pygame.mask.from_surface(self.img)

class Base:
    VEL = 450 / 60
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
        if win:
            win.blit(self.IMG, (self.x1, self.y))
            win.blit(self.IMG, (self.x2, self.y))

def draw_window(win, birds, pipes, base, score, gen):
    if not win:
        return
        
    win.blit(BG_IMG, (0,0))

    for pipe in pipes:
        pipe.draw(win)

    base.draw(win)
    for bird in birds:
        if len(pipes) > 0:
            next_pipe = None
            for pipe in pipes:
                if pipe.x > bird.x:
                    next_pipe = pipe
                    break
            if next_pipe:
                pygame.draw.line(win, (255,0,0), 
                    (bird.x + bird.img.get_width()/2, bird.y + bird.img.get_height()/2),
                    (next_pipe.x + next_pipe.PIPELOW.get_width()/2, next_pipe.top + next_pipe.PIPEHIGH.get_height()),
                    2)
                pygame.draw.line(win, (255,0,0),
                    (bird.x + bird.img.get_width()/2, bird.y + bird.img.get_height()/2),
                    (next_pipe.x + next_pipe.PIPELOW.get_width()/2, next_pipe.bottom),
                    2)
        bird.draw(win)

    score_label = STAT_FONT.render("Score: " + str(score),1,(255,255,255))
    win.blit(score_label, (WIN_WIDTH - score_label.get_width() - 15, 10))
    
    Game.max_score = max(Game.max_score, score)
    max_score_label = STAT_FONT.render("Max: " + str(Game.max_score),1,(255,255,255))
    win.blit(max_score_label, (WIN_WIDTH - max_score_label.get_width() - 15, 50))
    
    gen_label = STAT_FONT.render("Gen: " + str(gen),1,(255,255,255))
    win.blit(gen_label, (10, 10))

    alive_label = STAT_FONT.render("Alive: " + str(len(birds)),1,(255,255,255))
    win.blit(alive_label, (10, 50))

    pygame.display.update()

class ResearchTracker:
    def __init__(self, target_scores, max_generations):
        self.target_scores = target_scores
        self.max_generations = max_generations
        self.generations_to_reach = {score: None for score in target_scores}
        self.current_generation = 0
        self.max_score_achieved = 0
        self.finished = False
        
    def update(self, generation, max_score):
        self.current_generation = generation
        self.max_score_achieved = max(self.max_score_achieved, max_score)
        
        # Check if we've reached any new target scores
        for score in self.target_scores:
            if self.generations_to_reach[score] is None and max_score >= score:
                self.generations_to_reach[score] = generation
                
        # Check if we've reached all targets or hit max generations
        if (all(g is not None for g in self.generations_to_reach.values()) or 
            generation >= self.max_generations):
            self.finished = True
            
    def get_results(self):
        return {
            'max_score_achieved': self.max_score_achieved,
            'generations_to_reach': self.generations_to_reach,
            'total_generations': self.current_generation,
            'completed': all(g is not None for g in self.generations_to_reach.values())
        }

def eval_genomes(genomes, config, tracker, config_dict):
    global win
    
    nets = []
    birds = []
    ge = []
    for genome_id, genome in genomes:
        genome.fitness = 0
        net = neat.nn.FeedForwardNetwork.create(genome, config)
        nets.append(net)
        birds.append(Bird(50, 200))
        ge.append(genome)

    base = Base(730)
    pipes = deque()
    for i in range(CONCURRENT_PIPES):
        pipes.append(Pipes(700 + i * Pipes.PIPE_DISTANCE))
    score = 0

    if config_dict.get('show_graphics', False):
        clock = pygame.time.Clock()

    run = True
    frame_count = 0
    while run and len(birds) > 0:
        if config_dict.get('show_graphics', False):
            clock.tick(60)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    run = False
                    pygame.quit()
                    quit()
                    break
        else:
            # Fast mode - no graphics, limited frames for efficiency
            frame_count += 1
            if frame_count > config_dict.get('frame_limit', 10000):  # Prevent infinite loops
                break

        base.move()

        pipe_ind = 0
        if len(birds) > 0:
            closest_dist = float('inf')
            for i, pipe in enumerate(pipes):
                pipe_right_edge = pipe.x + pipe.PIPELOW.get_width()
                if pipe_right_edge > birds[0].x:
                    dist = pipe_right_edge - birds[0].x
                    if dist < closest_dist:
                        closest_dist = dist
                        pipe_ind = i

        for x, bird in enumerate(birds):
            ge[x].fitness += config_dict.get('fitness_reward_alive', 0.1)
            bird.move()

            output = nets[x].activate((
                bird.y,
                abs(bird.y - pipes[pipe_ind].height),
                abs(bird.y - pipes[pipe_ind].bottom),
                pipes[pipe_ind].x - bird.x,
                (pipes[pipe_ind].x + pipes[pipe_ind].PIPELOW.get_width()) - bird.x
            ))

            if output[0] > 0.5:
                bird.jump()

        rem_pipes = []
        add_pipe = False
        for pipe in pipes:
            pipe.move()

            for x, bird in enumerate(birds):
                if Game.collision_detected(bird, pipe):
                    ge[x].fitness -= config_dict.get('fitness_penalty_collision', 1)
                    birds.pop(x)
                    nets.pop(x)
                    ge.pop(x)
                    continue

                pipe_right_edge = pipe.x + pipe.PIPELOW.get_width()
                if not pipe.passed and pipe_right_edge < bird.x:
                    pipe.passed = True
                    add_pipe = True

            if pipe.x + pipe.PIPELOW.get_width() < 0:
                rem_pipes.append(pipe)

        if add_pipe:
            score += 1
            for g in ge:
                g.fitness += config_dict.get('fitness_reward_pipe', 5)

        for r in rem_pipes:
            pipes.remove(r)
            new_x = pipes[-1].x + Pipes.PIPE_DISTANCE
            pipes.append(Pipes(new_x))

        for x, bird in enumerate(birds):
            if bird.y + bird.img.get_height() >= 730 or bird.y < 0:
                birds.pop(x)
                nets.pop(x)
                ge.pop(x)

        if config_dict.get('show_graphics', False):
            draw_window(win, birds, pipes, base, score, tracker.current_generation)

    Game.generation_scores.append(score)
    return score

def run_single_experiment_mp(args):
    """Wrapper function for multiprocessing - runs a single experiment"""
    window_size, pipe_distance, run_number, config_dict = args
    
    try:
        # Initialize pygame for this process (required for each worker)
        import pygame
        pygame.init()
        pygame.font.init()
        
        # Create dummy surfaces for headless operation
        global BIRD_IMGS, PIPE_IMG, BASE_IMG, BG_IMG
        BIRD_IMGS = [pygame.Surface((34, 24)) for _ in range(3)]
        PIPE_IMG = pygame.Surface((52, 320))
        BASE_IMG = pygame.Surface((336, 112))
        BG_IMG = pygame.Surface((600, 900))
        
        # Update class variables
        Pipes.PIPELOW = PIPE_IMG
        Pipes.PIPEHIGH = pygame.transform.rotate(PIPE_IMG, 180)
        Bird.IMGS = BIRD_IMGS
        Base.IMG = BASE_IMG
        Base.WIDTH = BASE_IMG.get_width()
        
        # Run the experiment
        local_dir = os.path.dirname(__file__)
        config_path = os.path.join(local_dir, 'config-feedforward.txt')
        
        result = run_experiment_core(window_size, pipe_distance, config_path, config_dict)
        return {
            'window_size': window_size,
            'pipe_distance': pipe_distance,
            'run_number': run_number,
            'results': result,
            'success': True,
            'error': None
        }
    except Exception as e:
        return {
            'window_size': window_size,
            'pipe_distance': pipe_distance,
            'run_number': run_number,
            'results': None,
            'success': False,
            'error': str(e)
        }

def run_experiment_core(window_size, pipe_distance, config_file, config_dict):
    """Core experiment logic separated for multiprocessing"""
    
    # Set environment parameters
    Pipes.WINDOW = window_size
    Pipes.PIPE_DISTANCE = pipe_distance
    
    # Load NEAT config
    config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction,
                                neat.DefaultSpeciesSet, neat.DefaultStagnation,
                                config_file)
    
    # Create tracker for this experiment
    tracker = ResearchTracker(config_dict['target_scores'], config_dict['max_generations'])
    
    # Reset game state
    Game.score = 0
    Game.max_score = 0
    Game.generation_scores = []
    
    # Create population
    p = neat.Population(config)
    
    class CustomReporter(neat.reporting.BaseReporter):
        def __init__(self, tracker, config_dict, window_size, pipe_distance):
            self.tracker = tracker
            self.config_dict = config_dict
            self.window_size = window_size
            self.pipe_distance = pipe_distance
            self.generation_counter = 0
            
        def post_evaluate(self, config, population, species, best_genome):
            self.generation_counter += 1
            max_score = max(Game.generation_scores) if Game.generation_scores else 0
            self.tracker.update(self.generation_counter, max_score)
            
            # Only print if not in multiprocessing mode to avoid output chaos
            if self.config_dict.get('print_progress', True) and not self.config_dict.get('use_multiprocessing', False):
                print(f"Gen {self.generation_counter:3d}: Max Score = {max_score:3d}, "
                      f"Window = {self.window_size}, Pipe Distance = {self.pipe_distance}")
            
            Game.generation_scores = []
            return self.tracker.finished
    
    # Add custom reporter
    custom_reporter = CustomReporter(tracker, config_dict, window_size, pipe_distance)
    p.add_reporter(custom_reporter)
    
    # Run evolution with custom evaluation
    def eval_wrapper(genomes, config):
        return eval_genomes(genomes, config, tracker, config_dict)
    
    # Run until targets reached or max generations
    generation = 0
    while not tracker.finished and generation < config_dict['max_generations']:
        p.run(eval_wrapper, 1)
        generation += 1
        if tracker.finished:
            break
    
    # Final update to ensure we have correct total_generations count
    if hasattr(custom_reporter, 'generation_counter'):
        tracker.current_generation = custom_reporter.generation_counter
    
    return tracker.get_results()

def run_experiment(window_size, pipe_distance, config_file):
    """Original run_experiment function for non-multiprocessing mode"""
    return run_experiment_core(window_size, pipe_distance, config_file, RESEARCH_CONFIG)

def save_results_to_csv(all_results, filename):
    """Save experimental results to CSV file"""
    
    fieldnames = ['window_size', 'pipe_distance', 'run_number', 'max_score_achieved', 
                  'total_generations', 'completed']
    
    # Add columns for each target score
    for score in RESEARCH_CONFIG['target_scores']:
        fieldnames.append(f'generations_to_{score}')
    
    with open(filename, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for result in all_results:
            row = {
                'window_size': result['window_size'],
                'pipe_distance': result['pipe_distance'],
                'run_number': result['run_number'],
                'max_score_achieved': result['results']['max_score_achieved'],
                'total_generations': result['results']['total_generations'],
                'completed': result['results']['completed']
            }
            
            # Add target score columns
            for score in RESEARCH_CONFIG['target_scores']:
                gens = result['results']['generations_to_reach'].get(score)
                row[f'generations_to_{score}'] = gens if gens is not None else 'N/A'
            
            writer.writerow(row)

def run_research_study():
    """Run the complete research study in sequential mode"""
    
    print("=" * 60)
    print("FLAPPY BIRD GENETIC LEARNING RESEARCH STUDY")
    print("=" * 60)
    print(f"Window sizes to test: {RESEARCH_CONFIG['window_sizes']}")
    print(f"Pipe distances to test: {RESEARCH_CONFIG['pipe_distances']}")
    print(f"Target scores: {RESEARCH_CONFIG['target_scores']}")
    print(f"Runs per configuration: {RESEARCH_CONFIG['runs_per_config']}")
    print(f"Max generations per run: {RESEARCH_CONFIG['max_generations']}")
    print(f"Show graphics: {RESEARCH_CONFIG['show_graphics']}")
    print(f"Running in SEQUENTIAL mode (multiprocessing disabled)")
    print(f"Results will be saved to: {RESEARCH_CONFIG['results_file']}")
    print("=" * 60)
    
    # Prepare experiment list
    experiments = []
    for window_size in RESEARCH_CONFIG['window_sizes']:
        for pipe_distance in RESEARCH_CONFIG['pipe_distances']:
            for run_num in range(RESEARCH_CONFIG['runs_per_config']):
                experiments.append((window_size, pipe_distance, run_num + 1))
    
    total_experiments = len(experiments)
    print(f"Total experiments to run: {total_experiments}")
    
    start_time = time.time()
    all_results = []
    
    # Sequential mode only
    print("\nRunning experiments sequentially...\n")
    
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, 'config-feedforward.txt')
    
    for i, (window_size, pipe_distance, run_num) in enumerate(experiments):
        experiment_count = i + 1
        percent = (experiment_count / total_experiments) * 100
        
        print(f"[{experiment_count:3d}/{total_experiments}] ({percent:5.1f}%) "
              f"Testing W={window_size}, D={pipe_distance}, R={run_num}")
        
        results = run_experiment(window_size, pipe_distance, config_path)
        
        all_results.append({
            'window_size': window_size,
            'pipe_distance': pipe_distance,
            'run_number': run_num,
            'results': results
        })
        
        print(f"    → Score: {results['max_score_achieved']}, "
              f"Gen: {results['total_generations']}, "
              f"Done: {results['completed']}")
    
    # Save results
    if all_results:
        save_results_to_csv(all_results, RESEARCH_CONFIG['results_file'])
    
    end_time = time.time()
    total_time = end_time - start_time
    
    print("\n" + "=" * 60)
    print("RESEARCH STUDY COMPLETED!")
    print(f"Successful experiments: {len(all_results)}/{total_experiments}")
    print(f"Total time: {total_time:.2f} seconds ({total_time/60:.2f} minutes)")
    print(f"Results saved to: {RESEARCH_CONFIG['results_file']}")
    print("=" * 60)
    
    return all_results

if __name__ == '__main__':
    results = run_research_study()