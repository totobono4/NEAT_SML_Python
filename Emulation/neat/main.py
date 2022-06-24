import math
import sys
import os
from pyboy import PyBoy
import neat
from pathlib import Path, WindowsPath
import pygame
import pickle

sys.path.append(str(Path(Path().cwd().parent)))
import utils.learnOptions as options
import utils.dataExtractor as extractor
import utils.inputManager as manager

infos = {}

PYGAME_SCREEN_WIDTH = 700
PYGAME_SCREEN_HEIGH = 400

root = __file__

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
    infos['ROM file'] = str(SML_File.name)
else:
    print("Usage: python SML_IA.py [ROM file]")
    exit(1)

if not SML_File.exists:
    print('You have to put a Super Mario Land ROM that exists')
    exit(1)

# Check if the config is given through argv
if len(sys.argv) > 2:
    config_File = Path( sys.argv[2] )
    infos['config file'] = str(config_File.name)
else:
    print("Usage: python SML_IA.py [ROM file] [config file]")
    exit(1)

if len(sys.argv) > 3:
    save_state = Path( sys.argv[3] )
    infos['save_state file'] = str(save_state.name)
else:
    print("Usage: python SML_IA.py [ROM file] [config file] [save state file]")
    exit(1)

quiet = "--quiet" in sys.argv
debugging = "--debug" in sys.argv
flagInfos = "--Infos" in sys.argv
flagDisplay = "--Display" in sys.argv
pyboy = PyBoy(SML_File.as_posix(), game_wrapper=True, window_type="headless" if quiet else "SDL2", debug=debugging)
pyboy.set_emulation_speed(0)
sml = pyboy.game_wrapper()
sml.start_game()
infos['generation'] = -1
infos['fitnessMax'] = sml.fitness

f_save_state = open(save_state, "rb")
pyboy.load_state(f_save_state)
f_save_state.close()

if not flagInfos:
    PYGAME_SCREEN_WIDTH = 400

def displayNetwork(inputs, outputs, hiddens, connections, outs, tilesvector):
    infos['inputs'] = len(inputs)
    infos['hiddens'] = len(hiddens)
    infos['output'] = len(outputs)
    infos['connections'] = len(connections)

    screen.fill((0,0,0))
    size = screen.get_size()

    infos['fitnessMax'] = infos['fitness'] if infos['fitness'] > infos['fitnessMax'] else infos['fitnessMax']
    display_width = display_heigh = options.reduceSize

    tiling = (2,2)
    if flagInfos:
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
            math.trunc(abs(weight)+1) * sizex // 10 if active else 1)

    if flagInfos:
        for info in range(len(list(infos.keys()))):
            posx = math.trunc(tilingoffsetx * infosoffset[0])
            posy = math.trunc(tilingoffsety * infosoffset[1] + info * tilingy)
            sizex = math.trunc(tilingoffsetx)
            sizey = math.trunc(tilingoffsety)

            font = pygame.font.SysFont('didot.ttc', math.trunc(sizex/tiling[0]/2*3/4))
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

def runGenome(genome, config):
    info = extractor.readLevelInfos(sml, options)
    manager.resetInputs(pyboy)
    fitness = 0 
    net = neat.nn.FeedForwardNetwork.create(genome, config)
    stuckFrames = 0
    maxStuckFrames = 60
    noProgressFrames = 0
    maxNoProgressFrames = 600
    lastFitness = fitness
    maxFitness = fitness
    
    while not info["dead"]:
        if stuckFrames >= maxStuckFrames or noProgressFrames >= maxNoProgressFrames:
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
            manager.sendInputs(manipulations, pyboy, options)
            pyboy.tick()

            graph = buildGraph(config.genome_config.input_keys, config.genome_config.output_keys, genome)

            infos['fitness'] = fitness
            if flagDisplay:
                displayNetwork(config.genome_config.input_keys, config.genome_config.output_keys, graph[1], graph[0], manipulations, info["tiles"])
            info = extractor.readLevelInfos(sml, options)
            fitness = 0 if sml.level_progress is None else sml.level_progress
            if fitness <= maxFitness:
                noProgressFrames += 1
            else:
                maxFitness = fitness
                noProgressFrames = 0
            if fitness == lastFitness:
                stuckFrames += 1
            else:
                stuckFrames = 0
            lastFitness = fitness
        else:
            break
    if options.use_coins_in_fitness:
        fitness += sml.coins*10
    if options.use_score_in_fitness:
        fitness += sml.score/10
    f_save_state = open(save_state, "rb")
    pyboy.load_state(f_save_state)
    f_save_state.close()
    pyboy.tick()
    return fitness

def step(genomes, config):
    infos['generation'] += 1
    gen = 0
    for genome_id, genome in genomes:        
        print("Gen : "+str(gen)+" : "+str(len(genomes)), end="\r")
        gen+=1
        infos['individual'] = str(gen)+" ("+str(int(gen/len(genomes)*100))+"%)"
        genome.fitness = runGenome(genome, config)

def run(config_path):
    config = neat.Config(neat.DefaultGenome, neat.DefaultReproduction,
        neat.DefaultSpeciesSet, neat.DefaultStagnation,
        config_path)
    options.reduceSize = int(math.sqrt(config.genome_config.num_inputs))

    pop = neat.Population(config)
    pop = neat.Checkpointer.restore_checkpoint('./checkpoints/ch-potential1')

    # Add a stdout reporter to show progress in the terminal.
    pop.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    pop.add_reporter(stats)
    pop.add_reporter(neat.Checkpointer(1, filename_prefix='./checkpoints/neat-checkpoint-'))

    winner = pop.run(step, 1)

    with open(f"winners/winner_{config_File.stem}.pkl", "wb") as f:
        pickle.dump(winner, f)
        f.close()

    # Show output of the most fit genome against training data.
    print('\nOutput:')

    #p = neat.Checkpointer.restore_checkpoint('./checkpoints/neat-checkpoint-1')
    #p.run(step, 10)

if __name__ == '__main__':
    if flagDisplay:
        pygame.init()
        screen = pygame.display.set_mode([PYGAME_SCREEN_WIDTH, PYGAME_SCREEN_HEIGH], pygame.RESIZABLE)

    dirname = os.path.dirname(__file__)
    run(config_File)

    if flagDisplay:
        pygame.quit()
