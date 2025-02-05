import pickle
import os
import barobets

def load(): 
    if not os.path.isfile("data/state.pickle"):
        # make fresh state and save it
        s = State()
        s.save()

    with open("data/state.pickle", "rb") as fp:
        s = pickle.load(fp)

        if not hasattr(s, "barobets"):
            s.barobets = []

        return s


class State:
    def __init__(self):
        self.players = {}
        self.barobets = []

    def save(self):
        with open("data/state.pickle", "wb") as fp:
            pickle.dump(self, fp)

    def get_player(self, userid):
        return self.players[userid]

    def add_player(self, userid, player):
        self.players[userid] = player
        self.save()

    def get_players(self):
        return self.players

    def add_barobet(self, barobet):
        self.barobets.append(barobet)
        self.save()
        return len(self.barobets) - 1

    def get_barobet(self, id=-1):
        return self.barobets[id]

    def del_barobet(self, id=-1):
        self.barobets[id] = None
