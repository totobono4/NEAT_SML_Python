import math
import sys
import os
from pyboy import PyBoy
from pathlib import Path
import pygame
import numpy

PYGAME_SCREEN_WIDTH = 500
PYGAME_SCREEN_HEIGH = 500

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
pyboy.set_emulation_speed(1)
sml = pyboy.game_wrapper()
sml.start_game()

pygame.init()
screen = pygame.display.set_mode([PYGAME_SCREEN_HEIGH, PYGAME_SCREEN_WIDTH])

def display():
    screen.fill((0,0,0))

    neuron_size_out = 10
    neuron_size_in = 6

    area = numpy.asarray(sml.game_area())
    display_heigh = len(area)
    display_width = len(area[0])

    for y in range(display_heigh):
        for x in range(display_width):
            rawvalue = area[y][x]
            nuance = math.trunc(rawvalue/ 400 * 255)
            posx = math.trunc(PYGAME_SCREEN_WIDTH / (display_width) * x)
            posy = math.trunc(PYGAME_SCREEN_HEIGH / (display_heigh) * y)
            sizex = math.trunc(PYGAME_SCREEN_WIDTH / (display_width))
            sizey = math.trunc(PYGAME_SCREEN_HEIGH / (display_heigh))
            pygame.draw.rect(
                screen,
                pygame.Color((nuance, nuance, nuance)),
                pygame.Rect(posx, posy, sizex, sizey)
            )

            font = pygame.font.SysFont('didot.ttc', math.trunc(sizex*3/4))
            img = font.render(str(rawvalue), False, (0, 0, 255))
            screen.blit(img, (posx, posy, sizex, sizey))

    pygame.display.flip()

if __name__ == '__main__':
    while not pyboy.tick():
        display()
        pass
    pyboy.stop()
    pygame.quit()