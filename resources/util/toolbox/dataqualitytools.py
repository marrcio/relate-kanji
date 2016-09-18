import copy
import collections
import functools
import json
import re
import toolbox
import xmltodict

from collections import Counter, defaultdict, namedtuple, OrderedDict
from pathlib import Path
from structures import IP, IS

def filter_word_count(input_path=IP.RAW_WORDS_PATH, output_path=IP.WORDS_FILTERED, lower=2):
    holder = []
    for entry in toolbox.load_data(IP.RAW_WORDS_PATH, iterable=True):
        if int(entry[0]) > lower and any(char in toolbox.IS.jk_set for char in entry[1]):
            holder.append(entry)
    toolbox.save_data(holder, output_path)

def filter_word_count_teachable(input_path=IP.WORDS_FILTERED,
                                 output_path=IP.WORDS_TEACHABLE):
    """Separate only the count, word pairs in which all characters are acceptable."""
    wc = toolbox.load_data(input_path)
    wc_f = [x for x in wc if all(c in IS.teachable_set for c in x[1])]
    toolbox.save_data(wc_f, output_path)

def convert_and_filter_jdict(dict_path, output_path):
    """Transform the original XML dict in a resumed json only with 'teachable' words."""
    def _jdict_to_file(_, entry, words, f):
        if 'k_ele' in entry:
            if type(entry['k_ele']) != list:
                entry['k_ele'] = [entry['k_ele']]
            if any(x['keb'] in words for x in entry['k_ele']):
                f.write(json.dumps(entry, ensure_ascii=False, sort_keys=True))
                f.write('\n')
        return True
    wc_f = toolbox.load_data(IP.WORDS_TEACHABLE)
    words = set(word[1] for word in wc_f)
    with open(output_path, 'w', encoding='utf8') as f:
        callback = functools.partial(_jdict_to_file, words=words, f=f)
        xmltodict.parse(open(dict_path, 'rb'), item_depth=2, item_callback=callback)

def convert_and_filter_kanjidict(dict_path=IP.KANJIDICT_XML, output_path=IP.KANJIDICT_JSON):
    """Transform the original XML dict in a resumed json only with extended kanji."""
    def _kanjidict_to_file(_, character, acceptable, f):
        if character.get('literal', None) in acceptable:
            f.write(json.dumps(character, ensure_ascii=False, sort_keys=True))
            f.write('\n')
        return True
    with open(output_path, 'w') as f:
        callback = functools.partial(_kanjidict_to_file, acceptable=IS.acceptable_set, f=f)
        xmltodict.parse(open(dict_path, 'rb'), item_depth=2, item_callback=callback)

def clean_kanjidict(input_path=IP.KANJIDICT_JSON, output_path=IP.KANJIDICT_CLEAN):
    clean_kanjis = []
    for kanji in toolbox.load_data(input_path, iterable=True):
        new_kanji = {}
        new_kanji['literal'] = kanji['literal']
        if 'grade' in kanji['misc']:
            new_kanji['grade'] = kanji['misc']['grade']
        if 'stroke_count' in kanji['misc']:
            new_kanji['stroke_count'] = kanji['misc']['stroke_count']
        if 'reading_meaning' in kanji:
            new_kanji['nanori'] = kanji['reading_meaning'].get('nanori', [])
            if 'rmgroup' in kanji['reading_meaning']:
                if 'meaning' in kanji['reading_meaning']['rmgroup']:
                    new_kanji['meaning'] = [m
                                            for m in kanji['reading_meaning']['rmgroup']['meaning']
                                            if not isinstance(m, dict)]
                if 'reading' in kanji['reading_meaning']['rmgroup']:
                    new_kanji['kun'] = [elem['#text']
                                        for elem in kanji['reading_meaning']['rmgroup']['reading']
                                        if elem['@r_type'] == 'ja_kun']
                    new_kanji['on'] = [elem['#text']
                                       for elem in kanji['reading_meaning']['rmgroup']['reading']
                                       if elem['@r_type'] == 'ja_on']
        clean_kanjis.append(new_kanji)
    toolbox.save_data(clean_kanjis, output_path)

