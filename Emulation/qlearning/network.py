from tensorflow import keras
import tensorflow as tf
import random
import numpy as np
from pathlib import Path

history = keras.callbacks.History()

tf.get_logger().setLevel('ERROR')
tf.autograph.set_verbosity(3)

class MarioAi:

    def __init__(self, state_shape, actions, window_size=2, savedir = "./save/", state_creator = lambda model: [[0]*model.state_shape]*model.window_size):
        
        self.dataset = [] #the database

        self.epsilon = 1
        self.state_shape=state_shape
        self.action_shape=len(actions)
        self.actions=actions
        self.window_size = window_size

        savepath = Path(savedir)
        if not savepath.exists():
            savepath.mkdir()

        self.savecallback = tf.keras.callbacks.ModelCheckpoint(filepath=savedir,
                                                 save_weights_only=True,
                                                 verbose=0)

        self.optimizer = tf.keras.optimizers.Adam(learning_rate=0.00025)

        self.agent = self.getAgent()
        self.target_agent = self.getAgent()
        self.state_creator = state_creator

    def getAgent(self): #retrieves an agent (model)
        model = keras.Sequential()
        model.add(keras.Input(shape=(self.state_shape*self.window_size, )))
        model.add(keras.layers.Dense(25, activation='relu', kernel_initializer=keras.initializers.he_normal()))
        model.add(keras.layers.Dense(25, activation='relu', kernel_initializer=keras.initializers.he_normal()))
        model.add(keras.layers.Dense(25, activation='relu', kernel_initializer=keras.initializers.he_normal()))
        model.add(keras.layers.Dense(self.action_shape, activation='linear', kernel_initializer=keras.initializers.Zeros()))
        model.compile(loss = "mse", optimizer = self.optimizer)
        return model

    def dense_layer(num_units):
        return tf.keras.layers.Dense(
            num_units,
            activation=tf.keras.activations.relu,
            kernel_initializer=tf.keras.initializers.VarianceScaling(
                scale=2.0, mode='fan_in', distribution='truncated_normal'))

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
    def train(self, sml, stepper, batchsize = 32, episodes = 100, steps = 1000):

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
            previousprogress = sml.level_progress
            while step < steps:
                act = self.getSolution(st)
                reward = stepper(act, previousprogress) #step in game
                reward_mean.append(reward)
                previousprogress = sml.level_progress
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

                st = st2 #go to next state
                step += 1
                if stop: #if mario died, reset the game
                    stop = False
                    sml.reset_game()

            if epi%2 == 0:
                self.train_model(batchsize)
                
            self.epsilon = max(0.1, self.epsilon*0.99) #decrement epsilon

            if epi%5 == 0:
                self.target_agent.set_weights(self.agent.get_weights())
                sml.reset_game() #reset to initial game state
                tot_reward = 0
                stuckcount = 0
                state = self.state_creator(self) #extract initial game state
                previousprogress = sml.level_progress
                maxprogress = previousprogress
                while True:
                    out = self.agent.predict(state, verbose="0") #use model to get action from current state
                    act = 0
                    maxout = out[0] #get the action the model is the most "sur" about
                    for i in range(1, len(out)):
                        if out[i] > maxout:
                            act = i
                            maxout = out[i]
                    reward = stepper(act, previousprogress) #ste in game and get reward
                    state = self.state_creator(self)
                    previousprogress = sml.level_progress
                    if previousprogress > maxprogress:
                        maxprogress = previousprogress
                    tot_reward += reward
                    if sml.lives_left < 2 or stuckcount >= 150: #if end condition met, exit play mode
                        break
                    elif sml.level_progress < maxprogress: #if no progress, increment kill counter
                        stuckcount+=1
                    else:
                        stuckcount=0
                print("Game end : reward : "+str(tot_reward))
        
        print("------------stats------------")
        print("rewards mean : "+str(np.mean(reward_mean)))
        print("episode "+str(epi))
        print("-----------------------------")
            

    #make the model train
    def train_model(self, batchsize):
        minibatch = random.sample(self.dataset, batchsize)
        i = 0

        for state, reward, next_state, action in minibatch:

            target = self.agent.predict(state, verbose="0")

            t = self.target_agent.predict(next_state, verbose="0")
            target[0][action] = reward + 0.99 * np.amax(t)

            self.agent.fit(state, target, epochs=1, verbose="0")
            print("Learning "+str(i)+"/"+str(len(minibatch)), end = "\r")
            i+=1