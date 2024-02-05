import json
import numpy as np
from datetime import timedelta
from scheduler_algorithm_rafael import *

# Load image orders
image_orders = []
for i in range(1, 51):
    with open(f'database_scripts/populate_scripts/sample_image_orders/Order_{i}.json') as f:
        image_orders.append(json.load(f))

# Load maintenance orders
maintenance_orders = []
for i in range(1, 30):
    try:
        with open(f'database_scripts/populate_scripts/sample_maintenance_orders/MemoryScrubmaintenance{i}.json') as f:
            maintenance_orders.append(json.load(f))
        with open(f'database_scripts/populate_scripts/sample_maintenance_orders/Orbitmaintenance{i}.json') as f:
            maintenance_orders.append(json.load(f))
        with open(f'database_scripts/populate_scripts/sample_maintenance_orders/OrbitParameterUpdatemaintenance{i}.json') as f:
            maintenance_orders.append(json.load(f))
        with open(f'database_scripts/populate_scripts/sample_maintenance_orders/PayloadDiagnosticActivitymaintenance{i}.json') as f:
            maintenance_orders.append(json.load(f))
    except FileNotFoundError:
         print("File not found, moving on to next file...")

# Load outage orders
# outage_orders = []
# for i in range(1, 6):
#     with open(f'SampleOrders/Outage_Order_{i}.json') as f:
#         outage_orders.append(json.load(f))

# Define particle structure
class Particle:
    def __init__(self, image_order_sequence):
        self.image_order_sequence = image_order_sequence
        self.maintenance_order = None
        self.outage_order = None
        self.fitness = 0  # To be defined based on the objective function

# Define PSO parameters
num_particles = 10
max_iterations = 50
c1, c2 = 1.5, 1.5  # Cognitive and social learning factors
w = 0.7  # Inertia weight

# Initialize particles
particles = [Particle(np.random.permutation(range(1, 51))) for _ in range(num_particles)]

# Define a function to evaluate the fitness of a particle
def evaluate(self):
    total_penalty = 0

    # Example criteria for evaluation
    for sat in self.Satelites:
        # Penalty for overlapping maintenance events
        for ev1 in sat.Events:
            if ev1["Type"] == "Maintainence":
                for ev2 in sat.Events:
                    if ev2["Type"] == "Maintainence" and ev1 != ev2:
                        if self.ev_overlap(ev1, ev2["Start"], ev2["End"]):
                            total_penalty += 1  # Increment penalty for overlapping maintenance events

        # Additional evaluation criteria can be added based on the specific requirements

    # Example: A lower penalty is better
    fitness_score = 1 / (1 + total_penalty)

    return fitness_score

# Main PSO loop
for iteration in range(max_iterations):
    for particle in particles:
        # Evaluate fitness
        particle.fitness = evaluate(particle)

    # Update personal best
    for particle in particles:
        if particle.fitness > evaluate(particle):
            particle.personal_best = particle.position.copy()
            particle.best_fitness = particle.fitness

    # Update global best
    global_best_particle = max(particles, key=lambda x: x.fitness)
    global_best_position = global_best_particle.position

    # Update particle positions
    for particle in particles:
        inertia = w * np.array(particle.position)
        cognitive = c1 * np.random.rand() * (np.array(particle.personal_best) - np.array(particle.position))
        social = c2 * np.random.rand() * (np.array(global_best_position) - np.array(particle.position))

        new_position = inertia + cognitive + social
        particle.position = list(new_position.astype(int))

# Retrieve the best schedule
best_particle = max(particles, key=lambda x: x.fitness)
best_schedule = best_particle.image_order_sequence

# Print or use the best schedule as needed
print("Best Schedule:", best_schedule)