def update_dicts_with_kanjidict(kanjidic=IP.KANJIDICT_CLEAN):
    just_pass = {'on', 'nanori'}
    new_extra = []
    new_jouyou_d = dict()
    new_rads_d = dict()
    for entry in toolbox.load_data(kanjidic, iterable=True):
        k = entry['literal']
        if k in IS.joined_d:
            old_entry = IS.joined_d[k]
            new_entry = OrderedDict()
            new_entry['k'] = old_entry['k']
            if k in IS.rads_d:
                new_entry['v'] = old_entry['v']
                new_entry['o'] = old_entry['o']
            for key in ['c', 'l', 's']:
                new_entry[key] = old_entry[key]
            proposals = set([toolbox.absolute_to_hira(reading)
                             for reading in entry.get('on', [])])
            old_ons = set([toolbox.absolute_to_hira(reading)
                           for reading in old_entry.get('on', [])])
            new_entry['on'] = list(proposals | old_ons)
            new_entry['kun'] = old_entry.get('kun', dict())
            new_entry['kun'].update(toolbox.extract_kun_readings(entry.get('kun', [])))
            new_entry['nanori'] = entry.get('nanori', [])
            new_entry['m'] = old_entry['m']
            extra_m = [meaning for meaning in entry.get('meaning', [])
                       if meaning not in new_entry['m'].split(', ')]
            new_entry['extra_m'] = ', '.join(extra_m)
            new_entry['strokes'] = entry.get('stroke_count', ['-1'])[0]
            new_entry['grade'] = entry.get('grade', [])
            resting_of_old = OrderedDict([(key, value) for key, value in old_entry.items()
                                          if key not in new_entry])
            new_entry.update(resting_of_old)
            if k in IS.jk_d:
                new_jouyou_d[k] = new_entry
            elif k in IS.rads_d:
                new_rads_d[k] = new_entry
            else:
                new_extra.append(entry)
        elif k not in IS.equiv_to_jouyou:
            new_entry = OrderedDict()
            new_entry['k'] = k
            new_entry['c'] = []
            new_entry['l'] = []
            new_entry['s'] = []
            new_entry['on'] = [toolbox.absolute_to_hira(reading)
                               for reading in entry.get('on', [])]
            new_entry['kun'] = toolbox.extract_kun_readings(entry.get('kun', []))
            new_entry['nanori'] = entry.get('nanori', [])
            new_entry['m'] = entry.get('meaning', [""])[0]
            new_entry['extra_m'] = ', '.join(entry.get('meaning', [])[1:])
            new_entry['strokes'] = entry.get('stroke_count', ['-1'])[0]
            new_entry['grade'] = entry.get('grade', [])
            new_entry['ic'] = []
            new_entry['r'] = ''
            new_entry['cc'] = []
            new_extra.append(new_entry)
    new_jouyou = [new_jouyou_d[entry['k']] for entry in IS.jk]
    new_rads = [new_rads_d.get(entry['k'], entry) for entry in IS.rads]

    toolbox.save_data(new_rads, IP.RADICALS_PATH)
    toolbox.save_data(new_jouyou, IP.JOUYOU_PATH)
    toolbox.save_data(new_extra, IP.EXTRA_PATH)

def create_kanjis_and_examples(percent_hold=0.80, num_hold=5, num_max=50,
                               output_path=IP.KANJI_AND_EXAMPLES):
    refined = toolbox.get_refined_kanji_examples(percent_hold, num_hold, num_max)
    refined = sorted(refined.items(), key=lambda x: -x[1]['value'])
    refined = [dict([(kanji, details)]) for kanji, details in refined]
    toolbox.save_data(refined, output_path)


def double_filter_jdict(dict_path, output_path):
    """Further resume the json by only adding example words."""
    essential = set(x[0] for x in toolbox.load_data(IP.WORDS_ESSENTIAL))
    with open(output_path, 'w', encoding='utf8') as f:
        for entry in toolbox.load_data(dict_path, iterable=True):
            if any(x['keb'] in essential for x in entry['k_ele']):
                f.write(json.dumps(entry, ensure_ascii=False, sort_keys=True))
                f.write('\n')

