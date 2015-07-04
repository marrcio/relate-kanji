import json
import csv
import re
import os.path
from bs4 import BeautifulSoup
import urllib.request
import urllib.parse
import romkan
import xml.etree.ElementTree as ET
import matplotlib.pyplot as plt
from collections import Counter

example_dict = {'foo':1, 'bar':2, 'baz':3}
katakana_range = re.compile(r'[\u30a0-\u30ff]')
step = None
jmkanji = None
jmdict = None
problems = []

#File related

def load_data(filename, iterable=False, delimiter=','):
    ext = os.path.splitext(filename)[1]
    if ext == '.json':
        if iterable:
            return json_iter_loader(filename)
        else:
            return json_loader(filename)
    elif ext == '.csv' or ext == '.tsv':
        if iterable:
            return csv_iter_loader(filename, delimiter)
        else:
            return csv_loader(filename, delimiter)
    else:
        raise ValueError('Extension ' + ext + ' not supported.')

def save_data(data, filename, delimiter=','):
    ext = os.path.splitext(filename)[1]
    if ext == '.json':
        return json_saver(data, filename)
    elif ext == '.csv':
        return csv_saver(data, filename, delimiter)
    else:
        raise ValueError('Extension ' + ext + ' not supported.')

def json_loader(filename):
    holder = []
    with open(filename) as f:
        for line in f:
            holder.append(json.loads(line))
    return holder

def json_iter_loader(filename):
    with open(filename) as f:
        for line in f:
            yield json.loads(line)

def csv_loader(filename, delimiter):
    holder = []
    with open(filename) as f:
        reader = csv.reader(f, delimiter=delimiter)
        for row in reader:
            holder.append(row)
    return holder

def csv_iter_loader(filename, delimiter):
    with open(filename) as f:
        reader = csv.reader(f, delimiter=delimiter)
        for row in reader:
            yield row

def json_saver(data, filename):
    with open(filename, 'w') as f:
        f.writelines(json.dumps(x, ensure_ascii=False)+'\n' for x in data)

def csv_saver(data, filename, delimiter):
    with open(filename, 'w') as f:
        writer = csv.writer(f)
        for row in data:
            writer.writerow(row)

def pipe_filter(in_file, out_file, filter_f, **kwargs):
    source = load_data(in_file, iterable=True, **kwargs)
    save_data(filter(filter_f, source), out_file, **kwargs)

#Web related

def scrape_table(url, dict_output=False, **kwargs):
    with urllib.request.urlopen(url) as response:
        soup = BeautifulSoup(response.read())
    scraped_data = []
    table = soup.find(**kwargs)
    headers = [header.text for header in table.find_all('th')] #may be empty
    rows = table.find_all('tr')
    for row in rows:
        entries = row.find_all('td')
        if entries:
            scraped_data.append([entry.text for entry in entries])
    if dict_output:
        scraped_data = [dict(zip(headers, entries)) for entries in scraped_data]
    return scraped_data

def scrape_kanji(kanji):
    url = 'https://en.wiktionary.org/wiki/'
    url += urllib.parse.quote(kanji)
    with urllib.request.urlopen(url) as response:
        soup = BeautifulSoup(response.read())
    try:
        ans = soup.select('#Han_character')[0].parent.findNextSibling('p').text
    except:
        ans = ''
        problems.append(kanji)
        print('Problem with kanji ' + kanji)
    return ans


#Specific RelateKanji

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

def has_katakana(reading):
    return bool(re.match(katakana_range, reading))

def absolute_to_hira(thingie):
    romaji = romkan.to_hepburn(thingie)
    result = romkan.to_hiragana(romaji)
    return result

#Object handling tools (medling with dicts, lists, sets)

def dict_by_field(list_of_objects, field, transformation=lambda x:x, list_mode=False):
    """Indexes one of the fields of each object, returns a single dictionary"""
    if list_mode:
        field = int(field)
    return {transformation(entry[field]):entry for entry in list_of_objects}

def remove_duplicates(iterable):
    """Removes duplicates of an iterable without meddling with the order"""
    seen = set()
    seen_add = seen.add # for efficiency, local variable avoids check of binds
    return [x for x in iterable if not (x in seen or seen_add(x))]

def condense_duplicates_dict(list_of_lists):
    """Transforms a list of lists to a dictionary.

    Duplicates in the first element(list[0]) are condensed to a single key,
    contents are fused together by making dict[key].expand(list[1:])
    """
    ans = dict()
    for group in list_of_lists:
        if group[0] not in ans:
            ans[group[0]] = group[1:]
        else:
            ans[group[0]].extend(group[1:])
    return ans

#Graphic tools

def visualize_bars(iterable, width=0.5, color='b', transformation=lambda x:x):
    c = Counter(iterable)
    x,y = zip(*c.items())
    plt.bar([n-width/2 for n in x], transformation(y), width=width, color=color)
    plt.grid(True)

#MISC

def _paced_return_generator(container, size=1):
    it = iter(container)
    while True:
        result = []
        for i in range(size):
            try:
                result.append(next(it))
            except StopIteration:
                break
        yield result

def paced(container, size=1):
    global step
    step = _paced_return_generator(container, size)
    return next(step)

def walk():
    return next(step)

