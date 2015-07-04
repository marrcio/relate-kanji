import toolbox
import xml.etree.ElementTree as ET

class Statistics:
    JOYOU_PATH = '../data/joyou_kanji.json'
    RAW_WORDS_PATH = '../data/word_count.csv'
    WORDS_FILTERED = '../data/word_count_filtered.csv' # Words with joyou kanji
    WORDS_DOUBLE_FILTERED = '../data/word_count_double_filtered.csv' # used as examples entries
    WORDS_FILTERED_IN_DICT = '../data/word_count_filtered_in_jmdict.csv' # filtered and on jmdict
    WORDS_FILTERED_IN_NAMES = '../data/word_count_filtered_in_jmnedict.csv'
    JMDICT_PATH = '../data/JMdict_e'
    EXAMPLE_WORDS = '../data/example_words.csv'
    JMDICT_RELEVANT = '../data/jmdict_relevant.json'
    KANJI_AND_EXAMPLES = '../data/kanji_and_examples.json'

    def __init__(self):
        self.minimal_set_up()

    def minimal_set_up(self):
        self.jk = toolbox.load_data(Statistics.JOYOU_PATH)
        self.jk_set = set((k['kanji'] for k in self.jk))

    def filter_word_count(self):
        holder = []
        for entry in toolbox.load_data(Statistics.RAW_WORDS_PATH, iterable=True):
            if any(char in self.jk_set for char in entry[1]):
                holder.append(entry)
        return holder

    def get_kanji_examples(self, source='../data/word_count_filtered.csv'):
        kanji_examples = { k: {'words': [], 'value': 0} for k in self.jk_set}
        for entry in toolbox.load_data(source, iterable=True):
            for letter in entry[1]:
                if letter in self.jk_set:
                    kanji_examples[letter]['words'].append((entry[1], int(entry[0])))
                    kanji_examples[letter]['value'] += int(entry[0])
        kanji_examples = sorted(kanji_examples.items(), key=lambda x: -x[1]['value'])
        for kanji in kanji_examples:
            kanji[1]['words'] = sorted(kanji[1]['words'], key=lambda x: -x[1])
        return kanji_examples

    def get_refined_kanji_examples(self, percent_hold=0.95, num_hold=5, num_max=50,
                                   get_map=False):
        unrefined = self.get_kanji_examples()
        jmdict_set = set(x[1] for x in toolbox.load_data(Statistics.WORDS_FILTERED_IN_DICT))
        names_set = set(x[1] for x in toolbox.load_data(Statistics.WORDS_FILTERED_IN_NAMES))
        if get_map:
            words_map = {word[1]:False
                         for word in toolbox.load_data(Statistics.WORDS_FILTERED_IN_DICT)}
            names_map = {word[1]:False
                         for word in toolbox.load_data(Statistics.WORDS_FILTERED_IN_NAMES)}
        for k,v in unrefined:
            accum_percent = 0
            accum_num = 0
            holder = []
            hold = v['value']*percent_hold
            it = iter(v['words'])
            while (accum_percent < hold or accum_num < num_hold) and (accum_num < num_max):
                try:
                    word_value = next(it)
                    if word_value[0] in jmdict_set or word_value[0] in names_set:
                        accum_percent += word_value[1]
                        accum_num += 1
                        holder.append(word_value)
                        if get_map:
                            if word_value[0] in jmdict_set:
                                words_map[word_value[0]]=True
                            else:
                                names_map[word_value[0]]=True
                except StopIteration:
                    break
            v['words'] = holder
        if get_map:
            return unrefined, words_map, names_map
        else:
            return unrefined

    def get_dict_references(self, source='../data/word_count_filtered.csv'):
        words_set = set(x[1] for x in toolbox.load_data(source))
        useful_entry_set = set()
        words_ref = {word:[] for word in words_set}
        root = ET.parse(Statistics.JMDICT_PATH).getroot()
        for entry in root.findall('./entry'):
            for keb in entry.findall('.//keb'):
                if keb.text in words_set:
                    ent_seq = int(entry.find('./ent_seq').text)
                    useful_entry_set.add(ent_seq)
                    words_ref[keb.text].append(ent_seq)
        return useful_entry_set, words_ref
