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
import learnOptions as options

PYGAME_SCREEN_WIDTH = 750
PYGAME_SCREEN_HEIGH = 750

root = __file__

reduceSize = 5

def setReduceSize(value):
    global reduceSize
    reduceSize = value
    print(reduceSize)

def getReduceSize():
    global reduceSize
    return reduceSize

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

pygame.init()
screen = pygame.display.set_mode([PYGAME_SCREEN_HEIGH, PYGAME_SCREEN_WIDTH])

debut = open("./debut.save", "wb")
pyboy.save_state(debut)
debut.close()

#def displayNetwork():

def displayNetwork(inputs, outputs, hiddens, connections, outs, tilesvector):
	screen.fill((0,0,0))

	display_width = display_heigh = getReduceSize()

	tiling = 4

	tilingoffsetx = PYGAME_SCREEN_WIDTH/tiling
	tilingoffsety = PYGAME_SCREEN_HEIGH/tiling

	tilingx = tilingoffsetx/display_width
	tilingy = tilingoffsety/display_heigh

	colors_filter = {
		options.empty: (255,255,255),
		options.mario:(0,0,255),
		options.enemy:(255,0,0),
		options.platform:(121,26,126),
		options.block:(244,255,0),
		options.coin:(241,194,50)
	}
	
	controller = {
		'offset': (1,0),
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
			((7.8,3.8,1,1),(150,150,150)),
			((7.9,3.9,1,1),(100,100,100)),
			((9.8,3.8,1,1),(150,150,150)),
			((9.9,3.9,1,1),(100,100,100))
		),
		'left': ((2.2,3.2,.7,.7),((200,200,200),(50,50,50))),
		'up': ((3.2,2.2,.7,.7),((200,200,200),(50,50,50))),
		'right': ((4.2,3.2,.7,.7),((200,200,200),(50,50,50))),
		'down': ((3.2,4.2,.7,.7),((200,200,200),(50,50,50))),
		'a': ((10.1,4.1,.7,.7),((255,0,0),(150,0,0))),
		'b': ((8.1,4.1,.7,.7),((255,0,0),(150,0,0)))
	}

	perceptrons = {}

	hiddenoffset = (0,2)
	hiddentiling = (4,1)
	for hidden in range(len(hiddens)):
		tilingwidth = display_width * hiddentiling[0]
		x = hidden % tilingwidth
		y = math.trunc(hidden / tilingwidth)
		nuance = (255,255,255)
		posx = math.trunc(tilingoffsetx*hiddenoffset[0] + tilingx*(x+1/20))
		posy = math.trunc(tilingoffsety*hiddenoffset[1] + tilingy*(y+1/20))
		sizex = math.trunc(tilingx*(9/10))
		sizey = math.trunc(tilingy*(9/10))

		pygame.draw.rect(
			screen,
			pygame.Color(nuance),
			pygame.Rect(posx, posy, sizex, sizey)
		)

		center = (posx + sizex/2, posy + sizey/2)
		perceptrons[list(hiddens)[hidden]] = center

	for y in range(display_heigh):
		for x in range(display_width):
			index2d = y*getReduceSize()+x
			rawvalue = tilesvector[index2d]
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

			center = (posx + sizex/2, posy + sizey/2)
			perceptrons[-(index2d+1)] = center
	
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
		if outs[button] >= options.minButtonPress:
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

		if button == 'a' or button == 'b':
			font = pygame.font.SysFont('didot.ttc', math.trunc(sizex*1))
			img = font.render(str.upper(str(button)), False, (255, 0, 0))
			screen.blit(img, (posx + tilingx/2, posy + tilingy, sizex, sizey))

		center = (posx + sizex/2, posy + sizey/2)
		perceptrons[outputNames[button]] = center

	for connection in connections:
		id1 = connection[0]
		id2 = connection[1]
		weight = connection[2]
		active = connection[3]
		pygame.draw.line(
			screen,
			(150,150,150) if not active else (0,255,0) if weight > 0 else (255,0,0),
			perceptrons[id1],
			perceptrons[id2],
			math.trunc(abs(weight)+1)*2 if active else 1)
	
	pygame.display.flip()

def buildGraph(inputs, outputs, genome):
	connections = []
	hidden = set()
	for connection in genome.connections:
		connectionobj = genome.connections[connection]
		connections.append((connectionobj.key[0], connectionobj.key[1], connectionobj.weight, connectionobj.enabled))
		if connectionobj.key[0] not in inputs and connectionobj.key[0] not in outputs:
			hidden.add(connectionobj.key[0])
		if connectionobj.key[1] not in inputs and connectionobj.key[1] not in outputs:
			hidden.add(connectionobj.key[1])
	return (connections, hidden)

