import math
import sys
import os
from pyboy import PyBoy, WindowEvent
import neat
import copy
import visualize
from pathlib import Path
from graphviz import Digraph
import pygame
import numpy

PYGAME_SCREEN_WIDTH = 750
PYGAME_SCREEN_HEIGH = 750

root = __file__

empty = 0
mario = 1
enemy = 2
platform = 3

reduceSize = 5
minButtonPress = 1

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

pygame.init()
screen = pygame.display.set_mode([PYGAME_SCREEN_HEIGH, PYGAME_SCREEN_WIDTH])

debut = open("./debut.save", "wb")
pyboy.save_state(debut)
debut.close()

#def displayNetwork():

def displayNetwork(inputs, hiddens, outs, tilesvector):
	screen.fill((0,0,0))

	display_width = display_heigh = reduceSize

	tiling = 2

	tilingoffsetx = PYGAME_SCREEN_WIDTH/tiling
	tilingoffsety = PYGAME_SCREEN_HEIGH/tiling

	tilingx = tilingoffsetx/display_width
	tilingy = tilingoffsety/display_heigh

	colors_filter = {0: (255,255,255), 1:(0,0,255), 2:(255,0,0), 3:(0,0,0)}
	controller = {
		'offset': (0,1),
		'overlay': (
			# controller outline
			((0.1, 0.1, 12.8, 6.8),(200,200,200)),
			((1.1, 1.1, 10.8, 4.8),(50,50,50)),
			# cross outline
			((2.9, 1.9, 1, 3),(150,150,150)),
			((1.9, 2.9, 3, 1),(150,150,150)),
			((3, 2, 1, 3),(100,100,100)),
			((2, 3, 3, 1),(100,100,100)),
			# buttons outline
			((7.8,3.8,1,1),(255,255,255)),
			((7.9,3.9,1,1),(100,100,100)),
			((9.8,3.8,1,1),(255,255,255)),
			((9.9,3.9,1,1),(100,100,100))
		),
		'left': ((2.2,3.2,.7,.7),((200,200,200),(50,50,50))),
		'up': ((3.2,2.2,.7,.7),((200,200,200),(50,50,50))),
		'right': ((4.2,3.2,.7,.7),((200,200,200),(50,50,50))),
		'down': ((3.2,4.2,.7,.7),((200,200,200),(50,50,50))),
		'a': ((8.1,4.1,.7,.7),((255,0,0),(150,0,0))),
		'b': ((10.1,4.1,.7,.7),((255,0,0),(150,0,0)))
	}

	for y in range(display_heigh):
		for x in range(display_width):
			rawvalue = tilesvector[(y*reduceSize)+x]
			nuance = colors_filter[rawvalue]
			posx = math.trunc(tilingoffsetx*0 + tilingx*(x+1/20))
			posy = math.trunc(tilingoffsety*0 + tilingy*(y+1/20))
			sizex = math.trunc(tilingx*(9/10))
			sizey = math.trunc(tilingy*(9/10))
			pygame.draw.rect(
				screen,
				pygame.Color(nuance),
				pygame.Rect(posx, posy, sizex, sizey)
			)
	
	for miscalenious in controller['overlay']:
		pygame.draw.rect(
			screen,
			miscalenious[1],
			(
				tilingoffsetx*controller['offset'][0] + tilingx*(miscalenious[0][0]),
				tilingoffsety*controller['offset'][1] + tilingy*(miscalenious[0][1]),
				tilingx*(miscalenious[0][2]),
				tilingy*(miscalenious[0][3])
			)
		)

	for button in outs:
		nuance = 0
		if outs[button] >= minButtonPress:
			nuance = 1
		posx = math.trunc(tilingoffsetx*controller['offset'][0] + tilingx*controller[button][0][0])
		posy = math.trunc(tilingoffsety*controller['offset'][1] + tilingy*controller[button][0][1])
		sizex = math.trunc(tilingx*controller[button][0][2])
		sizey = math.trunc(tilingx*controller[button][0][3])

		pygame.draw.rect(
			screen,
			pygame.Color(controller[button][1][nuance]),
			pygame.Rect(posx, posy, sizex, sizey)
		)
		

	pygame.display.flip()

def step(genomes, config):
	genenb = 0
	for genome_id, genome in genomes:
		print("Gene : "+str(genenb)+"/"+str(config.pop_size), end="\r")
		genenb += 1
		info = readLevelInfos()
		genome.fitness = 0 
		net = neat.nn.FeedForwardNetwork.create(genome, config)
		stuckFrames = 0
		maxStuckFrames = 150
		maxFitness = genome.fitness
		
		while not info["dead"]:
			if stuckFrames >= maxStuckFrames:
				break
			if info["tiles"] is not None:
				out = net.activate(info["tiles"])
				manipulations = {
					"a":out[0],
					"b":out[1],
					"up":out[2],
					"down":out[3],
					"left":out[4],
					"right":out[5]
				} #outputs
				sendInputs(manipulations)
				pyboy.tick()
				displayNetwork(config.genome_config.input_keys, genomes, manipulations, info["tiles"])
				info = readLevelInfos()
				genome.fitness = 0 if sml.level_progress is None else sml.level_progress
				if genome.fitness <= maxFitness:
					stuckFrames += 1
				else:
					maxFitness = genome.fitness
					stuckFrames = 0
			else:
				break
		
		debut = open("./debut.save", "rb")
		pyboy.load_state(debut)
		pyboy.tick()
		debut.close()

