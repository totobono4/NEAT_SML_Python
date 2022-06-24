import sys
import os
import network
from pathlib import Path
import numpy as np
from pyboy import PyBoy
import io

sys.path.append(str(Path(Path().cwd().parent)))
import utils.learnOptions as options
import utils.dataExtractor as extractor
import utils.inputManager as manager

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

episodes = 300
batch = 1000
observeTime = 400*35 #lenght of a game

def executAction(act):	
	buttonpresses = { #transforms raw network data into game controll data
		"a":outputNames["a"] == act,
		"b":outputNames["b"] == act,
		"up":outputNames["up"] == act,
		"down":outputNames["down"] == act,
		"left":outputNames["left"] == act,
		"right":outputNames["right"] == act,
	}
	manager.sendInputs(buttonpresses, pyboy, options) #press on buttons
	pyboy.tick()

#steps in the game
def step(act, previous):
	executAction(act)
	return (sml.level_progress - previous)*20 #compute reward

rewindstate = io.BytesIO()

def createState(model : network.MarioAi):
	currentState = extractor.readLevelInfos(sml, options)["tiles"]
	states = currentState
	rewindsize = 0
	tonextstate = currentState
	rewindstate.seek(0)
	pyboy.save_state(rewindstate)
	for _ in range(1, model.window_size):
		executAction(model.getSolution(currentState))
		next = extractor.readLevelInfos(sml, options)["tiles"]
		if next is not None:
			states += next
			currentState = next
			rewindsize += 1
		else:
			return None
	
	rewindstate.seek(0)
	pyboy.load_state(rewindstate)
	
	executAction(model.getSolution(tonextstate))
	return np.array([states])

def main():
	agent = network.MarioAi(reduceSize*reduceSize, list(outputNames.values()), state_creator=createState) #generate agent with project scale
	
	agent.agent.summary()
	for i in range(100000): #trains the agent several times
		agent.train(sml, step)
		



if __name__ == "__main__":
	main()
