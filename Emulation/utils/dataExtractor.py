import pyboy
import utils.learnOptions as learnOptions

options = learnOptions

def getMarioPos(tiles):
	for y in range(len(tiles)):
		for x in range(len(tiles[y])):
			tile = tiles[y][x]
			if tile in range(0, 26): #mario
				return (x, y)
	return None

def normalise(tiles, reduceSize, options):
	pos = getMarioPos(tiles)
	if pos is None:
		return None
	offset = 1
	if reduceSize%2 == 0:
		offset = 0
	xmin = pos[0]-reduceSize//2+1
	xmax = pos[0]+reduceSize//2+offset+1
	ymin = pos[1]-reduceSize//2-offset+1
	ymax = pos[1]+reduceSize//2-offset+1
	if xmin < 0:
		xmin = 0
	if xmax >= len(tiles[0]):
		xmax = len(tiles[0])-1
	if ymin < 0:
		ymin = 0
	if ymax >= len(tiles):
		ymax = len(tiles)-1
	return transform(xmin, xmax, ymin, ymax, tiles, options)

def transform(xmin, xmax, ymin, ymax, tiles, options : learnOptions):
	ntiles = [0 for _ in range(options.reduceSize*options.reduceSize)]
	for y in range(ymin, ymax):
		for x in range(xmin, xmax):
			i = (options.reduceSize)*(y-ymin)+(x-xmin)
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

def readLevelInfos(sml : pyboy, options : learnOptions): 
	area = sml.game_area()
	tiles = normalise(area, options.reduceSize, options)
	levelInfo = {
        "dead":sml.lives_left <= 1, 
        "tiles":tiles
    }
	return levelInfo