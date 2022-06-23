import math
from operator import index
import sys
import os
from pyboy import PyBoy
from pathlib import Path
import pygame
from pyboy import WindowEvent

utilsPath = Path(Path().cwd().parent, 'utils')
sys.path.append(os.path.dirname(utilsPath))
import utils.learnOptions as options
import utils.dataExtractor as extractor

PYGAME_SCREEN_WIDTH = 750
PYGAME_SCREEN_HEIGH = 750

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

# Check if the config is given through argv
if len(sys.argv) > 2:
    options.reduceSize = int(sys.argv[2])
else:
    print("Usage: python SML_IA.py [ROM file] [Camera Size]")
    exit(1)

quiet = "--quiet" in sys.argv
debugging = "--debug" in sys.argv
pyboy = PyBoy(SML_File.as_posix(), game_wrapper=True, window_type="headless" if quiet else "SDL2", debug=debugging)
pyboy.set_emulation_speed(1)
sml = pyboy.game_wrapper()
sml.start_game()

pygame.init()
screen = pygame.display.set_mode([PYGAME_SCREEN_HEIGH, PYGAME_SCREEN_WIDTH], pygame.RESIZABLE)

outs = {
        "a": False,
        "b": False,
        "up": False,
        "down": False,
        "left": False,
        "right": False
    } #outputs

def display(goBrrrrr):
    screen.fill((0,0,0))
    size = screen.get_size()

    display_width = display_heigh = options.reduceSize

    tiling = (2,2)
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

    colors_filter = {
        options.empty: (255,255,255),
        options.mario:(0,0,255),
        options.enemy:(255,0,0),
        options.platform:(121,26,126),
        options.block:(244,255,0),
        options.coin:(241,194,50)
    }

    for y in range(display_heigh):
        for x in range(display_width):
            index2d = y*options.reduceSize+x
            rawvalue = goBrrrrr[index2d]
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
        nuance = 1 if outs[button] else 0
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
    
    pygame.display.flip()

def pyboyEventHandler():
    for input in pyboy.get_input():
        outs["a"] = True if input == WindowEvent.PRESS_BUTTON_A else False if input == WindowEvent.RELEASE_BUTTON_A else outs["a"]
        outs["b"] = True if input == WindowEvent.PRESS_BUTTON_B else False if input == WindowEvent.RELEASE_BUTTON_B else outs["b"]
        outs["up"] = True if input == WindowEvent.PRESS_ARROW_UP else False if input == WindowEvent.RELEASE_ARROW_UP else outs["up"]
        outs["down"] = True if input == WindowEvent.PRESS_ARROW_DOWN else False if input == WindowEvent.RELEASE_ARROW_DOWN else outs["down"]
        outs["left"] = True if input == WindowEvent.PRESS_ARROW_LEFT else False if input == WindowEvent.RELEASE_ARROW_LEFT else outs["left"]
        outs["right"] = True if input == WindowEvent.PRESS_ARROW_RIGHT else False if input == WindowEvent.RELEASE_ARROW_RIGHT else outs["right"]

if __name__ == '__main__':
    while not pyboy.tick():
        pyboyEventHandler()
        info = extractor.readLevelInfos(sml, options)
        if info["tiles"] is not None:
            display(info["tiles"])
        pass
    pyboy.stop()
    pygame.quit()