import math

class Console(object):
    """docstring for Console"""
    def __init__(self):
        super(Console, self).__init__()
        self.lines = []
        self.max = 15
        self.date = 0

    def update(self, date):
        self.date = date

    def print(self, s):
        minutes = (self.date*10)%60
        hours = math.floor((self.date*10)/60)%24
        days = math.floor(math.floor((self.date*10)/60)/24)

        lines = s.split('\n')

        # newlines = []
        self.lines.append("Day {} at {}:{}, {}".format(days, hours, minutes, lines[0]))

        for _s in lines[1:]:
            self.lines.append(_s)


        # self.lines.append(newline)
        if len(self.lines) > self.max:
            self.lines = self.lines[1:]
            
console = Console()