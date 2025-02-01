import pickle
import os

def load(): 
    if not os.path.isfile("data/state.pickle"):
        # make fresh state and save it
        s = State()
        s.save()

    with open("data/state.pickle", "rb") as fp:
        return pickle.load(fp)


class State:
    def __init__(self):
        self.players = {}

    def save(self):
        with open("data/state.pickle", "wb") as fp:
            pickle.dump(self, fp)

    def get_player(self, userid):
        return self.players[userid]

    def add_player(self, userid, player):
        self.players[userid] = player
        self.save()

    def get_players(self):
        self.players