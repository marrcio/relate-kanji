import copy
import functools
import json
import re
import toolbox
import xmltodict

from collections import Counter, defaultdict
from pathlib import Path
from structures import IP, IS

def filter_word_count(input_path=IP.RAW_WORDS_PATH, output_path=IP.WORDS_FILTERED, lower=2):
    holder = []
    for entry in toolbox.load_data(IP.RAW_WORDS_PATH, iterable=True):
        if int(entry[0]) > lower and any(char in toolbox.IS.jk_set for char in entry[1]):
            holder.append(entry)
    toolbox.save_data(holder, output_path)

def filter_word_count_teachable(input_path=IP.WORDS_FILTERED,
                                 output_path=IP.WORDS_TEACHEABLE):
    """Separate only the count, word pairs in which all characters are acceptable."""
    wc = toolbox.load_data(input_path)
    def is_wanted(x):
        return x in IS.jk_expanded_set or x in IS.hira_kata
    wc_f = [x for x in wc if all(is_wanted(c) for c in x[1])]
    toolbox.save_data(wc_f, output_path)

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
    wc_f = toolbox.load_data(IP.WORDS_TEACHEABLE)
    words = set(word[1] for word in wc_f)
    with open(output_path, 'w') as f:
        callback = functools.partial(_jdict_to_file, words=words, f=f)
        xmltodict.parse(open(dict_path, 'rb'), item_depth=2, item_callback=callback)


def get_kanji_examples():
    kanji_examples = { k: {'words': [], 'value': 0} for k in IS.jk_set}
    for entry in toolbox.load_data(IP.WORDS_FILTERED, iterable=True):
        for letter in entry[1]:
            if letter in IS.jk_set:
                kanji_examples[letter]['words'].append(Example(word=entry[1],
                                                       freq=int(entry[0])))
                kanji_examples[letter]['value'] += int(entry[0])
    kanji_examples = sorted(kanji_examples.items(), key=lambda x: -x[1]['value'])
    for kanji in kanji_examples:
        kanji[1]['words'] = sorted(kanji[1]['words'], key=lambda x: -x[1])
    return kanji_examples


def get_refined_kanji_examples(percent_hold=0.80, num_hold=5, num_max=50):
    unrefined = get_kanji_examples()
    dicts_set = set(x[1] for x in toolbox.load_data(IP.WORDS_FILTERED_IN_DICTS))
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


def create_kanjis_and_examples(percent_hold=0.80, num_hold=5, num_max=50, output_path=IP.):
    refined = get_refined_kanji_examples(percent_hold, num_hold, num_max)
    return refined


def double_filter_jdict(dict_path, output_path):
    """Further resume the json by only adding example words."""
    essential = set(x[0] for x in toolbox.load_data(IP.WORDS_ESSENTIAL))
    with open(output_path, 'w') as f:
        for entry in toolbox.load_data(dict_path, iterable=True):
            if any(x['keb'] in essential for x in entry['k_ele']):
                f.write(json.dumps(entry, ensure_ascii=False, sort_keys=True))
                f.write('\n')

def triple_filter_jmndict(output_path=IP.JMNDICT_ESSENTIAL):
    """If it is found that a word is part of both dicts, prefer JMDICT entries."""
    w_jm = set(k_ele['keb']
               for entry in toolbox.load_data(IP.JMDICT_ESSENTIAL, iterable=True)
               for k_ele in entry['k_ele'])
    w_jmn = set(k_ele['keb']
               for entry in toolbox.load_data(IP.JMNDICT_ESSENTIAL, iterable=True)
               for k_ele in entry['k_ele'])
    intersection = w_jm & w_jmn
    new_entries = []
    for entry in toolbox.load_data(IP.JMNDICT_ESSENTIAL, iterable=True):
        # Only one entry per word in this dict
        if entry['k_ele'][0]['keb'] not in intersection:
            new_entries.append(entry)
    toolbox.save_data(new_entries, output_path)

def remove_only_one_ocurrence_example():
    entries = toolbox.load_data_safe(IP.KANJI_AND_EXAMPLES)
    for entry in entries:
        for k, v in entry.items():
            entry[k]['words'] = [word_count for word_count in v['words'] if word_count[1] > 1]
    toolbox.save_data(entries, IP.KANJI_AND_EXAMPLES)


