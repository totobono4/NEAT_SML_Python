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

debut = open("./debut.save", "wb")
pyboy.save_state(debut)
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

if __name__ == '__main__':
    pygame.init()
    sml.le
    screen = pygame.display.set_mode([PYGAME_SCREEN_HEIGH, PYGAME_SCREEN_WIDTH])
    pygame.quit()
