import socket
import time
import agentpy as ap
import numpy as np
import random

"""
Part 1. Simulation Code
"""

"""
Class to represent the agent that will be moving through the streets
"""
class StreetAgent(ap.Agent):

  """
  Getting the parameters and setting initial values
  """
  def setup(self):
    # These are the possible actions
    self.actions = {"up": (-1, 0), "down": (1, 0), "right": (0, 1), "left": (0, -1)}

    # Learning parameters
    self.epsilon = self.p.epsilon
    self.train_episodes = self.p.train_episodes
    self.alpha = self.p.alpha
    self.gamma = self.p.gamma

    self.goal = self.p.goal
    self.grid = self.model.grid

    self.reward = 0

    # The agent keeps track of its own Q table while training and executing
    self.Q = {}
    for i in range(self.grid.shape[0]):
      for j in range(self.grid.shape[1]):
        self.Q[(i, j)] = {action: 0 for action in self.actions}

  """
  Function to get the current position (or state) of the agent
  """
  def get_position(self):
    return self.grid.positions[self]

  """
  Function that runs at each step of training and simulation
  """
  def execute(self):
    # Choose the next action and perform it
    action = self.choose_action(self.get_position())
    self.grid.move_by(self, self.actions[action])
    self.reward += self.grid.get_reward(self.get_position())
    return action

  """
  Function that executes a specified number of training episodes
  """
  def train(self, episodes):
    print("Training...")
    for i in range(episodes):
      state = self.p.start

      # Keep going until the goal is found
      while state != self.p.goal:
        action = self.execute()
        new_state = self.get_position()
        reward = self.grid.get_reward(new_state)
        self.update_Q(state, action, reward, new_state) # Update the q table accordingly
        state = new_state

      # Reset grid state
      self.grid.move_to(self, self.p.start)
      self.grid.setup()

    print("Finished training")

  """
  Function to choose an action depending on Q values and epsilon
  """
  def choose_action(self, state):
    if random.uniform(0, 1) < self.epsilon:
      return random.choice(list(self.actions.keys()))
    else:
      return max(self.Q[state], key=self.Q[state].get)

  """
  Function that runs the Q-learning formula after each training step
  """
  def update_Q(self, state, action, reward, new_state):
    max_Q_new_state = max(self.Q[new_state].values())
    self.Q[state][action] = self.Q[state][action] + self.alpha * (reward + self.gamma * max_Q_new_state - self.Q[state][action])

"""
Class to represent the grid of reward values in the streets
"""
class StreetGrid(ap.Grid):

  """
  Setup function to copy the street matrix
  """
  def setup(self):
    self.streets = np.copy(self.p.streets)

  """
  Function to get the reward (or value) at a specific position
  """
  def get_reward(self, pos):
    reward = self.p.streets[pos]

    if pos == self.p.goal: # The reward for being in the goal is special
      return self.p.goal_value
    elif reward < 0: # Dont allow the agent to go through closed roads (-1) or buildings (-10)
      return -1000
    else:
      return -self.p.streets[pos] # Negative value because it represents cost

"""
Class to represent the full simulation model that holds the agents and environments
"""
class StreetModel(ap.Model):

  """
  Setup method to create agent and environments, as well as run the agent training
  """
  def setup(self):
    # Create grid and agent
    self.grid = StreetGrid(self, shape=self.p.streets.shape)
    self.agent = StreetAgent(self)
    self.grid.add_agents([self.agent], positions=[self.p.start])

    # Train agent and reset agent state
    self.agent.train(self.p.train_episodes)
    self.agent.reward = 0

    # Make sure the final agent doesnt take any random paths
    self.agent.epsilon = 0

  """
  Function that runs each step of the simulation, executes the agents action
  """
  def step(self):
    self.agent.execute()

    # Also record the current position in order to stream it later to Unity
    self.record('position', self.agent.get_position)

  """
  Function that runs before the step function, checks if the agent made it to the goal
  """
  def update(self):
    if self.agent.get_position() == self.p.goal:
      print("Ending...")
      self.stop()

  """
  Function that runs just after the simulation ends, reports the final Q table in case of debugging
  """
  def end(self):
    self.report('Q-Table', self.agent.Q)

# Load street map from file
streets = np.load("streets-2.npy")

parameters = {
    "streets": streets,
    "train_episodes": 1000,
    "alpha": 1,
    "epsilon": 0.4,
    "gamma": 1,
    "start": (0, 6),
    "goal": (21, 18),
    "goal_value": 1000,
    "steps": 100,
}

# Run the simulation
model = StreetModel(parameters)
print("Running")
results = model.run(display=False)

# Get the resulting movements
movements = list(results.arrange_variables()['position'])



"""
Part 2. Socket code
"""

# Setting up the connection
print("\n\nCreating socket")
s=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind(('127.0.0.1', 1101))
print("Waiting for Unity to connect...")
s.listen()

while True:
    # Accepting a client
    conn, addr = s.accept()

    # Ask the client if they're ready for the instructions
    conn.send(b"R?")
    data = conn.recv(4096).decode("ascii")

    # Confirm they are ready by receiving an R (Ready)
    if data == "R":
      # Sending each position resulting from the simulation one by one
      # Protocol format: M {X} {Y}
      # M stands for movement
      for movement in movements:
        conn.send(f"M {movement[1]} {movement[0]}".encode())
        print(f"Sending {movement}")
        time.sleep(0.5)
      conn.send(b"E")
      break

print("Finished")
