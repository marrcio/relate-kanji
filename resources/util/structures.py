import toolbox

class ImportantPaths(object):
    JOUYOU_PATH = '../data/jouyou_kanji.json'
    RADICALS_PATH = '../data/radicals.json'
    RAW_WORDS_PATH = '../data/word_count.csv'
    WORDS_FILTERED = '../data/word_count_filtered.csv' # Words with joyou kanji
    WORDS_TEACHEABLE = '../data/word_count_filtered_teachable.csv'
    WORDS_FILTERED_IN_DICTS = '../data/word_count_filtered_in_dicts.csv' # On some dict
    WORDS_IN_DICT_SET = '../data/words_in_dicts.csv'
    WORDS_ESSENTIAL = '../data/essential_words.csv'
    KANJI_AND_EXAMPLES = '../data/kanji_and_examples.json'
    JINMEIYOU_PATH = '../data/jinmeiyou_kanji.txt'

    JMDICT_XML = '../data/JMdict_e.xml'
    JMDICT_BASE = '../data/jmdict.json'
    JMDICT_CLEAN = '../data/jmdict_clean.json'
    JMDICT_ESSENTIAL = '../data/jmdict_essential.json'
    JMDICT_UNWINDED = '../data/jmdict_unwinded.json'

    JMNEDICT_XML = '../data/JMnedict.xml'
    JMNEDICT_BASE = '../data/jmnedict.json'
    JMNEDICT_CLEAN = '../data/jmnedict_clean.json'
    JMNEDICT_ESSENTIAL = '../data/jmndeict_essential.json'

    EQUIVALENTS = '../data/equivalents.json'


IP = ImportantPaths()


class ImportantStructures(object):

    def __init__(self):
        self.set_up()

    def set_up(self):
        self.jk = toolbox.load_data(IP.JOUYOU_PATH)
        self.jk_set = set(k['k'] for k in self.jk)
        self.jinmeiyou_set = set(toolbox.load_data(IP.JINMEIYOU_PATH)[0])
        self.equivalents_set = set(toolbox.load_data(IP.EQUIVALENTS)[0].values())
        self.accetable_set = self.jk_set | self.jinmeiyou_set | self.equivalents_set | {'々'}
        self.hira_kata = set(chr(x) for x in range(ord('\u3041'), ord('\u30ff')))
        self.rads = toolbox.load_data(IP.RADICALS_PATH)
        self.jk_d = toolbox.dict_by_field(self.jk, 'k')
        self.rads_d = toolbox.dict_by_field(self.rads, 'k')
        self.joined_d = dict()
        self.joined_d.update(self.jk_d)
        self.joined_d.update(self.rads_d)

    def reload(self):
        self.set_up()


IS = ImportantStructures()
