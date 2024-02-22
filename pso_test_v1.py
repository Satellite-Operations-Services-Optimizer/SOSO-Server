# Import necessary libraries
import os
import json
import random
import numpy as np
from datetime import datetime, timedelta
from skyfield.api import load, Topos
from skyfield.sgp4lib import EarthSatellite
from scheduler_service.schedulers.deterministic.scheduler_algorithm_rafael import *

## Step 1: Define the Particle Class:
# This represents the order particles used in the system
# Each particle has a position, velocity, and fitness score
# Assume 24-hour batch scheduling method based on orders.

class Particle:
    def __init__(self, image_orders, maintenance_orders, outage_orders):
        self.image_orders = image_orders
        self.maintenance_orders = maintenance_orders
        self.outage_orders = outage_orders
        self.position = self.initialize_position(image_orders, maintenance_orders, outage_orders)
        self.velocity = self.initialize_velocity()
        self.best_position = self.position.copy()
        self.fitness = float('-inf') # To be calculated based on the objective function
    
    def initialize_position(self, image_orders, maintenance_orders, outage_orders):
        # Combine all orders and shuffle them to create an initial position
        all_orders = image_orders + maintenance_orders + outage_orders
        random.shuffle(all_orders)
        return all_orders
    
    def initialize_velocity(self):
        # Initialize velocity with random values
        return [random.uniform(-1, 1) for _ in range(len(self.position))]

    def calculate_fitness(self, scheduler):
        # Calculate the fitness of the particle using the deterministic scheduler
        # The scheduler should return a fitness value based on the quality of the schedule
        return scheduler.schedule(self.position)
    
# Load orders from directories
def load_orders(directory):
    orders = []
    for filename in os.listdir(directory):
        with open(os.path.join(directory, filename), 'r') as f:
            orders.append(json.load(f))
    return orders

image_orders = load_orders('database_scripts/populate_scripts/sample_image_orders')
maintenance_orders = load_orders('database_scripts/populate_scripts/sample_maintenance_orders')
outage_orders = load_orders('database_scripts/populate_scripts/sample_outage_orders')

# PSO parameters
num_particles = 10
max_iterations = 50
c1, c2 = 1.5, 1.5  # Cognitive and social learning factors
w = 0.7  # Inertia weight

# Initialize particles
particles = [Particle(image_orders, maintenance_orders, outage_orders) for _ in range(num_particles)]

## Step 2: Define the Objective Function
# This should represent the function that evaluates the:
# 1. Fitness of each particle based on priority of orders.
# 2. A penalty for overlapping order events between orders/conflicts.
# 3. Speed at which the schedules are generated based on the order particles position.

# Define the objective function
def objective_function(particle, ts):
    # Initialize penalty
    penalty = 0
    # Initialize scheduler system
    scheduler_system = SchedulerSystem(ts)
    # Process each order in the particle's position
    for order in particle.position:
        # Check for order type and process accordingly
        if 'ImageType' in order:
            # Process image order
            scheduler_system.process_image_order(order)
        elif 'Activity' in order:
            # Process maintenance order
            scheduler_system.process_maintenance_order(order)
        else:
            # Process outage order
            scheduler_system.process_outage_order(order)
    # Calculate fitness based on the quality of the schedule
    fitness = scheduler_system.evaluate_schedule_quality()
    # Apply penalties for any overlaps or conflicts
    penalty += scheduler_system.calculate_overlaps()
    # Return the fitness score (higher is better) minus any penalties
    return fitness - penalty
    
## Step 3: Update the Particle Position and Velocity
# The order particles position and velocities will be based on the time values given in 
# the .json schema for the outage, maintenance, and imaging orders.
# Therefore, if the order particle position and velocity can be assumed to have a local best 
# when most orders can be filled from each order type (most outage OR most maintenance OR most imaging) and global best 
# when most if not all orders can be filled for each order type.

# Define the SchedulerSystem class based on the deterministic file
class SchedulerSystem:
    def __init__(self, ts):
        self.ts = ts
        self.ground_stations = []  # List of ground_station objects
        self.satellites = []  # List of satelite objects
        # Initialize ground stations and satellites here based on the paste.txt file
    
    def process_image_order(self, order):
        # Process image order logic
        pass
    
    def process_maintenance_order(self, order):
        # Process maintenance order logic
        pass
    
    def process_outage_order(self, order):
        # Process outage order logic
        pass
    
    def evaluate_schedule_quality(self):
        # Evaluate the quality of the schedule
        # This could be based on the number of successfully scheduled orders
        pass
    
    def calculate_overlaps(self):
        # Calculate any overlaps or conflicts between orders
        pass


## Step 4: Schedule Evaluation
# In each iteration, the order particles position should be improved to reach the global best 
# where each order type is filled or can be fit into the schedule based on the deterministic algorithm 
# satellite and ground stations communication code.

# Main PSO loop
for iteration in range(max_iterations):
    for particle in particles:
        # Evaluate fitness
        particle.fitness = objective_function(particle, load.timescale())
        # Update personal best
        if particle.fitness > particle.best_fitness:
            particle.best_position = particle.position.copy()
            particle.best_fitness = particle.fitness
    # Update global best
    global_best_particle = max(particles, key=lambda p: p.fitness)
    global_best_position = global_best_particle.position

    # Update particle positions and velocities
    for particle in particles:
        inertia = w * np.array(particle.velocity)
        cognitive = c1 * np.random.rand() * (np.array(particle.best_position) - np.array(particle.position))
        social = c2 * np.random.rand() * (np.array(global_best_position) - np.array(particle.position))
        particle.velocity = list(inertia + cognitive + social)
        particle.position = list(np.array(particle.position) + np.array(particle.velocity))

## Step 5: Convergence Criterion
# In this case, the convergence criterion is that all orders have been processed and determined to be 
# suitable for a schedule or not.

# Retrieve the best schedule
best_particle = max(particles, key=lambda p: p.fitness)
best_schedule = best_particle.position

# Print or use the best schedule as needed
print("Best Schedule:", best_schedule)

## Performance Check
# Code to see failed orders, overlapped orders, and time it takes to generate schedules.
sys = System()
sys.run(start_time, end_time)

