import toolbox
import xml.etree.ElementTree as ET

from collections import namedtuple, defaultdict, Counter

Example = namedtuple('Example', ['word', 'freq'])

class Statistics:
    JOUYOU_PATH = '../data/jouyou_kanji.json'
    RADICALS_PATH = '../data/radicals.json'
    RAW_WORDS_PATH = '../data/word_count.csv'
    WORDS_FILTERED = '../data/word_count_filtered.csv' # Words with joyou kanji
    WORDS_TEACHEABLE = '../data/word_count_teacheable.csv'
    WORDS_FILTERED_IN_DICTS = '../data/word_count_filtered_in_dicts.csv' # On some dict
    EXAMPLE_WORDS = '../data/example_words.csv'
    KANJI_AND_EXAMPLES = '../data/kanji_and_examples.json'

    def __init__(self):
        self.minimal_set_up()

    def minimal_set_up(self):
        self.jk = toolbox.load_data(Statistics.JOUYOU_PATH)
        self.jk_set = set(k['k'] for k in self.jk)
        self.hira_kata = set(chr(x) for x in range(ord('\u3041'), ord('\u30ff')))
        self.rads = toolbox.load_data(Statistics.RADICALS_PATH)
        self.jk_d = toolbox.dict_by_field(self.jk, 'k')
        self.rads_d = toolbox.dict_by_field(self.rads, 'k')
        self.joined_d = dict()
        self.joined_d.update(self.jk_d)
        self.joined_d.update(self.rads_d)


    def reload(self):
        self.minimal_set_up()


    def filter_word_count(self):
        holder = []
        for entry in toolbox.load_data(Statistics.RAW_WORDS_PATH, iterable=True):
            if any(char in self.jk_set for char in entry[1]):
                holder.append(entry)
        return holder


    def get_kanji_examples(self):
        kanji_examples = { k: {'words': [], 'value': 0} for k in self.jk_set}
        for entry in toolbox.load_data(Statistics.WORDS_FILTERED, iterable=True):
            for letter in entry[1]:
                if letter in self.jk_set:
                    kanji_examples[letter]['words'].append(Example(word=entry[1],
                                                           freq=int(entry[0])))
                    kanji_examples[letter]['value'] += int(entry[0])
        kanji_examples = sorted(kanji_examples.items(), key=lambda x: -x[1]['value'])
        for kanji in kanji_examples:
            kanji[1]['words'] = sorted(kanji[1]['words'], key=lambda x: -x[1])
        return kanji_examples


    def get_refined_kanji_examples(self, percent_hold=0.80, num_hold=5, num_max=50):
        unrefined = self.get_kanji_examples()
        dicts_set = set(x[1] for x in toolbox.load_data(Statistics.WORDS_FILTERED_IN_DICTS))
        for k,v in unrefined:
            accum_percent = 0
            accum_num = 0
            holder = []
            hold = v['value']*percent_hold
            it = iter(v['words'])
            while (accum_percent < hold or accum_num < num_hold) and (accum_num < num_max):
                try:
                    word_value = next(it)
                    if word_value.word in dicts_set:
                        accum_percent += word_value.freq
                        accum_num += 1
                        holder.append(word_value)
                except StopIteration:
                    break
            v['words'] = holder
        return unrefined


    def estimate_examples_cdfs(self, granularity=0.05, stop=0.95):
        unrefined = self.get_kanji_examples()
        dicts_set = set(x[1] for x in toolbox.load_data(Statistics.WORDS_FILTERED_IN_DICTS))

        for kanji, details in unrefined:
            details["distribution"] = []
            accum = 0
            for example in details["words"]:
                if example.word in dicts_set:
                    accum += example.freq
                    true_freq = accum/details['value']
                    gran_freq = round(round(true_freq/granularity)*granularity, 2)
                    details["distribution"].append(gran_freq)
                    if gran_freq >= stop:
                        break
        return unrefined

    def estimate_number_necessary_for_stop(self, stop=0.95):
        ks = self.estimate_examples_cdfs(stop=stop)
        ds = []
        for kanji, detail in ks:
            ds.append(detail['distribution'])
        c = Counter(len(d) for d in ds)
        for metric in range(10, 100+1, 10):
            print("%3d Examples: %4d" % (
                  metric,
                  sum(count for x, count in c.items() if x <= metric)))


    def analyze_kanji_hierarchy(self, result_file = '../data/kanji_hierarchy.json'):
        """Find kanjis that share part of or the whole of their c+ condensed form"""
        result = defaultdict(list)
        # First pass: puts each kanji as the first in its contents list of components
        for kanji, details in self.joined_d.items():
            components = details['c+'] if 'c+' in details else details['c']
            squares = details['s+'] if 's+' in details else details['s']
            condensed = toolbox.condensate_contents(components, squares)
            if condensed not in self.joined_d: # The case of composed components
                result[condensed].append(kanji)
        result.pop('', None)
        # Second pass: puts subgroups in the same place
        for kanji, details in self.joined_d.items():
            components = details['c+'] if 'c+' in details else details['c']
            squares = details['s+'] if 's+' in details else details['s']
            condensed = toolbox.condensate_contents(components, squares)
            for subgroup in toolbox.get_contents_subgroups(components, squares):
                if (subgroup in result and
                    kanji not in result[subgroup] and
                    not any([letter in details and
                         self.joined_d[result[subgroup][0]]['k'] in details[letter]
                         for letter in ('c', 'cc', 'c+', 'alt', 'l')])):
                    result[subgroup].append(kanji)
        result = [dict([(k,v)]) for k,v in result.items() if len(v) > 1]
        toolbox.save_data(result, result_file)

    def create_components_map(self):
        result = defaultdict(list)
        # First pass: puts each kanji as the first in its contents list of components
        for kanji, details in self.joined_d.items():
            if 'c+' in details:
                condensed = toolbox.condensate_contents(details['c+'], details['s+'])
            else:
                condensed = toolbox.condensate_contents(details['c'], details['s'])
            result[condensed].append(kanji)
        result.pop('', None)
        result2 = {k:v[0] for k,v in result.items()}
        return result2

    def analyze_repeated_groups(self, result_file = '../data/kanji_hierarchy.json'):
        components_map = self.create_components_map()
        result = defaultdict(list)
        for kanji, details in self.joined_d.items():
            components = details['c+'] if 'c+' in details else details['c']
            squares = details['s+'] if 's+' in details else details['s']
            condensed = toolbox.condensate_contents(components, squares)
            for subgroup in toolbox.get_contents_subgroups(components, squares):
                if subgroup not in self.joined_d: # already known subgroup
                    if not (subgroup in components_map and  # already listed as a subcomponent
                            components_map[subgroup] in details['c']):
                        result[subgroup].append(kanji)
        result = {k: sorted(set(v)) for k,v in result.items() if len(set(v)) > 1}
        reverse = defaultdict(list)
        for k,v in result.items():
            reverse[tuple(v)].append(k)
        reverse = {k:sorted(v, key=lambda x: -len(x)) for k,v in reverse.items() if len(v) > 1}
        for k,v in reverse.items():
            for elem in v[1:]:
                result.pop(elem, None)
        for k,v in result.items():
            v_set = set(v)
            new_v = []
            for item in v:
                if (v_set & (set(self.joined_d[item]['c']) |
                             set(self.joined_d[item]['cc']))) == set():
                    new_v.append(item)
            v = new_v
            result[k] = v
        result = [(k, v) for k,v in result.items() if len(v) > 1]
        result = sorted(result, key=lambda x: (len(x[0]), len(x[1])))
        result = [{k:v} for (k,v) in result]
        toolbox.save_data(result, result_file)
