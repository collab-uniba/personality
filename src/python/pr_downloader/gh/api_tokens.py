import random
import os


class Tokens:
    def __init__(self):
        self.tokens = []
        with open(os.path.join(os.getcwd(), 'gh/github-api-tokens.txt'), 'r') as tokens:
            for t in tokens:
                self.tokens.append(t.strip())
        random.shuffle(self.tokens)

    def length(self):
        return len(self.tokens)

    def iterator(self):
        return iter(self.tokens)
