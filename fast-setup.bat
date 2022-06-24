python -m ensurepip --upgrade
pip install -r requirements.txt
cd Emulation/save_states_generator
python save_state_generator.py ../ROMS/SML.gb
cd ../neat
python .\main.py ..\ROMS\SML.gb .\bests_configs\toto_10x10.txt ..\save_states_generator\saves_states\save_state_1-1.save