def gather_words_in_dict(jmdict_path=IP.JMDICT_CLEAN, jmndict_path = IP.JMNDICT_CLEAN,
                         output_path=IP.WORDS_IN_DICT_SET):
    words_jm = set(k_ele['keb'] for entry in toolbox.load_data(jmdict_path, iterable=True)
                for k_ele in entry['k_ele'])
    words_jmn = set(k_ele['keb'] for entry in toolbox.load_data(jmndict_path, iterable=True)
                for k_ele in entry['k_ele'])
    toolbox.save_data(words_jm | words_jmn, output_path)

def gather_essential_words(input_path=IP.KANJI_AND_EXAMPLES, output_path=IP.WORDS_ESSENTIAL):
    essential = set(word[0] for entry in toolbox.load_data(input_path)
                    for v in entry.values()
                    for word in v['words'])
    toolbox.save_data(essential, output_path)

def filter_word_count_with_definition(input_path=IP.WORDS_TEACHEABLE,
                                      output_path=IP.WORDS_FILTERED_IN_DICTS):
    """Filter the word count so that it only contains words that exist in one of the dicts."""
    words_in_dicts = set(word[0] for word in toolbox.load_data('../data/words_in_dicts.csv'))
    in_words = toolbox.load_data(input_path)
    out_words = [count_word for count_word in in_words if count_word[1] in words_in_dicts]
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

def clean_jmdict_olds(output_path=IP.JMDICT_CLEAN):
    undesired_infs = {'word containing out-dated kanji'}
    undesired_miscs = {'archaism', 'obscure term', 'obsolete term'}
    new_entries = []
    for entry in toolbox.load_data('../data/jmdict.json', iterable=True):
        entry['k_ele'] = [k_ele for k_ele in entry['k_ele']
                          if all(x not in undesired_infs for x in k_ele.get('ke_inf', []))]
        entry['sense'] = [sense for sense in entry['sense']
                          if all(x not in undesired_miscs for x in sense.get('misc', []))]
        if bool(entry['k_ele']) and bool(entry['sense']):
            new_entries.append(entry)
    toolbox.save_data(new_entries, output_path)


def clean_jmdict_gloss(output_path=IP.JMDICT_ESSENTIAL):
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
                    if 're_restr' not in r_ele or elem['keb'] in r_ele['re_restr']]
                new_entry['sense'] = [sense for sense in entry['sense']
                    if ('stagk' not in sense or elem['keb'] in sense['stagk']) and
                    ('stagr' not in sense or
                     any(r_ele['reb'] in sense['stagr'] for r_ele in new_entry['r_ele']))]
                new_entries.append(new_entry)
    toolbox.save_data(new_entries, output_path)

def rebuild_base_files(safe=False):
    filter_word_count()  # Make sure WORDS_FILTERED only has words with at least one kanji.
    filter_word_count_teachable()  # Make sure WORDS_TEACHEABLE has only acceptable characters.
    print("Filtering JMdict...")  # Takes a while
    filter_jdict(IP.JMDICT_XML, IP.JMDICT_BASE)
    print("Filtering JMnedict...")  # Takes a while
    filter_jdict(IP.JMNEDICT_XML, IP.JMNEDICT_BASE)

def update_radicals_counter(book='../../../Copy/smallest_book.json',
                            rads_file='../../../Copy/radicals.txt',
                            rads_book='../../../Copy/radicals_book.json'):
    lb = toolbox.load_data(book)
    rb = toolbox.load_data(rads_book)
    counter = Counter(IS.rads)
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
                log_entries.append('Added ' + kanji + ' to the lookalikes of ' + lookalike)
        for component in details['c']:
            if kanji not in IS.joined_d[component]['ic']:
                IS.joined_d[component]['ic'].append(kanji)
                log_entries.append('Added ' + kanji + ' to the is components of ' + component)
        if 'alt' in details:
            for component in details['alt']:
                IS.joined_d[component]['ic'].append(kanji)
                log_entries.append('Added ' + kanji + ' to the is alternate components of ' +
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
                                   ' replaced the component: ' + details['c+'][i] +
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
    toolbox.save_data(log_entries, log_file)
    IS.reload()
