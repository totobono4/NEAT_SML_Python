import os
import sys
from pyboy import PyBoy
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

if __name__ == '__main__':
	while not pyboy.tick():
		pass
	pyboy.stop()
