import time
import config
from env import *
import numpy as np
from tqdm import tqdm
import tensorflow as tf


class Game:
    """
    Game class with corresponding functionalities
    Attributes:
        state (np.array): 
    """

    def __init__(self):
        self.state = np.array((0, 0, 0, 0)).reshape((1, 4))

    def generate_data(self, nb_episodes):
        """
        generate data over nb_episodes with user play
        Args:
            nb_episodes (int): number of episodes will be used to generate data
        """
        score_requirement = -200
        training_data = []
        accepted_scores = []

        for game_index in tqdm(range(nb_episodes)):
            # reset environment
            player = Player()
            player.init_player()
            player.init_food()
            player.score = 0
            score = 0
            game_memory = []
            game_score = 0
            prev_state = []
            prev_distance = 1000
            for step_index in range(1000):
                state = [player.px, player.py, player.food_x, player.food_y]
                new_state, action, game_score = player.preprocessing()
                if len(prev_state) > 0:
                    game_memory.append([prev_state, action])
                prev_state = new_state

                if game_score != 0:
                    reward = 100
                    break
                else:
                    reward = -5
                score += reward

            if score >= score_requirement:
                accepted_scores.append(score)
                for data in game_memory:
                    # one hot encoding
                    if data[1] == 0:
                        output = [1, 0, 0, 0]
                    elif data[1] == 1:
                        output = [0, 1, 0, 0]
                    elif data[1] == 2:
                        output = [0, 0, 1, 0]
                    elif data[1] == 3:
                        output = [0, 0, 0, 1]
                    training_data.append([data[0], output])

        training_data_save = np.array(training_data)
        np.save(config.DATA_PATH,
                training_data_save, allow_pickle=True)
        print(accepted_scores)
        return training_data

    def train(self, training_data_path):
        """
        train model over over generated data
        Args:
            training_data_path (str): path of generated data obtained during user play.
        """
        training_data = np.load(training_data_path)
        model = tf.keras.models.Sequential([
            tf.keras.layers.Dense(64, input_shape=(4,), activation='relu'),
            tf.keras.layers.Dense(64, activation='relu'),
            tf.keras.layers.Dense(4, activation='softmax')])
        model.compile(loss='categorical_crossentropy',
                      optimizer=tf.keras.optimizers.Adam(lr=0.001))

        X = np.array([i[0] for i in training_data]
                     ).reshape(-1, len(training_data[0][0]))
        y = np.array([i[1] for i in training_data]
                     ).reshape(-1, len(training_data[0][1]))
        model.fit(X, y, epochs=config.EPOCHS)
        model.save(config.MODEL_PATH)
        return model

    def render(self, player):
        """
        rendering environment
        Args:
            player (class Player): player object 
        """
        episode_env = player.env.copy()
        cv2.circle(episode_env, (player.food_x, player.food_y),
                   5, (255, 255, 255), 5)
        cv2.circle(episode_env, (player.px, player.py),
                   5, (255, 255, 255), 1)
        cv2.putText(episode_env, "score" + str(player.score),
                    (20, 30), 1, cv2.FONT_HERSHEY_DUPLEX, (255, 255, 255), 1)
        cv2.imshow("env", episode_env)
        key = cv2.waitKey(1)
        if key == 27:
            # user pressed 'esc'
            exit(0)

    def game_run(self, model_path=None):
        """
        runing game with neural network model
        Args:
            model_path (str): path of trained model
        """

        player = Player()
        player.init_food()
        player.init_player()
        if model_path:
            model = tf.keras.models.load_model(model_path)
        else:
            model = tf.keras.models.load_model(config.MODEL_PATH)

        while True:
            # rendering
            self.render(player)

            state = [player.px, player.py, player.food_x, player.food_y]
            player.run(state, model)
            if player.done is True:
                time.sleep(5)
                exit(0)
            time.sleep(0.05)
