import utils.learnOptions as options
import pygame
import math

infos = {}

PYGAME_SCREEN_WIDTH = 600
PYGAME_SCREEN_HEIGH = 400
size = (PYGAME_SCREEN_WIDTH, PYGAME_SCREEN_HEIGH)


pygame.init()
screen = pygame.display.set_mode([PYGAME_SCREEN_WIDTH, PYGAME_SCREEN_HEIGH], pygame.RESIZABLE)

def displayNetwork(inputs, outputs, hiddens, connections, outs, tilesvector):
	global reduceSize

	screen.fill((0,0,0))

	infos['fitnessMax'] = infos['fitness'] if infos['fitness'] > infos['fitnessMax'] else infos['fitnessMax']

	display_width = display_heigh = options.reduceSize

	tiling = (3,2)

	tilingoffsetx : int
	tilingoffsety : int
	
	if size[0] / tiling[0] < size[1] / tiling[1]:
		tilingoffsetx = size[0] / tiling[0]
		tilingoffsety = tilingoffsetx
	else:
		tilingoffsety = size[1] / tiling[1]
		tilingoffsetx = tilingoffsety

	tilingx = tilingoffsetx/display_width
	tilingy = tilingoffsety/display_heigh

	controller_tiling = tilingoffsety/7
	
	perceptrons = {}

	hiddenoffset = (1,0)
	hiddentiling = (1,1)

	infosoffset = (2,0)

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
			index2d = y*options.reduceSize+x
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
		perceptrons[options.outputNames[button]] = center

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
	
	for info in range(len(list(infos.keys()))):
		posx = math.trunc(tilingoffsetx * infosoffset[0])
		posy = math.trunc(tilingoffsety * infosoffset[1] + info * tilingy)
		sizex = math.trunc(tilingoffsetx)
		sizey = math.trunc(tilingoffsety)

		font = pygame.font.SysFont('didot.ttc', math.trunc(sizex/tiling[0]/2))
		img = font.render(list(infos.keys())[info] + ': ' + str(infos[list(infos.keys())[info]]), False, (255, 255, 0))
		screen.blit(img, (posx, posy, sizex, sizey))
	
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