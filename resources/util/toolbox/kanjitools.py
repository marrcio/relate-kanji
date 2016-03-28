import re
import xml.etree.ElementTree as ET
import collections
import romkan
import itertools
import toolbox
import xmltodict
import json
import functools
from statistics import Statistics
from collections import deque
from toolbox.filetools import save_data, load_data, pipe_transform
from collections import Counter, defaultdict
from pathlib import Path

hiragana_range = re.compile(r'[\u3040-\u309F]')
katakana_range = re.compile(r'[\u30a0-\u30ff]')

jmkanji = None
jmdict = None

def setup_kanjidic():
    global jmkanji
    jmkanji = ET.parse('../data/kanjidic2.xml').getroot()

def get_dict_index(kanji, dict_name='henshall'):
    if jmkanji is None:
        setup_kanjidic()
    e  = jmkanji.find(".//*[literal='" + kanji + "']").find("./dic_number/dic_ref[@dr_type='" +
                                                         dict_name + "']")
    if e is not None:
        return int(e.text)
    else:
        return -1

def filter_jdict(dict_path, output_path):
    """Transform the original XML dict in a resumed json only with 'teachable' words."""
    def _jdict_to_file(_, entry, words, f):
        if 'k_ele' in entry:
            if type(entry['k_ele']) != list:
                entry['k_ele'] = [entry['k_ele']]
            if any(x['keb'] in words for x in entry['k_ele']):
                f.write(json.dumps(entry, ensure_ascii=False, sort_keys=True))
                f.write('\n')
        return True
    S = Statistics()
    wc_f = toolbox.load_data('../data/word_count_filtered_teachable.csv')
    words = set(word[1] for word in wc_f)
    f = open(output_path, 'w')
    callback = functools.partial(_jdict_to_file, words=words, f=f)
    xmltodict.parse(open(dict_path, 'rb'), item_depth=2, item_callback=callback)
    f.close()

def double_filter_jdict(dict_path, output_path):
    """Further resume the json by only adding example words."""
    essential = set(x[0] for x in toolbox.load_data('../data/essential_words.csv'))
    with open(output_path, 'w') as f:
        for entry in toolbox.load_data(dict_path, iterable=True):
            if any(x['keb'] in essential for x in entry['k_ele']):
                f.write(json.dumps(entry, ensure_ascii=False, sort_keys=True))
                f.write('\n')


def filter_word_count_teachable(input_path='../data/word_count_filtered.csv',
                                 output_path='../data/word_count_filtered_teachable.csv'):
    """Separate only the count, word pairs in which all the characters of the word are either
    Jouyou Kanji or Hiragana/Katakana."""
    wc = toolbox.load_data(input_path)
    S = Statistics()
    def is_wanted(x):
        return x in S.jk_set or x in S.hira_kata
    wc_f = [x for x in wc if all(is_wanted(c) for c in x[1])]
    toolbox.save_data(wc_f, output_path)

def filter_word_count_with_definition(input_path='../data/word_count_filtered_teachable.csv',
                                      output_path='../data/word_count_filtered_in_dicts.csv'):
    """Filter the word count so that it only contains words that exist in one of the dicts."""
    words_in_dict = set(word[0] for word in toolbox.load_data('../data/words_in_dicts.csv'))
    in_words = toolbox.load_data(input_path)
    out_words = [count_word for count_word in in_words if count_word[1] in words_in_dict]
    toolbox.save_data(out_words, output_path)

def filter_jmndict_name_types(input_path='../data/jmndict.json',
                              output_path='../data/jmndict_filtered.json'):
    wanted_fields = {'place name',
                     'company name',
                     'railway station',
                     'organization name',
                     'full name of a particular person',
                     'product name',
                     'work of art, literature, music, etc. name'}
    def filter_wanted(entry, wanted_fields):
        return any(name_type in wanted_fields for trans in entry['trans']
                   for name_type in trans['name_type'])

    toolbox.pipe_filter(input_path, output_path,
                        functools.partial(filter_wanted, wanted_fields=wanted_fields))

def _investigate_types(path, entry, results_dict):
    if not isinstance(entry, collections.Mapping):
        return
    for k, v in entry.items():
        results_dict[path + (k,)].add(type(v))
        if type(v) == list:
            for elem in v:
                _investigate_types(path + (k,), elem, results_dict)
        else:
            _investigate_types(path + (k,), v, results_dict)

def _correct_problematic_dicts(entry, path):
    if len(path) == 1:
        if path[0] in entry and type(entry[path[0]]) != list:
            entry[path[0]] = [entry[path[0]]]
    else:
        if path[0] in entry:
            relevant = entry[path[0]]
            # The structure is at most one list > one problematic dict.
            if type(relevant) == list:
                for elem in relevant:
                    _correct_problematic_dicts(elem, path[1:])
            else:
                _correct_problematic_dicts(relevant, path[1:])

def get_types_investigation(input_path):
    entries = toolbox.load_data(input_path)
    results = defaultdict(set)
    for entry in entries:
        _investigate_types(tuple(), entry, results)
    return entries, dict(results)

def uniformize(input_path, output_path):
    entries, results = get_types_investigation(input_path)
    problem_paths = [k for k, v in results.items() if list in v and len(v) > 1]
    for entry in entries:
        for path in problem_paths:
            _correct_problematic_dicts(entry, path)
    toolbox.save_data(entries, output_path)



