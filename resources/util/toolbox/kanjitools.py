import re
import xml.etree.ElementTree as ET
import romkan
import itertools
import toolbox
from collections import deque
from toolbox.filetools import save_data, load_data, pipe_transform
from collections import Counter, defaultdict
from pathlib import Path

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

def set_jmdict():
    global jmdict
    jmdict = dict_by_field(load_data('../data/jmdict_relevant.json'), 'ent_seq', int)

def collision_comparison(collision_entry):
    if jmdict is None:
        set_jmdict()
    k, collisions_list = collision_entry
    return [jmdict[entry] for entry in collisions_list]

def update_little_book(place='../../../Copy/little_book.json',implied=False, log=None):
    lb = load_data(place)
    lb_kanji = dict_by_field(lb, "kanji")
    resemblance_groups = {k["kanji"]:set(k["kanji"]) for k in lb}
    added_symmetry = defaultdict(list)
    implied_symmetry = defaultdict(list)
    for kanji in lb:
        k_char = kanji["kanji"]
        for look_a_like in kanji["looks_like"]:
            if look_a_like in lb_kanji: # Radicals not in
                fusion = resemblance_groups[look_a_like].union(resemblance_groups[k_char])
                resemblance_groups[look_a_like] = fusion
                resemblance_groups[k_char] = fusion
                if k_char not in lb_kanji[look_a_like]["looks_like"]:
                    lb_kanji[look_a_like]["looks_like"].append(k_char)
                    added_symmetry[look_a_like].append(k_char)
                    # print("symmetric", look_a_like, k_char)
    if implied:
        for kanji in lb:
            k_char = kanji["kanji"]
            for similar in resemblance_groups[k_char]:
                if similar != k_char and similar not in kanji["looks_like"]:
                    kanji["looks_like"].append(similar+"?")
                    implied_symmetry[k_char].append(similar)
                    # print("implied", similar, k_char)
    if log is not None and implied:
        save_data([added_symmetry, implied_symmetry], log)
    elif log is not None:
        save_data([added_symmetry], log)
    destination = place.rsplit('.', 1)
    destination[0] += '2'
    destination = '.'.join(destination)
    save_data(lb, destination)

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
    jk = toolbox.load_data('../data/jouyou_kanji.json')
    rads = toolbox.load_data('../data/radicals.json')
    toolbox.save_data(jk, '../data/jouyou_kanji_bkp.json')
    toolbox.save_data(rads, '../data/radicals_bkp.json')
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
                                   ' added the supercomponent of ' + supercomponent)
                details['ic+'].extend(joined_d[supercomponent]['ic'])
        details['ic+'] = list(set(details['ic+']))
        if len(details['ic']) == len(details['ic+']):
            details.pop('ic+', None)
        else:
            details['ic+'] = list(set(details['ic+']) - set(details['ic']))
    log_entries.append('---Finished succesfully---')
    toolbox.save_data(jk, '../data/jouyou_kanji.json')
    toolbox.save_data(rads, '../data/radicals.json')
    toolbox.save_data(log_entries, log_file)

def has_katakana(reading):
    return bool(re.match(katakana_range, reading))

def condensate_contents(contents, squares):
    """Joins two list in a round-robbin manner.

    Example: contents = ['a', 'b', 'c']; squares = ['+', '*']
    result = 'a+b*c'
    """
    return''.join([elem for sublist in itertools.zip_longest(contents,squares, fillvalue='')
                   for elem in sublist])

def absolute_to_hira(thingie):
    romaji = romkan.to_hepburn(thingie)
    result = romkan.to_hiragana(romaji)
    return result