def triple_filter_jmnedict(output_path=IP.JMNEDICT_ESSENTIAL):
    """If it is found that a word is part of both dicts, prefer JMDICT entries."""
    w_jm = set(k_ele['keb']
               for entry in toolbox.load_data(IP.JMDICT_ESSENTIAL, iterable=True)
               for k_ele in entry['k_ele'])
    w_jmn = set(k_ele['keb']
               for entry in toolbox.load_data(IP.JMNEDICT_ESSENTIAL, iterable=True)
               for k_ele in entry['k_ele'])
    intersection = w_jm & w_jmn
    new_entries = []
    for entry in toolbox.load_data(IP.JMNEDICT_ESSENTIAL, iterable=True):
        # Only one entry per word in this dict
        if entry['k_ele'][0]['keb'] not in intersection:
            new_entries.append(entry)
    toolbox.save_data(new_entries, output_path)

def gather_words_in_dict(jmdict_path=IP.JMDICT_CLEAN, jmnedict_path = IP.JMNEDICT_CLEAN,
                         output_path=IP.WORDS_IN_DICT_SET):
    words_jm = set(k_ele['keb'] for entry in toolbox.load_data(jmdict_path, iterable=True)
                for k_ele in entry['k_ele'])
    words_jmn = set(k_ele['keb'] for entry in toolbox.load_data(jmnedict_path, iterable=True)
                for k_ele in entry['k_ele'])
    toolbox.save_data(words_jm | words_jmn, output_path)

def gather_essential_words(input_path=IP.KANJI_AND_EXAMPLES, output_path=IP.WORDS_ESSENTIAL):
    essential = set(word[0] for entry in toolbox.load_data(input_path)
                    for v in entry.values()
                    for word in v['words'])
    toolbox.save_data(essential, output_path)

def filter_word_count_with_definition(input_path=IP.WORDS_TEACHABLE,
                                      output_path=IP.WORDS_FILTERED_IN_DICTS):
    """Filter the word count so that it only contains words that exist in one of the dicts."""
    words_in_dicts = set(word[0] for word in toolbox.load_data(IP.WORDS_IN_DICT_SET))
    in_words = toolbox.load_data(input_path)
    out_words = [count_word for count_word in in_words if count_word[1] in words_in_dicts]
    toolbox.save_data(out_words, output_path)

def clean_jmnedict(input_path=IP.JMNEDICT_BASE,
                   output_path=IP.JMNEDICT_CLEAN):
    wanted_fields = {'place name',
                     'company name',
                     'railway station',
                     'organization name',
                     'full name of a particular person',
                     'product name',
                     'work of art, literature, music, etc. name'}
    def filter_wanted(entry, wanted_fields):
        return any(name_type in wanted_fields for trans in entry['trans']
                   for name_type in trans.get('name_type', []))

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

def clean_jmdict(input_path=IP.JMDICT_BASE, output_path=IP.JMDICT_CLEAN):
    """No out-dated kanji, archaismsm, obscure or obsolete terms."""
    undesired_k_infs = {'word containing out-dated kanji'}
    undesired_r_infs = {'out-dated or obsolete kana usage'}
    undesired_miscs = {'archaism', 'obscure term', 'obsolete term'}
    new_entries = []
    for entry in toolbox.load_data(input_path, iterable=True):
        entry['k_ele'] = [k_ele for k_ele in entry['k_ele']
                          if all(x not in undesired_k_infs for x in k_ele.get('ke_inf', []))]
        entry['r_ele'] = [r_ele for r_ele in entry['r_ele']
                  if all(x not in undesired_r_infs for x in r_ele.get('re_inf', []))]
        entry['sense'] = [sense for sense in entry['sense']
                          if all(x not in undesired_miscs for x in sense.get('misc', []))]
        if bool(entry['k_ele']) and bool(entry['sense']) and bool(entry['r_ele']):
            new_entries.append(entry)
    toolbox.save_data(new_entries, output_path)


def fix_jmdict_gloss(output_path=IP.JMDICT_ESSENTIAL):
    entries = toolbox.load_data(IP.JMDICT_ESSENTIAL)
    for entry in entries:
        for sense in entry['sense']:
            sense['gloss'] = [d['#text'] for d in sense['gloss']]
    toolbox.save_data(entries, output_path)

