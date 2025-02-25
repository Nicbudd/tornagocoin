"""Global state tracking for entire bot."""

import pickle
import os

PICKLE_PATH = "data/state.pickle"

def load():
    """Loads the state from the file.
    If the file does not exist, it makes a new state and saves it."""

    if not os.path.isfile(PICKLE_PATH):
        # make fresh state and save it
        s = State()
        s.save()

    with open(PICKLE_PATH, "rb") as fp:
        s = pickle.load(fp)

        # s.barobets = {}
        if not hasattr(s, "barobets"):
            s.barobets = {}

        if not hasattr(s, "last_barobet_id"):
            s.last_barobet_id = 0

        return s


class State:
    """Global state tracking for entire bot.
    Saves state to pickle file for loading later."""
    def __init__(self):
        """DO NOT USE! Use global_state.load() instead"""
        self.players = {}
        self.barobets = {}
        self.last_barobet_id = 0

    def save(self):
        """Saves the state to the pickle file."""
        with open(PICKLE_PATH, "wb") as fp:
            pickle.dump(self, fp)

    def get_player(self, player_id: int):
        """Returns a player based on their userid."""
        return self.players[player_id]

    def add_player(self, player_id: int, player):
        """Adds new player."""
        self.players[player_id] = player
        self.save()

    def del_user(self, player_id: int):
        """Deletes the player, selling off all of their assets."""
        if player_id in self.players.values():
            p = self.players[player_id]
            for stock in p.stocks:
                stock.sell()
            del p
            return True
        else:
            return False

    def get_players(self):
        """Gets entire list of players."""
        return self.players

    def add_barobet(self, barobet) -> int:
        """Adds new barobet to the list. Returns the id of the item."""
        self.last_barobet_id += 1
        self.barobets[self.last_barobet_id] = barobet
        self.save()
        return self.last_barobet_id

    def get_barobet(self, game_id: int = -1):
        """Adds new barobet to the list."""
        if game_id == -1:
            game_id = self.last_barobet_id
        return self.barobets[game_id]

    def del_barobet(self, game_id: int = -1):
        """Deletes the barobet game and sets the game number in the list to None."""
        if game_id == -1:
            game_id = self.last_barobet_id
        del self.barobets[game_id]