def step(genomes, config):
	gen = 0
	for genome_id, genome in genomes:
		print("Gen : "+str(gen)+" : "+str(len(genomes)), end="\r")
		gen+=1
		info = readLevelInfos()
		resetInputs()
		genome.fitness = 0 
		net = neat.nn.FeedForwardNetwork.create(genome, config)
		stuckFrames = 0
		maxStuckFrames = 25
		maxFitness = genome.fitness
		
		while not info["dead"]:
			if stuckFrames >= maxStuckFrames:
				break
			if info["tiles"] is not None:
				out = net.activate([ x/6 for x in info["tiles"]])
				manipulations = {
					"a":out[outputNames["a"]],
					"b":out[outputNames["b"]],
					"up":out[outputNames["up"]],
					"down":out[outputNames["down"]],
					"left":out[outputNames["left"]],
					"right":out[outputNames["right"]]
				} #outputs
				sendInputs(manipulations)
				pyboy.tick()

				graph = buildGraph(config.genome_config.input_keys, config.genome_config.output_keys, genome)


				displayNetwork(config.genome_config.input_keys, config.genome_config.output_keys, graph[1], graph[0], manipulations, info["tiles"])
				info = readLevelInfos()
				genome.fitness = 0 if sml.level_progress is None else sml.level_progress
				if genome.fitness <= maxFitness:
					stuckFrames += 1
				else:
					maxFitness = genome.fitness
					stuckFrames = 0
			else:
				break
		if options.use_coins_in_fitness:
			genome.fitness += sml.coins*10
		if options.use_score_in_fitness:
			genome.fitness += sml.score/10
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
	if getReduceSize()%2 == 0:
		offset = 0
	xmin = pos[0]-getReduceSize()//2+1
	xmax = pos[0]+getReduceSize()//2+offset+1
	ymin = pos[1]-getReduceSize()//2+1
	ymax = pos[1]+getReduceSize()//2+offset+1
	if xmin < 0:
		xmax += abs(xmin)
		xmin = 0
	if xmax >= len(tiles[0]):
		xmin -= xmax-len(tiles[0])+1
		xmax = len(tiles[0])-1
	if ymin < 0:
		ymax += abs(ymin)
		ymin = 0
	if ymax >= len(tiles):
		ymin -= ymax-len(tiles)+1
		ymax = len(tiles)-1
	return transform(xmin, xmax, ymin, ymax, tiles)

def transform(xmin, xmax, ymin, ymax, tiles):
	ntiles = [0 for _ in range(getReduceSize()*getReduceSize())]
	for y in range(ymin, ymax):
		for x in range(xmin, xmax):
			i = (getReduceSize())*(y-ymin)+(x-xmin)
			tile = tiles[y][x]
			looking = True
			select = None
			while(looking):
				if select is None:
					for activator in options.activation:
						if options.activation[activator][2](tile):
							if not options.activation[activator][0]:
								select = options.activation[activator][1]
							else:
								select = activator
								looking = False
							break
					if select is None:
						select = options.empty
						looking = False
				else:
					if select not in options.activation:
						looking = False
					elif options.activation[select][2](tile):
						if not options.activation[select][0]:
							select = options.activation[select][1]
						else:
							looking = False
					else:
						looking = False
			ntiles[i] = select
	return ntiles

def readLevelInfos(): 
	area = sml.game_area()
	tiles = normalise(area)
	levelInfo = {
        "dead":sml.lives_left <= 1, 
        "tiles":tiles
    }
	return levelInfo

def resetInputs():
	pyboy.send_input(WindowEvent.RELEASE_BUTTON_A)
	pyboy.send_input(WindowEvent.RELEASE_BUTTON_B)
	pyboy.send_input(WindowEvent.RELEASE_ARROW_UP)
	pyboy.send_input(WindowEvent.RELEASE_ARROW_DOWN)
	pyboy.send_input(WindowEvent.RELEASE_ARROW_LEFT)
	pyboy.send_input(WindowEvent.RELEASE_ARROW_RIGHT)


def sendInputs(manipulations):
	resetInputs()
	if manipulations["a"]>=options.minButtonPress:
		pyboy.send_input(WindowEvent.PRESS_BUTTON_A)
	if manipulations["b"]>=options.minButtonPress:
		pyboy.send_input(WindowEvent.PRESS_BUTTON_B)
	if manipulations["up"]>=options.minButtonPress:
		pyboy.send_input(WindowEvent.PRESS_ARROW_UP)
	if manipulations["down"]>=options.minButtonPress:
		pyboy.send_input(WindowEvent.PRESS_ARROW_DOWN)
	if manipulations["left"]>=options.minButtonPress:
		pyboy.send_input(WindowEvent.PRESS_ARROW_LEFT)
	if manipulations["right"]>=options.minButtonPress:
		pyboy.send_input(WindowEvent.PRESS_ARROW_RIGHT)

def run(config_path):
	config = neat.Config(neat.DefaultGenome, neat.DefaultReproduction,
		neat.DefaultSpeciesSet, neat.DefaultStagnation,
		config_path)
	setReduceSize(int(math.sqrt(config.genome_config.num_inputs)))

	pop = neat.Population(config)

    # Add a stdout reporter to show progress in the terminal.
	pop.add_reporter(neat.StdOutReporter(True))
	stats = neat.StatisticsReporter()
	pop.add_reporter(stats)
	pop.add_reporter(neat.Checkpointer(1, filename_prefix='./checkpoints/neat-checkpoint-'))

	winner = pop.run(step, 100)

    # Show output of the most fit genome against training data.
	print('\nOutput:')

	p = neat.Checkpointer.restore_checkpoint('./checkpoints/neat-checkpoint-1')
	pyboy.set_emulation_speed(0)

	p.run(step, 10)

if __name__ == '__main__':
	#while not pyboy.tick():
	#	pass
	#pyboy.stop()
	#print(sml)
	dirname = os.path.dirname(__file__)
	config_path = os.path.join(dirname, "neat_config.txt")
	run(config_path)

	pygame.quit()
