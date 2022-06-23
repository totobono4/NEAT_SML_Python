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

states = [] #the states database
rewards = [] #the rewards database
rewards_mean = [] #the reward database for mean reward
next_states = [] #the next state database
actions = [] #the actions database

epsilon = 1
optimizer = tf.keras.optimizers.Adam(learning_rate=0.01)

def getAgent(state_shape, action_shape): #retrieves an agent (model)
    model = keras.Sequential()
    model.add(keras.layers.Dense(32, input_dim=state_shape, activation='relu'))
    model.add(keras.layers.Dense(64, activation='relu'))
    model.add(keras.layers.Dense(units=128, activation='relu'))
    model.add(keras.layers.Dense(action_shape, activation='linear'))
    model.compile(optimizer=optimizer, loss='mse')
    return model

def getSolution(agent : keras.Sequential, state, actions): #gets an action from a state using an agent, with epsilon-greedy algorithm
    act = None
    if random.randrange(0, 1) <= epsilon:
        act =  random.choice(actions)
    else:
        tensor = np.array([state])
        result = agent.predict(tensor, verbose="0")
        max = result.argMax(1)
        act = max.buffer().values[0]

    return act

#trains the model
def train(agent, sml, acts, stepper, batch_size = 100, episodes = 150, steps = 10000, maxsave = 100000):

    global epsilon

    st = extractor.readLevelInfos(sml, options)["tiles"] #extracts a game state
    st2 = None
    for epi in range(episodes): #for each episode
        sml.reset_game() #set game to start state
        reward = 0
        step = 0
        stop = False
        lastState = st
        beginprogress = sml.level_progress
        while step < steps:
            act = getSolution(agent, st, acts)
            reward = stepper(act, beginprogress) #step in game
            st2 = extractor.readLevelInfos(sml, options) #extract next state
            if st2 is None or None in st2 or sml.lives_left < 2:
                st2 =  np.copy(lastState)
                stop = True
            else:
                laststate = st2["tiles"]     
                st2 = st2["tiles"]       

            mask = [1 if a == act else 0 for a in range(len(acts))] #use action as a decimal mask
            
            #save data in a random spot of our database
            index = random.randint(0, len(states))
            states.insert(index, st)
            rewards.insert(index, [reward])
            rewards_mean.insert(index, reward)
            next_states.insert(index, st2)
            actions.insert(index, mask)

            if len(states) > maxsave: #if database is too big, remove a random row
                del states[index]
                del rewards[index]
                del rewards_mean[index]
                del next_states[index]
                del actions[index]
            st = st2 #go to next state
            step += 1
            if stop: #if mario died, reset the game
                stop = False
                sml.reset_game()


        epsilon = max(0.1, epsilon*0.99) #decrement epsilon

        if epi % 5 == 0:
            print("------------stats------------")
            print("rewards mean : "+str(np.mean(rewards_mean)))
            print("episode "+str(epi))
            print("-----------------------------")
            train_model(agent, states, rewards, next_states, actions, batch_size)

        sml.reset_game() #reset to initial game state
        tot_reward = 0
        stuckcount = 0
        state = extractor.readLevelInfos(sml, options)["tiles"] #extract initial game state
        while True:
            out = agent.predict(np.array([state]), verbose="0") #use model to get action from current state
            act = 0
            maxout = out[0] #get the action the model is the most "sur" about
            for i in range(1, len(out)):
                if out[i] > maxout:
                    act = i
                    maxout = out[i]
            reward = stepper(act, beginprogress) #ste in game and get reward
            state = extractor.readLevelInfos(sml, options)["tiles"]
            tot_reward += reward
            if sml.lives_left < 2 or stuckcount >= 150: #if end condition met, exit play mode
                break
            elif sml.level_progress < sml._level_progress_max: #if no progress, increment kill counter
                stuckcount+=1
        print("Game end : reward : "+str(tot_reward))

#make the model train
def train_model(agent, states, rewards, next_states, actions, batch_size):
    tf_states = np.array(states)
    tf_rewards = np.array(rewards)
    tf_next_states = np.array(next_states)
    tf_actions = np.array(actions)
    
    meanloss = 0

    mse = tf.keras.losses.MeanSquaredError()
    for b in range(len(states) - batch_size + 1, len(states)): #split database in batches

        reward = tf_rewards[b]
        reward = reward + 0.99 * np.amax(agent.predict(np.array([tf_next_states[b]]), verbose="0")[0])

        target = agent.predict(np.array([tf_states[b]]), verbose="0")
        target[0][tf_actions[b]] = reward

        #minimize loss using custom loss function
        agent.fit(np.array([tf_states[b]]), target, verbose="0", use_multiprocessing=True, callbacks=[history])

    meanloss = np.mean(history.history["loss"])
    print("Mean loss : "+str(meanloss))
    history.history["loss"]=[]
