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

	colors_filter = {0: (255,255,255), 1:(0,0,255), 2:(255,0,0), 3:(0,0,0)}

	display_width = display_heigh = reduceSize

	for y in range(display_heigh):
		for x in range(display_width):
			rawvalue = tilesvector[(y*reduceSize)+x]
			nuance = colors_filter[rawvalue]
			posx = math.trunc(PYGAME_SCREEN_WIDTH / (display_width) * x / 4)
			posy = math.trunc(PYGAME_SCREEN_HEIGH / (display_heigh) * y / 4)
			sizex = math.trunc(PYGAME_SCREEN_WIDTH / (display_width) / 4)
			sizey = math.trunc(PYGAME_SCREEN_HEIGH / (display_heigh) / 4)
			pygame.draw.rect(
				screen,
				pygame.Color(nuance),
				pygame.Rect(posx, posy, sizex, sizey)
			)

	buttonIndex = 0
	for button in outs:
		nuance = 0
		if outs[button] > 0:
			nuance = 255
		posx = math.trunc(PYGAME_SCREEN_WIDTH / (display_width) * display_width + 400)
		posy = math.trunc(PYGAME_SCREEN_HEIGH / (display_heigh) * buttonIndex + 4)
		sizex = math.trunc(PYGAME_SCREEN_WIDTH / (display_width) / 4)
		sizey = math.trunc(PYGAME_SCREEN_HEIGH / (display_heigh) / 4)
		buttonIndex += 1
		font = pygame.font.SysFont('didot.ttc', math.trunc(sizex*3/4))
		img = font.render(button, False, (255, 255, 255))
		screen.blit(img, (posx, posy, sizex, sizey))
		pygame.draw.rect(
			screen,
			pygame.Color((nuance, nuance, nuance)),
			pygame.Rect(posx+10, posy, sizex, sizey)
		)

	for y in range(display_heigh):
		for x in range(display_width):
			rawvalue = tilesvector[(y*reduceSize)+x]
			nuance = colors_filter[rawvalue]
			posx = math.trunc(PYGAME_SCREEN_WIDTH / (display_width) * x / 4 + PYGAME_SCREEN_WIDTH / (display_width)/4*1/10)
			posy = math.trunc(PYGAME_SCREEN_HEIGH / (display_heigh) * y / 4 + PYGAME_SCREEN_WIDTH / (display_width)/4*1/10 + PYGAME_SCREEN_WIDTH*2 / 4)
			sizex = math.trunc(PYGAME_SCREEN_WIDTH / (display_width) / 4*8/10)
			sizey = math.trunc(PYGAME_SCREEN_HEIGH / (display_heigh) / 4*8/10)
			posxin = math.trunc(posx + PYGAME_SCREEN_WIDTH / (display_width)/4*3/20)
			posyin = math.trunc(posy + PYGAME_SCREEN_WIDTH / (display_width)/4*3/20)
			sizexin = math.trunc(sizex*9/10)
			sizeyin = math.trunc(sizey*9/10)
			pygame.draw.rect(
				screen,
				pygame.Color((0, 0, 0)),
				pygame.Rect(posxin, posyin, sizexin, sizeyin)
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
	ntiles = [0 for _ in range(reduceSize*reduceSize)]
	pos = getMarioPos(tiles)
	if pos is None:
		return None
	xmin = pos[0]-reduceSize//2
	xmax = pos[0]+reduceSize//2
	ymin = pos[1]-reduceSize//2
	ymax = pos[1]+reduceSize//2
	if xmin < 0:
		xmin = 0
	if xmax >= len(tiles[0]):
		xmax = len(tiles[0])-1
	if ymin < 0:
		ymin = 0
	if ymax >= len(tiles):
		ymax = len(tiles)-1
	for y in range(ymin, ymax+1):
		for x in range(xmin, xmax+1):
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
	if manipulations["a"]>0:
		pyboy.send_input(WindowEvent.PRESS_BUTTON_A)
	if manipulations["b"]>0:
		pyboy.send_input(WindowEvent.PRESS_BUTTON_B)
	if manipulations["up"]>0:
		pyboy.send_input(WindowEvent.PRESS_ARROW_UP)
	if manipulations["down"]>0:
		pyboy.send_input(WindowEvent.PRESS_ARROW_DOWN)
	if manipulations["left"]>0:
		pyboy.send_input(WindowEvent.PRESS_ARROW_LEFT)
	if manipulations["right"]>0:
		pyboy.send_input(WindowEvent.PRESS_ARROW_RIGHT)

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
