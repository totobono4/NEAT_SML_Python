import random
import neat
import os
import visualize

if __name__ == "__main__":
    dirname = os.path.dirname(__file__)
    config_path = os.path.join(dirname, "neat_config.txt")
    run(config_path)