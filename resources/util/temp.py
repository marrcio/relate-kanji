import xml.etree.ElementTree as ET

kvg = ET.parse('../data/kanjivg.xml').getroot()

ks_json = dict()
elem_id = '{http://kanjivg.tagaini.net}element'

for k in kvg.findall('kanji/g[@{http://kanjivg.tagaini.net}element]'):
    ks_json[k.get(elem_id)] = []
    for second_g in k.findall('g[@{http://kanjivg.tagaini.net}element]'):
        part = second_g.get(elem_id)
        ks_json[k.get(elem_id)].append(part)
