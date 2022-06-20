import sys
import os
from pyboy import PyBoy, WindowEvent
import neat
import visualize
from pathlib import Path, PosixPath, PurePath, PureWindowsPath

SML_File = Path('ROMS', 'SML.gb')

if not SML_File.exists:
	print('You have to put a Super Mario Land ROM named "SML.gb" in ROMS/.')
	exit(1)

quiet = "--quiet" in sys.argv
pyboy = PyBoy(Path(SML_File).as_posix(), game_wrapper=True, window_type="headless" if quiet else "SDL2")
pyboy.set_emulation_speed(0)
sml = pyboy.game_wrapper()
sml.start_game()

mario = pyboy.game_wrapper()

def step(genomes, config):
	for genome_id, genome in genomes:
		with open("./debut.state") as statefile:
			pyboy.save_state(statefile)
		info = readLevelInfos()
		genome.fitness = mario.fitness       
		net = neat.nn.FeedForwardNetwork.create(genome, config)
		stuckFrames = 0
		maxStuckFrames = 1000
		maxFitness = genome.fitness
        
		while not info["dead"]:
			if stuckFrames >= maxStuckFrames:
				break
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
			info = readLevelInfos()
			genome.fitness = info["mposition"]["x"]   
			if genome.fitness <= maxFitness:
				stuckFrames += 1
			else:
				stuckFrames = 0

def readLevelInfos():   
    levelInfo = {
        "dead":mario.lives_left <= 0, 
        "tiles":[]
    }
    return levelInfo

def sendInputs(manipulations):
	if manipulations["a"]:
		pyboy.send_input(WindowEvent.PRESS_BUTTON_A)
	if manipulations["b"]:
		pyboy.send_input(WindowEvent.PRESS_BUTTON_B)
	if manipulations["up"]:
		pyboy.send_input(WindowEvent.PRESS_ARROW_UP)
	if manipulations["down"]:
		pyboy.send_input(WindowEvent.PRESS_ARROW_DOWN)
	if manipulations["left"]:
		pyboy.send_input(WindowEvent.PRESS_ARROW_LEFT)
	if manipulations["right"]:
		pyboy.send_input(WindowEvent.PRESS_ARROW_RIGHT)

def run(config_path):
    config = neat.Config(neat.DefaultGenome, neat.DefaultReproduction,
        neat.DefaultSpeciesSet, neat.DefaultStagnation,
        config_path)
    config.genome_config.num_inputs = len(readLevelInfos()["tiles"])

    pop = neat.Population(config)

    # Add a stdout reporter to show progress in the terminal.
    pop.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    pop.add_reporter(stats)
    pop.add_reporter(neat.Checkpointer(5, filename_prefix="./checkpoints/neat-checkpoint-"))

    winner = pop.run(step,1000)

    # Show output of the most fit genome against training data.
    print('\nOutput:')

    node_names = {0: 'A', 1: 'B', 2:'X', 3:'Y', 4:'UP', 5:'DOWN', 6:'LEFT', 7:'RIGHT'}
    tiles = readLevelInfos()["tiles"]
    for i in range(len(tiles)):
        node_names[-len(tiles)+i] = "tile_"+str(i)
    visualize.draw_net(config, winner, True, node_names=node_names)
    visualize.plot_stats(stats, ylog=False, view=True)
    visualize.plot_species(stats, view=True)

    p = neat.Checkpointer.restore_checkpoint('./checkpoints/neat-checkpoint-4')
    p.run(step, 10)


if __name__ == '__main__':
	dirname = os.path.dirname(__file__)
	config_path = os.path.join(dirname, "neat_config.txt")
	run(config_path)
	pyboy.stop()
