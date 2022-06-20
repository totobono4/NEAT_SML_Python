import os
import sys
from pyboy import PyBoy
from pathlib import Path, PosixPath, PurePath, PureWindowsPath

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
pyboy = PyBoy(SML_File.as_posix(), game_wrapper=True, window_type="headless" if quiet else "SDL2")
pyboy.set_emulation_speed(0)
sml = pyboy.game_wrapper()
sml.start_game()

if __name__ == '__main__':
	print(sml)
	while not pyboy.tick():
		pass
	pyboy.stop()
