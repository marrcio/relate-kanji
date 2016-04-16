import collections
import itertools

import romkan
import toolbox
import xml.etree.ElementTree as ET

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

def separate_readings(word, reading):
    word = word.strip(' \r\n\t')
    reading = reading.strip(' \r\n\t')
    reading = absolute_to_hira(reading) # Make sure the reading is in hiragana
    # Make sure the whole word is either in hiragana or Kanji
    word = ''.join([absolute_to_hira(letter) if letter not in jk_d else letter for letter in word])
    if len(word) == 1:
        return {word: reading,
                'regular': reading in (set(jk_d[word]['on']) | set(jk_d[word]['on'].keys()))}
    split_word = [x for x in re.split(r'([^\u3040-\u309F])', word) if x]
    # hiragana_elem = ['(%s)' % elem for elem in split_word if]

def get_all_matchings(tokens, tokens_index, letters, letters_index, hiragana_spots):
    interest_tokens = tokens[tokens_index:]
    token_size = sum(len(token) for token in tokens)
    interest_letters = letters[letters_index:]
    if token_size > len(interest_letters):
        return [] # More tokens than letters to match.
    if token_size == len(interest_letters):
        pass
    if len(interest_tokens) == 1:
        return ([(interest_tokens[0], interest_letters)]
                if is_valid_reading(tokens, tokens_index,
                                    letters, letters_index,
                                    hiragana_spots)
                else [])

def is_valid_reading(tokens, tokens_index, letters, letters_index, hiragana_spots):
    pass
