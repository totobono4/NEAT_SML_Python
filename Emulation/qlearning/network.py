from tensorflow import keras
import tensorflow as tf
import random
import numpy as np
from pathlib import Path

history = keras.callbacks.History()

tf.get_logger().setLevel('ERROR')
tf.autograph.set_verbosity(3)

class MarioAi:

    def __init__(self, state_shape, actions, actiondistrib = None, savedir = "./save/", state_creator = lambda model: [0]*model.state_shape):
        
        self.dataset = [] #the database
        if actiondistrib is None:
            self.actiondistrib = [1]*len(actions)
        else:
            if len(actiondistrib) != len(actions): raise "Actions' distribution must have the same length as actions"
            else: self.actiondistrib = actiondistrib

        self.epsilon = 1
        self.state_shape=state_shape
        self.action_shape=len(actions)
        self.actions=actions

        savepath = Path(savedir)
        if not savepath.exists():
            savepath.mkdir()

        self.savecallback = tf.keras.callbacks.ModelCheckpoint(filepath=savedir,
                                                 save_weights_only=True,
                                                 verbose=0)

        self.optimizer = tf.keras.optimizers.Adam(learning_rate=0.00025)

        self.agent = self.getAgent()
        self.target_agent = self.getAgent()
        self.target_agent.set_weights(self.agent.get_weights())
        self.state_creator = state_creator

    def getAgent(self): #retrieves an agent (model)
        model = keras.Sequential()
        model.add(keras.Input(shape=(self.state_shape, )))
        model.add(keras.layers.Dense(50, activation='relu'))
        model.add(keras.layers.Dense(50, activation='relu'))
        model.add(keras.layers.Dense(self.action_shape, activation='softmax'))
        model.compile(loss = "mse", optimizer = self.optimizer)
        return model

    def getSolution(self, state): #gets an action from a state using an agent, with epsilon-greedy algorithm
        act = None
        if random.randrange(0, 1) <= self.epsilon:
            act =  np.random.choice(self.actions, 1, p=self.actiondistrib)
        else:
            tensor = np.array([state])
            result = self.agent.predict(tensor, verbose="0")
            max = result.argMax(1)
            act = max.buffer().values[0]
        return act

    #trains the model
    def train(self, sml, pyboy, stepper, batchsize = 900, episodes = 0, steps = 1000):

        global epsilon

        st = self.state_creator(self) #extracts a game state
        st2 = None
        epi = 0
        while epi < episodes or episodes <= 0: #for each episode
            
            print("Epoch "+str(epi)+" / "+str(episodes if episodes > 0 else "infinity")+" : epsilon "+str(self.epsilon))
            sml.reset_game() #set game to start state
            reward_mean = []
            reward = 0
            step = 0
            lastState = st
            previousprogress = sml.level_progress
            while step < steps:
                st2 = self.state_creator(self) #extract next state
                if sml.lives_left < 2 or st2 is None:
                    sml.reset_game()
                    continue
                act = self.getSolution(st)
                reward = stepper(act, previousprogress) #step in game
                reward_mean.append(reward)
                previousprogress = sml.level_progress
                
                #save data in a random spot of our database
                index = random.randint(0, len(self.dataset))
                self.dataset.insert(index, (st, reward, st2, act))

                st = st2 #go to next state
                step += 1
                print("Done step "+str(step)+"/"+str(steps)+" ("+str(round(step/float(steps)*100))+" %)", end="\r")
            print("\r")
                
            self.epsilon = max(0.1, self.epsilon*0.99) #decrement epsilon
            self.train_model(batchsize)

            if epi%3 == 0:
                self.target_agent.set_weights(self.agent.get_weights())
                pyboy.set_emulation_speed(1)
                tot_reward = 0
                stuckcount = 0
                sml.reset_game()
                state = self.state_creator(self) #extract initial game state
                previousprogress = sml.level_progress
                maxprogress = previousprogress
                lastact = None
                while True:
                    if state is None or None in state:
                        break
                    out = self.target_agent.predict(state, verbose="0") #use model to get action from current state
                    act = np.argmax(out)
                    if lastact is None or lastact != act:
                        print("Action performed : "+str(act))
                        lastact = act
                    reward = stepper(act, previousprogress) #ste in game and get reward
                    state = self.state_creator(self)
                    previousprogress = sml.level_progress
                    if previousprogress > maxprogress:
                        maxprogress = previousprogress
                    tot_reward += reward
                    if sml.lives_left < 2 or stuckcount >= 300: #if end condition met, exit play mode
                        break
                    if sml.level_progress <= maxprogress: #if no progress, increment kill counter
                        stuckcount+=1
                    else:
                        stuckcount=0
                
                pyboy.set_emulation_speed(0)
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

            self.agent.fit(state, target, epochs=1, verbose="0", callbacks=[self.savecallback, history])
            print("Learning "+str(i)+"/"+str(len(minibatch))+" ("+str(round(i/float(len(minibatch))*100))+" %)", end = "\r")
            i+=1
        print("\r")
        hlen = len(history.history["loss"])-1
        print("Mean loss : "+str(np.mean(history.history["loss"][hlen-batchsize:hlen])))