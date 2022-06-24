from tkinter import Variable
from tensorflow import keras
import tensorflow as tf
import random
import numpy as np
import copy
from pathlib import Path
import sys
import os
utilsPath = Path(Path().cwd().parent, 'utils')
sys.path.append(os.path.dirname(utilsPath))
import utils.dataExtractor as extractor
import utils.learnOptions as options
import math

history = keras.callbacks.History()

tf.get_logger().setLevel('ERROR')
tf.autograph.set_verbosity(3)

class MarioAi:

    def __init__(self, state_shape, actions, window_size=2, savedir = "save", state_creator = lambda model: [[0]*model.state_shape]*model.window_size):
        
        self.dataset = [] #the database

        self.epsilon = 1
        self.state_shape=state_shape
        self.action_shape=len(actions)
        self.actions=actions
        self.window_size = window_size
        self.savecallback = tf.keras.callbacks.ModelCheckpoint(filepath=savedir,
                                                 save_weights_only=True,
                                                 verbose=1)

        self.optimizer = tf.keras.optimizers.Adam(learning_rate=0.01)

        self.agent = self.getAgent()
        self.state_creator = state_creator

    def getAgent(self): #retrieves an agent (model)
        model = keras.Sequential()
        model.add(keras.layers.Dense(64, input_shape=(self.state_shape*self.window_size, ), activation='relu'))
        model.add(keras.layers.Dense(128, activation='relu'))
        model.add(keras.layers.Dense(255, activation='relu'))
        model.add(keras.layers.Dense(self.action_shape, activation='linear'))
        model.compile(optimizer=self.optimizer, loss='mse')
        return model

    def getSolution(self, state): #gets an action from a state using an agent, with epsilon-greedy algorithm
        act = None
        if random.randrange(0, 1) <= self.epsilon:
            act =  random.choice(self.actions)
        else:
            tensor = np.array([state])
            result = self.agent.predict(tensor, verbose="0")
            max = result.argMax(1)
            act = max.buffer().values[0]
        return act

    #trains the model
    def train(self, sml, stepper, batchsize=400, episodes = 150, steps = 1000, maxsave = 10000):

        global epsilon

        st = self.state_creator(self) #extracts a game state
        st2 = None
        for epi in range(episodes): #for each episode
            print("Epoch "+str(epi)+" / "+str(episodes))
            sml.reset_game() #set game to start state
            reward_mean = []
            reward = 0
            step = 0
            stop = False
            lastState = st
            beginprogress = sml.level_progress
            while step < steps:
                act = self.getSolution(st)
                reward = stepper(act, beginprogress) #step in game
                reward_mean.append(reward)
                st2 = self.state_creator(self) #extract next state
                if st2 is None or sml.lives_left < 2:
                    st2 =  np.copy(lastState)
                    stop = True
                else:
                    laststate = np.copy(st2)
                    st2 = st2
                
                #save data in a random spot of our database
                index = random.randint(0, len(self.dataset))
                self.dataset.insert(index, (st, reward, st2, act))

                if len(self.dataset) > maxsave: #if database is too big, remove a random row
                    del self.dataset[index]
                st = st2 #go to next state
                step += 1
                if stop: #if mario died, reset the game
                    stop = False
                    sml.reset_game()


            self.epsilon = max(0.1, self.epsilon*0.99) #decrement epsilon

            if epi % 5 == 0:
                print("------------stats------------")
                print("rewards mean : "+str(np.mean(reward_mean)))
                print("episode "+str(epi))
                print("-----------------------------")
                self.train_model(batchsize)



                sml.reset_game() #reset to initial game state
                tot_reward = 0
                stuckcount = 0
                state = self.state_creator(self) #extract initial game state
                while True:
                    out = self.agent.predict(state, verbose="0") #use model to get action from current state
                    act = 0
                    maxout = out[0] #get the action the model is the most "sur" about
                    for i in range(1, len(out)):
                        if out[i] > maxout:
                            act = i
                            maxout = out[i]
                    reward = stepper(act, beginprogress) #ste in game and get reward
                    state = self.state_creator(self)
                    tot_reward += reward
                    if sml.lives_left < 2 or stuckcount >= 150: #if end condition met, exit play mode
                        break
                    elif sml.level_progress < sml._level_progress_max: #if no progress, increment kill counter
                        stuckcount+=1
                print("Game end : reward : "+str(tot_reward))
            

    #make the model train
    def train_model(self, batchsize):

        index = random.randint(0, len(self.dataset)-batchsize-1)
        i = 0
        for state, reward, nextstate, action in self.dataset[index:index+batchsize]: #split database in batches

            reward = reward + 0.99 * np.amax(self.agent.predict(nextstate, verbose="0")[0])

            target = self.agent.predict(state, verbose="0")
            target[0][action] = reward

            print("Aggregating learning factors : "+str(i)+"/"+str(batchsize), end="\r")
            i+=1
            
            self.agent.fit(state, target, batch_size=len(self.dataset), verbose="0", use_multiprocessing=True, callbacks=[history, self.savecallback], workers=4)

        meanloss = np.mean(history.history["loss"])
        print("\r")
        print("Mean loss : "+str(meanloss))