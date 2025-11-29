# Research Study Configuration File
# Modify these parameters to customize your research experiment

# Environment Variables to Test
# WINDOW_SIZES = [150, 200, 250, 300, 350]  Distance between upper and lower pipes
WINDOW_SIZES = [150]
PIPE_DISTANCES = [300, 400, 500, 600, 700]  # Distance between consecutive pipes

# Target Scores to Track
TARGET_SCORES = [10, 20, 50, 100, 200]

# Training Parameters
MAX_GENERATIONS = 50  # Maximum generations per experiment
RUNS_PER_CONFIG = 1    # Number of runs per configuration (for statistical significance)

# NEAT Parameters (you can also modify config-feedforward.txt)
POPULATION_SIZE = 50   # Size of each generation

# Performance Settings
SHOW_GRAPHICS = False  # Set to True to see the birds learning (much slower)
PRINT_PROGRESS = True  # Print progress updates during training

# Multiprocessing Settings
USE_MULTIPROCESSING = True    # Enable parallel processing (automatically disabled if SHOW_GRAPHICS=True)
NUM_PROCESSES = None          # Number of processes (None = auto-detect CPU count - 1)

# Results Settings
RESULTS_FILENAME = None  # If None, auto-generates filename with timestamp

# Advanced Settings
FRAME_LIMIT = 10000    # Max frames per generation (prevents infinite loops)
FITNESS_REWARD_ALIVE = 0.1     # Reward for staying alive each frame
FITNESS_REWARD_PIPE = 5        # Reward for passing through a pipe
FITNESS_PENALTY_COLLISION = 1  # Penalty for collision