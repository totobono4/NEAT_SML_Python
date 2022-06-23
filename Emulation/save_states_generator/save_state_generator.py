from pyboy import PyBoy
import sys
from pathlib import Path

# Check if the ROM is given through argv
if len(sys.argv) > 1:
    SML_File = Path( sys.argv[1] )
else:
    print("Usage: python SML_IA.py [ROM file]")
    exit(1)

if not SML_File.exists:
    print('You have to put a Super Mario Land ROM that exists')
    exit(1)

for i in range(1,5):
    for j in range(1,4):
        pyboy = PyBoy(SML_File.as_posix(), game_wrapper=True, window_type="SDL2")
        pyboy.set_emulation_speed(1)
        sml = pyboy.game_wrapper()

        sml.set_world_level(i,j)
        sml.start_game()

        saves_states_folder = Path('saves_states')
        save_state = Path(saves_states_folder, f"save_state_{sml.world[0]}-{sml.world[1]}.save")

        save_state_file = open(save_state, "wb")
        pyboy.save_state(save_state_file)
        save_state_file.close()

        pyboy.stop()