def unwind_jdict(input_path=IP.JMDICT_ESSENTIAL, output_path=IP.JMDICT_UNWINDED):
    new_entries = []
    essential = set(x[0] for x in toolbox.load_data(IP.WORDS_ESSENTIAL))
    for entry in toolbox.load_data(input_path, iterable=True):
        for elem in entry['k_ele']:
            if elem['keb'] in essential:
                new_entry = copy.deepcopy(entry)
                new_entry['k_ele'] = elem
                new_entry['r_ele'] = [r_ele for r_ele in entry['r_ele']
                                      if 're_restr' not in r_ele or
                                      elem['keb'] in r_ele['re_restr']]
                new_entry['sense'] = [sense for sense in entry['sense']
                    if ('stagk' not in sense or
                        elem['keb'] in sense['stagk']) and
                    ('stagr' not in sense or
                     any(r_ele['reb'] in sense['stagr']
                         for r_ele in new_entry['r_ele']))]
                if new_entry['r_ele'] and new_entry['sense']:
                    new_entries.append(new_entry)
    toolbox.save_data(new_entries, output_path)

def build_kanji_to_reading_pairs(input_path=IP.JMDICT_CLEAN,
                                 output_path=IP.WORDS_TO_READINGS):
    words_to_readings = set()
    for entry in toolbox.load_data(input_path, iterable=True):
        # Only consider words such that all characters are teachable.
        current_words = {k_ele['keb']: [] for k_ele in entry['k_ele']
                         if all(c in IS.teachable_set for c in k_ele['keb'])}
        for reading in entry['r_ele']:
            assign_to = reading.get('re_restr', list(current_words.keys()))
            for k in assign_to:
                if k in current_words:
                    current_words[k].append(reading['reb'])
        for k, rs in current_words.items():
            for r in rs:
                if len(toolbox.separate_readings(k, r)):
                    words_to_readings.add((k,r))
    toolbox.save_data(sorted(words_to_readings), output_path)

def build_interpretations(input_path=IP.WORDS_TO_READINGS,
                          output_path=IP.INTERPRETATIONS):
    w2r = toolbox.load_data(input_path)
    interps = [toolbox.separate_readings(*x) for x in w2r]
    print("Number of interpretations:")
    print(Counter(len(interp) for interp in interps))
    for (kanji, reading), interp in zip(w2r, interps):
        for poss in interp:
            for elem in poss:
                elem['origin_word'] = kanji
                elem['origin_reading'] = reading

    all_interps = [elem
                   for interp in interps
                   for poss in interp
                   for elem in poss]
    all_interps = sorted(all_interps, key=lambda x: (x['kanji'], x['reading']))
    proper_order = ["kanji", "reading", "best_match", "match", "diff", "executed_subs",
                    "origin_word", "origin_reading", "sub_list"]
    all_interps = [toolbox.make_ordered_dict(d, proper_order)
                   for d in all_interps]
    toolbox.save_data(all_interps, output_path)

def _take_what_you_can(list_of_entries, field, filter_func):
    entries_bkp = copy.deepcopy(list_of_entries)
    for entry in list_of_entries:
        entry[field] = [elem for elem in entry[field] if filter_func(elem, entry)]
    list_of_entries = [entry for entry in list_of_entries if entry[field]]
    return list_of_entries or entries_bkp

def _is_of_readings(sense, entry):
    readings = {elem['reb'] for elem in entry['r_ele']}
    return ('stagr' not in sense) or any(stag in readings for stag in sense['stagr'])

def convert_jmnedict_to_jmdict(input_path=IP.JMNEDICT_ESSENTIAL, output_path=IP.JMNEDICT_REFORMAT):
    new = []
    for entry in toolbox.load_data(input_path, iterable=True):
        current = dict()
        current['ent_seq'] = entry['ent_seq']
        current['k_ele'] = entry['k_ele'][0]
        current['r_ele'] = [entry['r_ele']]
        current['sense'] = []
        for meaning in entry['trans']:
            current['sense'].append({'gloss': meaning['trans_det'], 'pos': meaning['name_type']})
        new.append(current)
    toolbox.save_data(new, output_path)

