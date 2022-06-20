import random
import neat
import os
import visualize

def readLevelInfos():    
    levelInfo = {
        "mposition":{"x":random.randint(0, 200), "y":5}, 
        "dead":random.choice([True, False]), 
        "tiles":[random.randrange(1, 5, 1) for i in range(10)]
    }
    return levelInfo

def sendInputs(manipulations):
    pass

def step(genomes, config):
    for genome_id, genome in genomes:
        info = readLevelInfos()   
        genome.fitness = info["mposition"]["x"]        
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
                "x":out[2],
                "y":out[3],
                "up":out[4],
                "down":out[5],
                "left":out[6],
                "right":out[7]
            } #outputs
            sendInputs(manipulations)
            info = readLevelInfos()
            genome.fitness = info["mposition"]["x"]   
            if genome.fitness <= maxFitness:
                stuckFrames += 1
            else:
                stuckFrames = 0


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

if __name__ == "__main__":
    dirname = os.path.dirname(__file__)
    config_path = os.path.join(dirname, "neat_config.txt")
    run(config_path)