from tabnanny import verbose
import keras
import tensorflow as tf
import random
import numpy as np

epsilon = 1

def getAgent(state_shape, action_shape):
    learning_rate = 0.001
    init = tf.keras.initializers.HeUniform()
    model = keras.Sequential()
    model.add(keras.layers.Dense(24, input_shape=state_shape, activation='relu', kernel_initializer = init))
    model.add(keras.layers.Dense(12, activation='relu', kernel_initializer=init))
    model.add(keras.layers.Dense(action_shape, activation='linear', kernel_initializer=init))
    model.compile(loss=tf.keras.losses.Huber(), optimizer=tf.keras.optimizers.Adam(learning_rate=learning_rate), metrics=['accuracy'])
    return model

def getSolution(agent : keras.Sequential, state, actions):
    result = []
    if random.randrange(0, 1) <= epsilon:
        choices =  random.choices(actions)
        result = [1 if x in choices else 0 for x in actions]
    else:
        result : agent.predict(state)
        resActions = []
        best = None
        bestres = 0
        for i in range(len(result)):
            if best is None or result[i] > bestres:
                best = i
                bestres = result[i]
        resActions.append(best)
        for i in range(len(result)):
            if abs(result[i] - bestres) < 0.1:
                resActions.append(i)
        result = [1 if x in resActions else 0 for x in actions]
    return result

            

def train(replay_memory, model, target_model):
    learning_rate = 0.7 # Learning rate
    discount_factor = 0.618

    MIN_REPLAY_SIZE = 1000
    if len(replay_memory) < MIN_REPLAY_SIZE:
        return

    batch_size = 64 * 2
    mini_batch = random.sample(replay_memory, batch_size)
    current_states = np.array([transition[0] for transition in mini_batch])
    current_qs_list = model.predict(current_states, verbose=0)
    new_current_states = np.array([transition[3] for transition in mini_batch])
    future_qs_list = target_model.predict(new_current_states, verbose=0)

    X = []
    Y = []
    for index, (observation, actions, reward, new_observation) in enumerate(mini_batch):
        max_future_q = reward + discount_factor * np.max(future_qs_list[index])

        current_qs = current_qs_list[index]
        for action in actions:
            current_qs[action] = (1 - learning_rate) * current_qs[action] + learning_rate * max_future_q

        X.append(observation)
        Y.append(current_qs)
    model.fit(np.array(X), np.array(Y), batch_size=batch_size, verbose=0, shuffle=True)

