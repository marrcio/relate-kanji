import toolbox
import xml.etree.ElementTree as ET

from structures import IP, IS
from collections import namedtuple, defaultdict, Counter

class Statistics:

    def estimate_examples_cdfs(self, granularity=0.05, stop=0.95):
        unrefined = toolbox.get_kanji_examples()
        dicts_set = set(x[1] for x in toolbox.load_data(IP.WORDS_FILTERED_IN_DICTS))

        for kanji, details in unrefined.items():
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
        """Print in screen the number of kanjis satisfied with each range of number of examples."""
        ks = self.estimate_examples_cdfs(stop=stop)
        ds = []
        for kanji, detail in ks.items():
            ds.append(detail['distribution'])
        c = Counter(len(d) for d in ds)
        for metric in range(1, 10):
            print("%3d Examples: %4d" % (
                  metric,
                  sum(count for x, count in c.items() if x <= metric)))
        for metric in range(10, 100+1, 10):
            print("%3d Examples: %4d" % (
                  metric,
                  sum(count for x, count in c.items() if x <= metric)))


    def analyze_kanji_hierarchy(self, result_file = '../data/kanji_hierarchy.json'):
        """Find kanjis that share part of or the whole of their components."""
        result = defaultdict(list)
        # First pass: puts each kanji as the first in its contents list of components
        for kanji, details in IS.joined_d.items():
            components = details['c+'] if 'c+' in details else details['c']
            squares = details['s+'] if 's+' in details else details['s']
            condensed = toolbox.condensate_contents(components, squares)
            if condensed not in IS.joined_d: # The case of composed components
                result[condensed].append(kanji)
        result.pop('', None)
        # Second pass: puts subgroups in the same place
        for kanji, details in IS.joined_d.items():
            components = details['c+'] if 'c+' in details else details['c']
            squares = details['s+'] if 's+' in details else details['s']
            condensed = toolbox.condensate_contents(components, squares)
            for subgroup in toolbox.get_contents_subgroups(components, squares):
                if (subgroup in result and
                    kanji not in result[subgroup] and
                    not any([letter in details and
                         IS.joined_d[result[subgroup][0]]['k'] in details[letter]
                         for letter in ('c', 'cc', 'c+', 'alt', 'l')])):
                    result[subgroup].append(kanji)
        result = [dict([(k,v)]) for k,v in result.items() if len(v) > 1]
        toolbox.save_data(result, result_file)

    def create_components_map(self):
        result = defaultdict(list)
        # First pass: puts each kanji as the first in its contents list of components
        for kanji, details in IS.joined_d.items():
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
        for kanji, details in IS.joined_d.items():
            components = details['c+'] if 'c+' in details else details['c']
            squares = details['s+'] if 's+' in details else details['s']
            condensed = toolbox.condensate_contents(components, squares)
            for subgroup in toolbox.get_contents_subgroups(components, squares):
                if subgroup not in IS.joined_d: # already known subgroup
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
                if (v_set & (set(IS.joined_d[item]['c']) |
                             set(IS.joined_d[item]['cc']))) == set():
                    new_v.append(item)
            v = new_v
            result[k] = v
        result = [(k, v) for k,v in result.items() if len(v) > 1]
        result = sorted(result, key=lambda x: (len(x[0]), len(x[1])))
        result = [{k:v} for (k,v) in result]
        toolbox.save_data(result, result_file)