def update_radicals_counter(book='../../../Copy/smallest_book.json',
                            rads_file='../../../Copy/radicals.txt',
                            rads_book='../../../Copy/radicals_book.json'):
    lb = load_data(book)
    rb = load_data(rads_book)
    jk = set(k["k"] for k in lb)
    rads = [rad for kanji in itertools.chain(lb, rb) for rad in kanji["c"] if rad not in jk]
    counter = Counter(rads)
    p = Path(rads_file)
    rads_file2 = str(p.with_name(p.stem + '_new' + p.suffix))
    pipe_transform(rads_file, rads_file2, lambda x: radicals_update_transform(x,counter))
    with open(rads_file2, 'a') as f:
        f.writelines('-----------------------\n')
        f.writelines(r + ', ' + str(c) + '\n' for r, c in counter.items())


def radicals_update_transform(line, counter):
    radical = line.split(',')[0]
    if radical not in counter:
        if re.match('\d|-|[a-zA-Z]', radical):
            return line.strip('\n') #Just indicator lines, not radicals
        else:
            return radical + ', 0'
    else:
        return radical + ', ' + str(counter.pop(radical))


def guarantee_consistency(log_file='../data/log.txt'):
    jk = toolbox.load_data_safe('../data/jouyou_kanji.json')
    rads = toolbox.load_data_safe('../data/radicals.json')
    jk_d = toolbox.dict_by_field(jk, 'k')
    rads_d = toolbox.dict_by_field(rads, 'k')
    joined_d = dict()
    joined_d.update(jk_d)
    joined_d.update(rads_d)
    assert len(joined_d) == len(rads_d) + len(jk_d)
    log_entries = ["---Asserting consistency---"]
    log_entries.append('---Looks like simmetry and is contained---')
    # first pass: 'looks like' simmetry and is contained
    for kanji, details in joined_d.items():
        details['ic'] = []
        if 'cc' not in details:
            details['cc'] = []
    for kanji, details in joined_d.items():
        for lookalike in details['l']:
            if kanji not in joined_d[lookalike]['l']:
                joined_d[lookalike]['l'].append(kanji)
                log_entries.append('Added ' + kanji + ' to the lookalikes of ' + lookalike)
        for component in details['c']:
            if kanji not in joined_d[component]['ic']:
                joined_d[component]['ic'].append(kanji)
                log_entries.append('Added ' + kanji + ' to the is components of ' + component)
        if 'alt' in details:
            for component in details['alt']:
                joined_d[component]['ic'].append(kanji)
                log_entries.append('Added ' + kanji + ' to the is alternate components of ' +
                                   component)
    # second pass: recursive c, s and ic.
    log_entries.append('---Recursive c, s and ic---')
    counter = 0
    for kanji, details in joined_d.items():
        counter+=1
        if counter%100 == 0:
            print(counter)
        # print(details['m'].encode('utf8'))
        details['c+'] = details['c'].copy()
        details['ic'] = list(set(details['ic']))
        details['ic+'] = details['ic'].copy()
        details['s+'] = details['s'].copy()
        # Components and squares
        i = 0
        while i < len(details['c+']):
            if len(joined_d[details['c+'][i]]['c']) > 0:
                log_entries.append('On the kanji: ' + kanji +
                                   ' replaced the component: ' + details['c+'][i] +
                                   ' for its subcomponents')
                if details['c+'][i] not in details['c'] and details['c+'][i] not in details['cc']:
                    details['cc'].append(details['c+'][i])
                    log_entries.append('Added ' + details['c+'][i] +
                                       ' to the is EXTRA components of ' + kanji)
                # Add one item as a list element
                details['s+'] = (details['s+'][:i] +
                                 joined_d[details['c+'][i]]['s'] +
                                 details['s+'][i:])
                details['c+'] = (details['c+'][:i] +
                                 joined_d[details['c+'][i]]['c'] +
                                 details['c+'][i+1:])
            else:
                i += 1
        if len(details['c']) == len(details['c+']):
            details.pop('c+', None)
            details.pop('s+', None)
        # Is component
        for supercomponent in details['ic+']:
            if joined_d[supercomponent]['ic']:
                log_entries.append('On the kanji: ' + kanji +
                                   ' added the super-component of ' + supercomponent)
                details['ic+'].extend(joined_d[supercomponent]['ic'])
        details['ic+'] = list(set(details['ic+']))
        if len(details['ic']) == len(details['ic+']):
            details.pop('ic+', None)
        else:
            details['ic+'] = list(set(details['ic+']) - set(details['ic']))
    log_entries.append('---Finished successfully---')
    toolbox.save_data(jk, '../data/jouyou_kanji.json')
    toolbox.save_data(rads, '../data/radicals.json')
    toolbox.save_data(log_entries, log_file)

def has_katakana(reading):
    return bool(re.match(katakana_range, reading))

def condensate_contents(contents, squares, also_join=True):
    """Joins two list in a round-robbin manner.

    Example: contents = ['a', 'b', 'c']; squares = ['+', '*']
    result = 'a+b*c'
    """
    condensed_list = [elem
                      for sublist in itertools.zip_longest(contents,squares, fillvalue='')
                      for elem in sublist]
    if condensed_list:
        condensed_list.pop()
    if also_join:
        return ''.join(condensed_list)
    else:
        return condensed_list

def get_contents_subgroups(contents, squares, complete=False):
    condensed_list = condensate_contents(contents, squares, also_join=False)
    l = len(condensed_list)
    if complete:
        for j in range(l, 1, -1): # from the length up to two elements
            for i in range(l-j+1):
                yield ''.join(condensed_list[i:i+j])
        for elem in contents:
            yield elem
    else:
        for i in range(0, l - 2, 2):
            yield ''.join(condensed_list[i:i+3])

def absolute_to_hira(thingie):
    romaji = romkan.to_hepburn(thingie)
    result = romkan.to_hiragana(romaji)
    return result
