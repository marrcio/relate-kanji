import collections
import itertools
import re

import romkan
import toolbox
import xml.etree.ElementTree as ET

from structures import IP, IS

Example = collections.namedtuple('Example', ['word', 'freq'])

hiragana_range = re.compile(r'[\u3040-\u309F]')
katakana_range = re.compile(r'[\u30a0-\u30ff]')

jmkanji = None

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

def get_kanji_examples():
    kanji_examples = { k: {'words': [], 'value': 0}
                      for k in IS.acceptable_set - IS.equivalents_set}
    for count_word in toolbox.load_data(IP.WORDS_FILTERED, iterable=True):
        example = Example(word=count_word[1], freq=int(count_word[0]))
        for letter in example.word:
            if letter in IS.equiv_to_jouyou:
                letter = IS.equiv_to_jouyou[letter]
            if letter in IS.acceptable_set:
                kanji_examples[letter]['words'].append(example)
                kanji_examples[letter]['value'] += int(example.freq)
    for details in kanji_examples.values():
        details['words'] = sorted(details['words'], key=lambda x: -x.freq)
    return kanji_examples


def get_refined_kanji_examples(percent_hold=0.80, num_hold=5, num_max=50):
    unrefined = get_kanji_examples()
    dicts_set = set(x[1] for x in toolbox.load_data(IP.WORDS_FILTERED_IN_DICTS))
    for details in unrefined.values():
        accum_percent = 0
        accum_num = 0
        holder = []
        hold = details['value']*percent_hold
        it = iter(details['words'])
        while (accum_percent < hold or accum_num < num_hold) and (accum_num < num_max):
            try:
                word_value = next(it)
                if word_value.word in dicts_set:
                    accum_percent += word_value.freq
                    accum_num += 1
                    holder.append(word_value)
            except StopIteration:
                break
        details['words'] = holder
    return unrefined

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

def generate_separations(num_parts, word, start=0):
    """Generate all possible separations of a word in num_parts."""
    if num_parts == 1:
        return [[word[start:]]]
    if num_parts > len(word) - start:
        return []
    possibilities = []
    for n in range(1, len(word) - start):
        new_possibilities = []
        for possibility in generate_separations(num_parts - 1, word, start + n):
            new_possibilities.append([word[start:start + n]] + possibility)
        possibilities.extend(new_possibilities)
    return possibilities

def is_element_match(k, r):
    """Returns true if the element k can match to the element r."""
    if k in IS.hira_kata:
        return absolute_to_hira(k) == absolute_to_hira(r)
    if k in IS.joined_d:
        # Still naive. Certain small modifications can be made to accomodate
        r = absolute_to_hira(r)
        return (r in IS.joined_d[k].get('on', []) or 
                r in IS.joined_d[k].get('kun', dict()).keys() or 
                r in IS.joined_d[k].get('nanori', []))
    
    # Don't care.
    # Next step: special treatment for 々, somehow
    return True

def is_word_match(word, reading):
    all_readings = separate_readings(word, reading)
    # No possible interpretation found
    if not all_readings:
        return False
    # Since all interpretations have the same number of kanji matches, we only have to see if the first
    # have a match for all Kanji
    interpretation = all_readings[0]    
    if all(elem['match'] for elem in interpretation):
        return True
    return False


def find_equivalence(kanji, reading):
    """Returns a map with Kanji, Reading, MatchFlag, Best Match, Diff, Sub list"""
    # Next step: delineate the TYPE of match (on, kun, nanori), with preference for same-type.
    reading = absolute_to_hira(reading)
    smallest_diff = len(reading)
    best_match = None
    sub_list = []
    executed_subs = []
    if kanji not in IS.joined_d:
        return {'kanji': kanji, 'reading': reading, 'match': True, 'executed_subs': [],
                'best_match': reading, 'diff': 0, 'sub_list': []}
    for candidate in itertools.chain(IS.joined_d[kanji]['on'], 
                                     IS.joined_d[kanji]['kun'].keys(),
                                     IS.joined_d[kanji]['nanori']):
        
        # We'll only consider substitution types of differences
        if len(candidate) != len(reading):
            continue
        diff = 0
        subs = []
        exec_subs = []
        for a, b in zip(candidate, reading):
            if a != b:
                if (a,b) in IS.close_hiragana:
                    exec_subs.append((a,b))
                else:
                    diff += 1
                    subs.append((a,b))
        if diff < smallest_diff:
            smallest_diff = diff
            best_match = candidate
            sub_list = subs
            executed_subs = exec_subs
    return {'kanji': kanji, 'reading': reading, 'match': smallest_diff == 0, 
            'executed_subs': executed_subs, 'best_match': best_match, 'diff': smallest_diff, 
            'sub_list': sub_list}


def separate_readings(word, reading):
    word = word.strip(' \r\n\t')
    reading = reading.strip(' \r\n\t')
    possible_separations = generate_separations(len(word), reading)
    interpretations = []
    max_num_of_matches = 0
    for separations in possible_separations:
        interpretation = []
        for kanji, r in zip(word, separations):
            matches = is_element_match(kanji, r)
            if kanji in IS.hira_kata:
                if not matches:
                    interpretation = []
                    break
            else:
                interpretation.append(find_equivalence(kanji, r))
        if interpretation:
            perfect_matches = sum(i['match'] for i in interpretation)
            if perfect_matches > max_num_of_matches:
                max_num_of_matches = perfect_matches
                interpretations = [interpretation]
            elif perfect_matches == max_num_of_matches:
                interpretations.append(interpretation)
    return interpretations


def extract_kun_readings(readings):
    readings = [reading.strip('-') for reading in readings]
    readings_d = collections.defaultdict(list)
    for reading in readings:
        parts = reading.split('.')
        if len(parts) == 1:
            x = parts[0]
            if x not in readings_d:
                readings_d[x] = []
        elif len(parts) == 2:
            x, y = parts
            readings_d[x].append(y)
        else:
            print("Strange length! %d" % len(parts))
            toolbox.save_data(readings, '../data/temp_output.txt')
    return readings_d
