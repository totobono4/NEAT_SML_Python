import sys
from pyboy import PyBoy

quiet = "--quiet" in sys.argv
pyboy = PyBoy('ROMS/SML.gb', game_wrapper=True, window_type="headless" if quiet else "SDL2")
pyboy.set_emulation_speed(0)
sml = pyboy.game_wrapper()
sml.start_game()

if __name__ == '__main__':
	while not pyboy.tick():
		pass
	pyboy.stop()
