class Ballot_Box():
    def __init__(self):
        self.running = False
        self.yes = 0
        self.no = 0
        self.votedlist = []
    def started(self):
        self.running = True
    def stopped(self):
        self.running = False
    def alive(self):
        return self.running
    def voteyes(self):
        self.yes += 1
    def voteno(self):
        self.no += 1
    def results(self):
        return self.yes, self.no
    def reset(self):
        self.yes = 0
        self.no = 0
        self.votedlist = []
    def voted(self, name):
        self.votedlist.append(name)
    def has_voted(self, name):
        if self.votedlist.count(name):
            return False
        else:
            return True