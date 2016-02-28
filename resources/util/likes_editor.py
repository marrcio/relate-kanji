import pygame, sys, traceback
import pygame.freetype
from pygame.locals import *
import toolbox as tb
from statistics import Statistics

WINDOWWIDTH = 640
X_CENTER = 320
WINDOWHEIGHT = 480
NEXT_FLAG = 1
EXIT_FLAG = -1
SUCCESS_FLAG = 0
RIGHT_FLAG = 2
LEFT_FLAG = 3
REDRAW_FLAGS = {SUCCESS_FLAG, LEFT_FLAG, RIGHT_FLAG}

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
        self.likes_font = pygame.freetype.SysFont('hanaminaregular', 40)
        self.small_font = pygame.freetype.SysFont('hanaminaregular', 30)
        self.num_font = pygame.freetype.SysFont('ipaexgothic', 30)
        self.background = pygame.Surface(self.screen.get_size()).convert()
        self.joined_d = Statistics().joined_d

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

    def write_kanji(self, kanji, i, pos):
        self.screen.blit(self.background,(0,0))
        self.write_at(kanji["k"], X_CENTER, 100, self.kanji_font, center=True)
        self.write_at(str(kanji["l"]), X_CENTER, 230, self.likes_font, center=True)
        arrow_parallel = self._create_arrow_parallel(kanji["l"], pos)
        self.write_at(str(arrow_parallel), X_CENTER, 290, self.likes_font, center=True)
        kanji_contents = kanji["c+"] if "c+" in kanji else kanji["c"]
        self.write_at(str(kanji_contents), X_CENTER, 350, self.small_font, center=True)
        related_kanji = self.joined_d[kanji["l"][pos]]
        related_contents = related_kanji["c+"] if "c+" in related_kanji else related_kanji["c"]
        self.write_at(str(related_contents), X_CENTER, 410,
                      self.small_font, center=True)
        self.write_at(str(i), 600, 460, self.num_font, center=True)

    def _create_arrow_parallel(self, look_a_likes, pos):
        arrow_parallel = [' '*len(x) for x in look_a_likes]
        arrow = '↑'
        arrow_parallel[pos] = arrow_parallel[pos][:-1] + arrow
        return arrow_parallel

class Controller:
    def __init__(self):
        self.movement_keys = {K_RIGHT, K_LEFT}
        self.deletion_keys = {K_BACKSPACE, K_DELETE}
        self.next_keys = {K_KP_ENTER, K_RETURN}
        self.exit_keys = {K_ESCAPE, K_q}

    def act(self, pressed_key, current_kanji, pos):
        if pressed_key in self.movement_keys:
            if pressed_key == K_RIGHT:
                return RIGHT_FLAG
            else:
                return LEFT_FLAG
        elif pressed_key in self.deletion_keys:
            current_kanji["l"].pop(pos)
            if pos != 0:
                return LEFT_FLAG
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
            if len(kanji["l"]) == 0:
                continue
            pos = 0
            self.screen.write_kanji(kanji, i+1, pos)
            next_kanji = False
            while not next_kanji:
                for event in pygame.event.get():
                    if event.type == QUIT:
                        self.exit_application()
                    elif event.type == KEYUP:
                        operation = self.controller.act(event.key, kanji, pos)
                        if operation == EXIT_FLAG:
                            self.exit_application()
                        elif operation == RIGHT_FLAG:
                            if pos + 1 < len(kanji["l"]):
                                pos += 1
                        elif operation == LEFT_FLAG:
                            if pos > 0:
                                pos -= 1
                        if operation == NEXT_FLAG or len(kanji["l"]) == 0:
                            next_kanji = True
                        if operation in REDRAW_FLAGS:
                            self.screen.write_kanji(kanji, i+1, pos)
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