def create_unified_dict(input_paths = (IP.JMDICT_UNWINDED, IP.JMNEDICT_REFORMAT),
                        output_path = IP.JDICT_FUSION):
    jdicts = toolbox.load_data(input_paths[0])
    jdicts.extend(toolbox.load_data(input_paths[1]))
    toolbox.save_data(jdicts, output_path)

def build_jdict_definition_map(input_path=IP.JDICT_FUSION, output_path=IP.WORDS_TO_DEFINITIONS):
    entries = toolbox.load_data(input_path)
    kanji_to_results = defaultdict(list)
    for entry in entries:
        kanji_to_results[entry['k_ele']['keb']].append(entry)

    # Try to reduce the mapping in cases that a word matches to multiple definitions, using
    # the validity of the reading to those kanjis, the priority of the reading,
    for k, l in kanji_to_results.items():
        if len(l) == 1:
            continue
        refined = [entry for entry in l if 'ke_pri' in entry['k_ele']] or l
        refined = _take_what_you_can(refined, 'r_ele', lambda r, _: 're_pri' in r)
        refined = _take_what_you_can(refined, 'r_ele', lambda r, _: 're_inf' not in r)
        refined = _take_what_you_can(refined, 'r_ele', lambda r, _: 're_nokanji' not in r)
        refined = _take_what_you_can(refined, 'sense', lambda s, _: 'dial' not in s)
        refined = _take_what_you_can(refined, 'sense', _is_of_readings)
        refined = _take_what_you_can(
            refined,
            'r_ele',
            lambda r, entry: toolbox.is_word_match(entry['k_ele']['keb'], r['reb']))
        kanji_to_results[k] = refined
    toolbox.save_data([kanji_to_results], output_path)


def build_jmnedict_definition_map(input_path=IP.JMNEDICT_ESSENTIAL,
                                  output_path=IP.WORDS_TO_NAMES):
    entries = toolbox.load_data(input_path)
    kanji_to_results = defaultdict(list)
    for entry in entries:
        kanji_to_results[entry['k_ele'][0]['keb']].append(entry)

    for k, l in kanji_to_results.items():
        if len(l) == 1:
            continue
        refined = _take_what_you_can(
            l,
            'k_ele',
            lambda k_ele, entry: toolbox.is_word_match(k_ele['keb'], entry['r_ele']['reb']))
        kanji_to_results[k] = refined
    toolbox.save_data([kanji_to_results], output_path)


def rebuild_base_files():
    print("Filtering the raw words file to only words with at least one"
          " kanji...")
    filter_word_count()

    print("Further filtering the words to a list where all characthers are"
          " acceptable.")
    filter_word_count_teachable()

    print("Filtering JMdict...")  # Takes a while
    convert_and_filter_jdict(IP.JMDICT_XML, IP.JMDICT_BASE)

    print("Uniformizing the fields from JMDICT.")
    uniformize(IP.JMDICT_BASE, IP.JMDICT_BASE)

    print("Filtering JMnedict...")  # Takes a while
    convert_and_filter_jdict(IP.JMNEDICT_XML, IP.JMNEDICT_BASE)

    print("Uniformizing the fields from JMNEDICT.")
    uniformize(IP.JMNEDICT_BASE, IP.JMNEDICT_BASE)

    print("Cleaning JMDICT.")
    clean_jmdict()

    print("Cleaning JMNEDICT.")
    clean_jmnedict()

    print("Saving the available words in both dictionaries.")
    gather_words_in_dict()

    print("Filtering the teachable words to only those present in a "
          "dictionary.")
    filter_word_count_with_definition()

    print("Create the file with the actual examples that will be used.")
    create_kanjis_and_examples()

    print("Gather only the essential words.")
    gather_essential_words()

    print("Filter again the JMDICT, to just keep the essential words.")
    double_filter_jdict(IP.JMDICT_CLEAN, IP.JMDICT_ESSENTIAL)

    print("Fix the glosses from JMDICT.")
    fix_jmdict_gloss()

    print("Filter again the JMNEDICT, to just keep the essential words.")
    double_filter_jdict(IP.JMNEDICT_CLEAN, IP.JMNEDICT_ESSENTIAL)

    print("Filter JMNEDICT still one more time, keeping only words exclusive"
          " to it.")
    triple_filter_jmnedict()

    print("Unwinding JMDICT")
    unwind_jdict()

    print("Reformating JMNEDICT")
    convert_jmnedict_to_jmdict()

    print("Creating a unified definition dict")
    create_unified_dict()

    print("Creating a map from word to definition on both dicts")
    build_jdict_definition_map()



