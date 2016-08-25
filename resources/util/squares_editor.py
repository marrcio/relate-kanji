import pygame, sys, traceback
import pygame.freetype
from pygame.locals import *
import toolbox as tb

WINDOWWIDTH = 640
X_CENTER = 320
WINDOWHEIGHT = 480
NEXT_FLAG = 1
EXIT_FLAG = -1
SUCCESS_FLAG = 0

BOOK = '../data/jouyou_kanji.json'
# BOOK = '../data/radicals.json'

#            R    G    B
WHITE    = (255, 255, 255)
BLACK    = (  0,   0,   0)

class Screen:
    def __init__(self):
        self.screen = pygame.display.set_mode((WINDOWWIDTH, WINDOWHEIGHT))
        pygame.display.set_caption('Kanji Squares Editor')
        self.kanji_font = pygame.freetype.SysFont('ipaexgothic', 150)
        self.components_font = pygame.freetype.SysFont('hanaminaregular', 40)
        self.num_font = pygame.freetype.SysFont('ipaexgothic', 30)
        self.background = pygame.Surface(self.screen.get_size()).convert()

    def write_at(self, message, pos_x, pos_y, font, center=False):
        mark = font.render(message, fgcolor=WHITE)
        surf, mark_rect = mark
        if center:
            mark_rect.centerx = pos_x
            mark_rect.centery = pos_y
        else:
            mark_rect.left = pos_x
            mark_rect.top = pos_y
        self.screen.blit(surf, mark_rect)
        pygame.display.flip()

    def write_kanji(self, kanji, i):
        self.screen.blit(self.background,(0,0))
        self.write_at(kanji["k"], X_CENTER, 100, self.kanji_font, center=True)
        self.write_at(str(kanji["c"]), X_CENTER, 250, self.components_font, center=True)
        self.write_at(str(kanji["s"]), X_CENTER, 330, self.components_font, center=True)
        self.write_at(str(i), 600, 460, self.num_font, center=True)

class Controller:
    def __init__(self):
        self.insertion_map = {K_RIGHT: "⿰", K_DOWN: "⿱", K_KP_PLUS: "⿻",
                              K_KP_MULTIPLY: "⿲", K_KP_DIVIDE: "⿳", K_KP5: "⿴",
                              K_KP2: "⿵", K_KP8: "⿶", K_KP6: "⿷", K_KP3: "⿸",
                              K_KP1: "⿹", K_KP9: "⿺"}
        self.deletion_keys = {K_BACKSPACE, K_DELETE}
        self.next_keys = {K_KP_ENTER, K_RETURN}
        self.exit_keys = {K_ESCAPE, K_q}

    def act(self, pressed_key, current_kanji):
        if pressed_key in self.insertion_map.keys():
            current_kanji["s"].append(self.insertion_map[pressed_key])
        elif pressed_key in self.deletion_keys:
            if len(current_kanji["s"]) > 0:
                current_kanji["s"].pop()
        elif pressed_key in self.next_keys:
            return NEXT_FLAG
        elif pressed_key in self.exit_keys:
            return EXIT_FLAG
        return SUCCESS_FLAG

class Model:
    def __init__(self):
        self.kanjis = tb.load_data_safe(BOOK)

class Editor:
    def __init__(self):
        pygame.init()
        self.screen = Screen()
        self.controller = Controller()
        self.model = Model()

    def enter_editor_loop(self, start=0):
        for i, kanji in enumerate(self.model.kanjis):
            if i < start:
                continue
            # if len(kanji["c"]) == 0:
            #     kanji["s"] = []
            #     continue
            if len(kanji["c"]) == 0 or len(kanji["c"]) == len(kanji["s"])+1:
                continue
            self.screen.write_kanji(kanji, i+1)
            next_kanji = False
            while not next_kanji:
                for event in pygame.event.get():
                    if event.type == QUIT:
                        self.exit_application()
                    elif event.type == KEYUP:
                        operation = self.controller.act(event.key, kanji)
                        if operation == EXIT_FLAG:
                            self.exit_application()
                        elif operation == NEXT_FLAG:
                            # if (len(kanji["c"]) == len(kanji["s"]) + 1 or
                            #     len(kanji["c"]) == len(kanji["s"]) == 0):
                            next_kanji = True
                        elif operation == SUCCESS_FLAG:
                            self.screen.write_kanji(kanji, i+1)
        self.exit_application()


    def exit_application(self):
        pygame.quit()
        tb.save_data(self.model.kanjis, BOOK)
        sys.exit()


if __name__ == "__main__":
    try:
        e = Editor()
        start = int(sys.argv[1]) if len(sys.argv) > 1 else 0
        e.enter_editor_loop(start)
    except Exception:
        traceback.print_exc()
    finally:
        e.exit_application()