def getMarioPos(tiles):
	for y in range(len(tiles)):
		for x in range(len(tiles[y])):
			tile = tiles[y][x]
			if tile in range(0, 26): #mario
				return (x, y)
	return None

def normalise(tiles):
	pos = getMarioPos(tiles)
	if pos is None:
		return None
	offset = 1
	if reduceSize%2 == 0:
		offset = 0
	xmin = pos[0]-reduceSize//2
	xmax = pos[0]+reduceSize//2+offset
	ymin = pos[1]-reduceSize//2
	ymax = pos[1]+reduceSize//2+offset
	if xmin < 0:
		xmin = 0
	if xmax >= len(tiles[0]):
		xmax = len(tiles[0])-1
	if ymin < 0:
		ymin = 0
	if ymax >= len(tiles):
		ymax = len(tiles)-1
	return transform(xmin, xmax, ymin, ymax, tiles)

def transform(xmin, xmax, ymin, ymax, tiles):
	ntiles = [0 for _ in range(reduceSize*reduceSize)]
	for y in range(ymin, ymax):
		for x in range(xmin, xmax):
			i = (reduceSize)*(y-ymin)+(x-xmin)
			tile = tiles[y][x]
			if tile in range(0, 26): #mario
				ntiles[i] = mario
			elif tile in range(351, 400) or tile in range(129, 144) or tile == 239:
				ntiles[i] = platform
			elif tile in range(144, 211):
				ntiles[i] = enemy
			else:
				ntiles[i] = empty
	return ntiles

def readLevelInfos(): 
	area = sml.game_area()
	tiles = normalise(area)
	levelInfo = {
        "dead":sml.lives_left <= 1, 
        "tiles":tiles
    }
	return levelInfo

def sendInputs(manipulations):
	if manipulations["a"]>=minButtonPress:
		pyboy.send_input(WindowEvent.PRESS_BUTTON_A)
	else:		
		pyboy.send_input(WindowEvent.RELEASE_BUTTON_A)
	if manipulations["b"]>=minButtonPress:
		pyboy.send_input(WindowEvent.PRESS_BUTTON_B)
	else:		
		pyboy.send_input(WindowEvent.RELEASE_BUTTON_B)
	if manipulations["up"]>=minButtonPress:
		pyboy.send_input(WindowEvent.PRESS_ARROW_UP)
	else:		
		pyboy.send_input(WindowEvent.RELEASE_ARROW_UP)
	if manipulations["down"]>=minButtonPress:
		pyboy.send_input(WindowEvent.PRESS_ARROW_DOWN)
	else:		
		pyboy.send_input(WindowEvent.RELEASE_ARROW_DOWN)
	if manipulations["left"]>=minButtonPress:
		pyboy.send_input(WindowEvent.PRESS_ARROW_LEFT)
	else:		
		pyboy.send_input(WindowEvent.RELEASE_ARROW_LEFT)
	if manipulations["right"]>=minButtonPress:
		pyboy.send_input(WindowEvent.PRESS_ARROW_RIGHT)
	else:		
		pyboy.send_input(WindowEvent.RELEASE_ARROW_RIGHT)

def run(config_path):
	global reduceSize
	config = neat.Config(neat.DefaultGenome, neat.DefaultReproduction,
		neat.DefaultSpeciesSet, neat.DefaultStagnation,
		config_path)
	reduceSize = int(math.sqrt(config.genome_config.num_inputs))

	pop = neat.Population(config)

    # Add a stdout reporter to show progress in the terminal.
	pop.add_reporter(neat.StdOutReporter(True))
	stats = neat.StatisticsReporter()
	pop.add_reporter(stats)
	pop.add_reporter(neat.Checkpointer(5, filename_prefix='./checkpoints/neat-checkpoint-'))

	winner = pop.run(step)

    # Show output of the most fit genome against training data.
	print('\nOutput:')

	node_names = {0: 'A', 1: 'B', 2:'UP', 3:'DOWN', 4:'LEFT', 5:'RIGHT'}
	tiles = readLevelInfos()["tiles"]
	for i in range(len(tiles)):
		node_names[-len(tiles)+i] = "tile_"+str(i)
	visualize.draw_net(config, winner, True, node_names=node_names)
	visualize.plot_stats(stats, ylog=False, view=True)
	visualize.plot_species(stats, view=True)

	p = neat.Checkpointer.restore_checkpoint('./checkpoints/neat-checkpoint-4')
	pyboy.set_emulation_speed(0)

	p.run(step, 10)

if __name__ == '__main__':
	dirname = os.path.dirname(__file__)
	config_path = os.path.join(dirname, "neat_config.txt")
	run(config_path)

	pygame.quit()
