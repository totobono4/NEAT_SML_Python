from collections import deque
import sys
import os
import network
from pathlib import Path
import numpy as np
import utils.inputManager as manager
import utils.dataExtractor as extractor
import utils.learnOptions as options
from pyboy import PyBoy

PYGAME_SCREEN_WIDTH = 750
PYGAME_SCREEN_HEIGH = 750

root = __file__

reduceSize = 5

outputNames = {
	"a":0,
	"b":1,
	"up":2,
	"down":3,
	"left":4,
	"right":5
}

# Makes us able to import PyBoy from the directory below
SML_File = Path(os.path.dirname(os.path.realpath(__file__)))
sys.path.insert(0, str(SML_File) + "/..")

# Check if the ROM is given through argv
if len(sys.argv) > 1:
    SML_File = Path( sys.argv[1] )
else:
    print("Usage: python SML_IA.py [ROM file]")
    exit(1)

if not SML_File.exists:
	print('You have to put a Super Mario Land ROM that exists')
	exit(1)

quiet = "--quiet" in sys.argv
debugging = "--debug" in sys.argv
pyboy = PyBoy(SML_File.as_posix(), game_wrapper=True, window_type="headless" if quiet else "SDL2", debug=debugging)
pyboy.set_emulation_speed(0)
sml = pyboy.game_wrapper()
sml.start_game()

#pygame.init()
#screen = pygame.display.set_mode([PYGAME_SCREEN_HEIGH, PYGAME_SCREEN_WIDTH])

train_epoch = 300
current_progress = 0
max_progress = 0
start = sml.level_progress

def step(action):
	global current_progress
	buttonpresses = {
		"a":action[outputNames["a"]],
		"b":action[outputNames["b"]],
		"up":action[outputNames["up"]],
		"down":action[outputNames["down"]],
		"left":action[outputNames["left"]],
		"right":action[outputNames["right"]],
	}

	manager.sendInputs(buttonpresses, pyboy, options)
	pyboy.tick()

	reward = sml.level_progress - start
	reward += (sml.lives_left-2)*100 #losing lives is bad
	new_state = extractor.readLevelInfos(sml, options)["tiles"]
	return (new_state, reward)

def main():
	global current_progress
	max_epsilon = 1 # You can't explore more than 100% of the time
	min_epsilon = 0.01 # At a minimum, we'll always explore 1% of the time
	decay = 0.01

	current_progess = sml.level_progress
	mainmodel = network.getAgent((reduceSize*reduceSize,), len(outputNames))

	targetmodel = network.getAgent((reduceSize*reduceSize,), len(outputNames))
	targetmodel.set_weights(mainmodel.get_weights())

	replay_memory = deque(maxlen = 50_000)

	steps_to_update_target_model = 0

	for epoch in range(train_epoch):
		sml.reset_game()
		total_training_rewards = 0
		state = extractor.readLevelInfos(sml, options)["tiles"]
		while not sml.game_over():
			manager.resetInputs(pyboy)
			steps_to_update_target_model += 1
			action = network.getSolution(mainmodel, state, list(outputNames.values()))
			new_state, reward = step(action)
			replay_memory.append([state, action, reward, new_state])

			if steps_to_update_target_model % 4 == 0 or (sml.game_over() and sml.lives_left > 0):
				network.train(replay_memory, mainmodel, targetmodel)

			state = new_state
			total_training_rewards += reward
		if sml.lives_left > 0:
			print('Total training rewards: {} after n steps = {} with final reward = {}'.format(total_training_rewards, epoch, reward))
			total_training_rewards += 1

			if steps_to_update_target_model >= 100:
				print('Copying main network weights to the target network weights')
				targetmodel.set_weights(mainmodel.get_weights())
				steps_to_update_target_model = 0
			break

		network.epsilon = min_epsilon + (max_epsilon - min_epsilon) * np.exp(-decay * epoch)

if __name__ == "__main__":
	main()
