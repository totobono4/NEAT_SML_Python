from tkinter import Variable
from tensorflow import keras
import tensorflow as tf
import random
import numpy as np
import copy
import utils.dataExtractor as extractor
import utils.learnOptions as options
import math

tf.get_logger().setLevel('ERROR')
tf.autograph.set_verbosity(3)

states = []
rewards = []
rewards_mean = []
next_states = []
actions = []

epsilon = 1
optimizer = tf.keras.optimizers.Adam(learning_rate=0.01)

def getAgent(state_shape, action_shape):
    model = keras.Sequential()
    model.add(keras.layers.Input(shape=(state_shape,)))
    model.add(keras.layers.Dense(32, activation='relu'))
    model.add(keras.layers.Dense(action_shape, activation='linear'))
    model.compile(optimizer=optimizer, loss=tf.keras.losses.BinaryCrossentropy(), metrics=['accuracy'], run_eagerly=True)
    return model

def lossFunc(model, states, actions, targets):
    return np.mean(np.multiply(np.subtract(model.predict(states), targets), actions))

def getSolution(agent : keras.Sequential, state, actions):
    act = None
    if random.randrange(0, 1) <= epsilon:
        act =  random.choice(actions)
    else:
        tensor = np.array([state])
        result = agent.predict(tensor)
        max = result.argMax(1)
        act = max.buffer().values[0]

    return act

def train(agent, sml, acts, nbstates, nbactions, stepper, batch_size = 100, episodes = 150, steps = 10000, maxsave = 100000):

    global epsilon

    st = extractor.readLevelInfos(sml, options)
    st2 = None
    for epi in range(episodes):
        reward = 0
        step = 0
        stop = False
        lastState = st
        beginprogress = sml.level_progress
        while step < steps:
            act = getSolution(agent, st, acts)
            reward = stepper(act, beginprogress)
            st2 = extractor.readLevelInfos(sml, options)
            if st2 is None or None in st2 or sml.lives_left < 2:
                st2 = lastState
                stop = True
            else:
                laststate = st2
                

            mask = [1 if a == act else 0 for a in range(len(acts))]
            
            index = random.randint(0, len(states))
            states.insert(index, st["tiles"])
            rewards.insert(index, [reward])
            rewards_mean.insert(index, reward)
            next_states.insert(index, st2["tiles"])
            actions.insert(index, mask)

            if len(states) > maxsave:
                states.remove(random.choice(states))
                rewards.remove(random.choice(rewards))
                rewards_mean.remove(random.choice(rewards_mean))
                next_states.remove(random.choice(next_states))
                actions.remove(random.choice(actions))

            st = st2
            step += 1
            if stop:
                sml.reset_game()


        epsilon = max(0.1, epsilon*0.99)

        if epi % 5 == 0:
            print("------------stats------------")
            print("rewards mean : "+str(np.mean(rewards_mean)))
            print("episode "+str(epi))
            print("-----------------------------")
            train_model(agent, states, nbstates, rewards, next_states, actions, nbactions, batch_size)


        sml.reset_game()
        tot_reward = 0
        stuckcount = 0
        state = extractor.readLevelInfos(sml, options)["tiles"]
        while True:
            out = agent.predict(np.array([state]))
            act = 0
            maxout = out[0]
            for i in range(1, len(out)):
                if out[i] > maxout:
                    act = i
                    maxout = out[i]
            reward = stepper(act, beginprogress)
            state = extractor.readLevelInfos(sml, options)["tiles"]
            tot_reward += reward
            if sml.lives_left < 2 or stuckcount >= 150:
                break
            elif sml.level_progress < sml._level_progress_max:
                print(str(150-stuckcount)+" frames before death ...")
                stuckcount+=1
        print("Game end : reward : "+str(tot_reward))
        sml.reset_game()

def train_model(agent, states, nbstates, rewards, next_states, actions, nbactions, batch_size):
    size = len(next_states)
    tf_states = np.array(states)
    tf_rewards = np.array(rewards)
    tf_next_states = np.array(next_states)
    tf_actions = np.array(actions)


    stpl = agent.predict(tf_next_states)
    targets = np.add(np.multiply(np.expand_dims(np.max(stpl, 1), axis = 1), 0.99), tf_rewards)

    for b in range(0, size, batch_size):

        to = batch_size if (b+batch_size)<size else (size-b)
        tf_states_b = tf.constant(np.array(tf_states[b:to]).astype(np.float32))
        tf_action_b = np.array(tf_actions[b:to]).astype(np.float32)
        tf_targets_b = tf.constant(np.array(targets[b:to]).astype(np.float32))

        inputs = tf.Variable(tf_action_b)

        with tf.GradientTape() as tape:

            tape.watch(inputs)

            loss = tf.square(agent(tf_states_b) - tf_targets_b) * inputs

        optimizer.minimize(loss, var_list=inputs, tape=tape)

        #agent.fit(tf_states_b, tf_targets_b)