def update_radicals_counter(book='../../../Copy/smallest_book.json',
                            rads_file='../../../Copy/radicals.txt',
                            rads_book='../../../Copy/radicals_book.json'):
    lb = toolbox.load_data(book)
    rb = toolbox.load_data(rads_book)
    counter = Counter(IS.rads)
    p = Path(rads_file)
    rads_file2 = str(p.with_name(p.stem + '_new' + p.suffix))
    pipe_transform(rads_file, rads_file2,
                   lambda x: radicals_update_transform(x,counter))
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
    log_entries = ["---Asserting consistency---"]
    log_entries.append('---Looks like simmetry and is contained---')
    # first pass: 'looks like' simmetry and is contained jk
    for kanji, details in IS.joined_d.items():
        details['ic'] = []
        if 'cc' not in details:
            details['cc'] = []
    for kanji, details in IS.joined_d.items():
        for lookalike in details['l']:
            if kanji not in IS.joined_d[lookalike]['l']:
                IS.joined_d[lookalike]['l'].append(kanji)
                log_entries.append('Added ' + kanji +
                                   ' to the lookalikes of ' + lookalike)
        for component in details['c']:
            if kanji not in IS.joined_d[component]['ic']:
                IS.joined_d[component]['ic'].append(kanji)
                log_entries.append('Added ' + kanji +
                                   ' to the is components of ' + component)
        if 'alt' in details:
            for component in details['alt']:
                IS.joined_d[component]['ic'].append(kanji)
                log_entries.append('Added ' + kanji +
                                   ' to the is alternate components of ' +
                                   component)
    # second pass: recursive c, s and ic.
    log_entries.append('---Recursive c, s and ic---')
    counter = 0
    for kanji, details in IS.joined_d.items():
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
            if len(IS.joined_d[details['c+'][i]]['c']) > 0:
                log_entries.append('On the kanji: ' + kanji +
                                   ' replaced the component: ' +
                                   details['c+'][i] +
                                   ' for its subcomponents')
                if details['c+'][i] not in details['c'] and details['c+'][i] not in details['cc']:
                    details['cc'].append(details['c+'][i])
                    log_entries.append('Added ' + details['c+'][i] +
                                       ' to the is EXTRA components of ' + kanji)
                # Add one item as a list element
                details['s+'] = (details['s+'][:i] +
                                 IS.joined_d[details['c+'][i]]['s'] +
                                 details['s+'][i:])
                details['c+'] = (details['c+'][:i] +
                                 IS.joined_d[details['c+'][i]]['c'] +
                                 details['c+'][i+1:])
            else:
                i += 1
        if len(details['c']) == len(details['c+']):
            details.pop('c+', None)
            details.pop('s+', None)
        # Is component
        for supercomponent in details['ic+']:
            if IS.joined_d[supercomponent]['ic']:
                log_entries.append('On the kanji: ' + kanji +
                                   ' added the super-component of ' + supercomponent)
                details['ic+'].extend(IS.joined_d[supercomponent]['ic'])
        details['ic+'] = list(set(details['ic+']))
        if len(details['ic']) == len(details['ic+']):
            details.pop('ic+', None)
        else:
            details['ic+'] = list(set(details['ic+']) - set(details['ic']))
    log_entries.append('---Finished successfully---')
    toolbox.save_data(IS.jk, IP.JOUYOU_PATH)
    toolbox.save_data(IS.rads, IP.RADICALS_PATH)
    toolbox.save_data(IS.extra, IP.EXTRA_PATH)
    toolbox.save_data(log_entries, log_file)
    IS.reload()
