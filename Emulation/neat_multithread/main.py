import math
import sys
import os
from pyboy import PyBoy, WindowEvent
import neat
from pathlib import Path
from multiprocessing import Value
import pygame
import learnOptions as options

PYGAME_SCREEN_WIDTH = 350
PYGAME_SCREEN_HEIGH = 350

root = __file__

outputNames = {
	"a":0,
	"b":1,
	"up":2,
	"down":3,
	"left":4,
	"right":5
}

if __name__ != '__main__':
	pyboy = PyBoy(Path(sys.argv[1]).as_posix(), game_wrapper=True, window_type="SDL2", kwargs="--log-level ERROR")
	pyboy.set_emulation_speed(0)
	sml = pyboy.game_wrapper()

	sml.start_game()
	pygame.init()

	debut = open("./debut.save", "wb")
	pyboy.save_state(debut)
	debut.close()

	screen = pygame.display.set_mode([PYGAME_SCREEN_HEIGH, PYGAME_SCREEN_WIDTH])

def displayNetwork(screen, reduceSize, inputs, outputs, hiddens, connections, outs, tilesvector):
	screen.fill((0,0,0))

	display_width = display_heigh = reduceSize

	tiling = 2

	tilingoffsetx = PYGAME_SCREEN_WIDTH/tiling
	tilingoffsety = PYGAME_SCREEN_HEIGH/tiling

	tilingx = tilingoffsetx/display_width
	tilingy = tilingoffsety/display_heigh

	controller_tiling = tilingoffsety/7

	colors_filter = {
		options.empty: (255,255,255),
		options.mario:(0,0,255),
		options.enemy:(255,0,0),
		options.platform:(121,26,126),
		options.block:(244,255,0),
		options.coin:(241,194,50)
	}
	
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

	hiddenoffset = (1,0)
	hiddentiling = (1,1)
	for hidden in range(len(hiddens)):
		tilingwidth = display_width * hiddentiling[0]
		x = hidden % tilingwidth
		y = math.trunc(hidden / tilingwidth)
		nuance = (75,220,206)
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
			index2d = y*reduceSize+x
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
				tilingoffsetx*controller['offset'][0] + controller_tiling*(miscalenious[0][0]),
				tilingoffsety*controller['offset'][1] + controller_tiling*(miscalenious[0][1]),
				controller_tiling*(miscalenious[0][2]),
				controller_tiling*(miscalenious[0][3])
			)
		)

	for button in outs:
		nuance = 0
		if outs[button] >= options.minButtonPress:
			nuance = 1
		posx = math.trunc(tilingoffsetx*controller['offset'][0] + controller_tiling*controller[button][0][0])
		posy = math.trunc(tilingoffsety*controller['offset'][1] + controller_tiling*controller[button][0][1])
		sizex = math.trunc(controller_tiling*controller[button][0][2])
		sizey = math.trunc(controller_tiling*controller[button][0][3])

		pygame.draw.rect(
			screen,
			pygame.Color(controller[button][1][nuance]),
			pygame.Rect(posx, posy, sizex, sizey)
		)

		if button == 'a' or button == 'b':
			font = pygame.font.SysFont('didot.ttc', math.trunc(sizex*1))
			img = font.render(str.upper(str(button)), False, (255, 0, 0))
			screen.blit(img, (posx + controller_tiling/2, posy + controller_tiling, sizex, sizey))

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

def runGenome(genome, config):

	reduceSize = int(math.sqrt(config.genome_config.num_inputs))

	debut = open("./debut.save", "rb")
	pyboy.load_state(debut)
	pyboy.tick()
	debut.close()

	info = readLevelInfos(sml, reduceSize)
	resetInputs(pyboy)
	fitness = 0 
	net = neat.nn.FeedForwardNetwork.create(genome, config)
	stuckFrames = 0
	maxStuckFrames = 25
	maxFitness = fitness
	
	while not pyboy.tick():
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
			sendInputs(pyboy, manipulations)

			graph = buildGraph(config.genome_config.input_keys, config.genome_config.output_keys, genome)


			displayNetwork(screen, reduceSize, config.genome_config.input_keys, config.genome_config.output_keys, graph[1], graph[0], manipulations, info["tiles"])
			info = readLevelInfos(sml, reduceSize)
			fitness = 0 if sml.level_progress is None else sml.level_progress
			if fitness <= maxFitness:
				stuckFrames += 1
			else:
				maxFitness = fitness
				stuckFrames = 0
		else:
			break
	if options.use_coins_in_fitness:
		fitness += sml.coins*10
	if options.use_score_in_fitness:
		fitness += sml.score/10
	return fitness
		

def getMarioPos(tiles):
	for y in range(len(tiles)):
		for x in range(len(tiles[y])):
			tile = tiles[y][x]
			if tile in range(0, 26): #mario
				return (x, y)
	return None

def normalise(tiles, reduceSize):
	pos = getMarioPos(tiles)
	if pos is None:
		return None
	offset = 1
	if reduceSize%2 == 0:
		offset = 0
	xmin = pos[0]-reduceSize//2+1
	xmax = pos[0]+reduceSize//2+offset+1
	ymin = pos[1]-reduceSize//2+1
	ymax = pos[1]+reduceSize//2+offset+1
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
	return transform(xmin, xmax, ymin, ymax, tiles, reduceSize)

def transform(xmin, xmax, ymin, ymax, tiles, reduceSize):
	ntiles = [0 for _ in range(reduceSize*reduceSize)]
	for y in range(ymin, ymax):
		for x in range(xmin, xmax):
			i = (reduceSize)*(y-ymin)+(x-xmin)
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

def readLevelInfos(sml, reduceSize): 
	area = sml.game_area()
	tiles = normalise(area, reduceSize)
	levelInfo = {
        "dead":sml.lives_left <= 1, 
        "tiles":tiles
    }
	return levelInfo

def resetInputs(pyboy):
	pyboy.send_input(WindowEvent.RELEASE_BUTTON_A)
	pyboy.send_input(WindowEvent.RELEASE_BUTTON_B)
	pyboy.send_input(WindowEvent.RELEASE_ARROW_UP)
	pyboy.send_input(WindowEvent.RELEASE_ARROW_DOWN)
	pyboy.send_input(WindowEvent.RELEASE_ARROW_LEFT)
	pyboy.send_input(WindowEvent.RELEASE_ARROW_RIGHT)


def sendInputs(pyboy, manipulations):
	resetInputs(pyboy)
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

	pop = neat.Population(config)

    # Add a stdout reporter to show progress in the terminal.
	pop.add_reporter(neat.StdOutReporter(True))
	stats = neat.StatisticsReporter()
	pop.add_reporter(stats)
	pop.add_reporter(neat.Checkpointer(1, filename_prefix='./checkpoints/neat-checkpoint-'))

	pe = neat.ParallelEvaluator(4, runGenome)
	winner = pop.run(pe.evaluate, 100)

if __name__ == '__main__':
	#while not pyboy.tick():
	#	pass
	#pyboy.stop()
	#print(sml)
	dirname = os.path.dirname(__file__)
	run(Path( sys.argv[2] ))