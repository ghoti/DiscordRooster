import shelve
from fuzzywuzzy import fuzz

class Trivia():
    def __init__(self):
        self.stats = shelve.open('triviastats')
        self.active = False
    def start(self):
        self.active = True
    def stop(self):
        self.active = False
    def is_active(self):
        return self.active
    def add_correct(self, user):
        if user in self.stats:
            self.stats[user] += 1
        else:
            self.stats[user] = 1
    def get_stats(self, user):
        if user in self.stats:
            return self.stats[user]
        else:
            return 0


