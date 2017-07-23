import curses
import curses.ascii
from string import printable


class Node:
    def main(self):
        curses.wrapper(self.init) # start running the program

    def init(self, screen):
        global PRINTABLE

        PRINTABLE = map(ord, printable)
        Y, X = screen.getmaxyx()
        height = Y - 1
        type = 0
        input = self.stdin_fixed(screen, height, type)


    def stdin_fixed(self, screen, height, type):
        global PRINTABLE

        screen.move(height, 0)
        screen.clrtoeol()
        if (type == 0):
            screen.addstr("Level1> ")
        elif (type == 1):
            screen.addstr("Level2> ")

        ERASE = self.stdin_fixed.ERASE = getattr(self.stdin_fixed, "erasechar", ord(curses.erasechar()))
        Y, X = screen.getyx()
        s = []
        while True:
            c = screen.getch()
            if c in (curses.ascii.LF, curses.ascii.CR, curses.KEY_ENTER):
                break
            elif c == ERASE or c == curses.KEY_BACKSPACE:
                y, x = screen.getyx()
                if x > X:
                    del s[-1]
                    screen.move(y, (x - 1))
                    screen.clrtoeol()
                    screen.refresh()
            elif c in PRINTABLE:
                s.append(chr(c))
                screen.addch(c)
            else:
                pass
        return "".join(s)

if __name__ == '__main__':
    node = Node()
    node.main() # run the instance