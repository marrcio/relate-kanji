from structures import IP, IS
import matplotlib.pyplot as plt
import itertools
import time
import toolbox
import numpy as np
from scipy.sparse import csr_matrix
from collections import defaultdict, Counter

def create_morphological_graph():
    morpho_dict = {k: defaultdict(int) 
                   for k in (IS.jk_set | IS.rads_set - {'?'})}
    for json_line in itertools.chain(IS.jk, IS.rads):
        current_char = json_line['k']
        if current_char == '?':
            continue
        if 'v' in json_line and json_line['v']:
            morpho_dict[current_char][json_line['v']] += 1
            morpho_dict[json_line['v']][current_char] += 1
        for other_node in itertools.chain(json_line['c'], 
                                          json_line['ic'], 
                                          json_line['l'], 
                                          json_line.get('alt', [])):
            if other_node != '?':
                morpho_dict[current_char][other_node] += 1
    kfg = toolbox.load_data('../data/kanji_freq_grade_novels.csv')
    Kanji, Freq, Grade = zip(*kfg)
    id_to_char = [k for k in Kanji]
    id_to_char.extend([rad['k'] for rad in IS.rads if rad['k'] != '?'])
    char_to_id = {c: i for i, c in enumerate(id_to_char)}
    freqs = np.zeros(len(morpho_dict))
    freqs[:len(Freq)] = np.array(Freq)
    return morpho_dict, id_to_char, char_to_id, freqs

def create_coocurrence_graph(use_log=False, preview=False):
    count_words = toolbox.load_data(IP.WORDS_TEACHABLE)
    # Kanji that are equivalent to jouyou will be equiparated with jouyou,
    # So they will not be individual nodes in the graph.
    graph_nodes = IS.acceptable_set - IS.equivalents_set
    coocurrence_dict = {k: defaultdict(float) for k in graph_nodes}
    for count, word in count_words:
        kanji_chars = [IS.equiv_to_jouyou.get(k, k) 
                       for k in word 
                       if k in IS.acceptable_set]
        add_val = np.log(int(count)) if use_log else int(count)
        if len(kanji_chars) == 1:
            k = kanji_chars[0]
            coocurrence_dict[k][k] += add_val
        else:
            for origin, sink in itertools.permutations(kanji_chars, 2):
                coocurrence_dict[origin][sink] += add_val
    # Clean up of extra chars that don't create relations.
    to_pop = []
    for key, values in coocurrence_dict.items():
        if key not in IS.jk_set and len(values) == 0:
            to_pop.append(key)
    for key in to_pop:
        coocurrence_dict.pop(key, None)
    kfg = toolbox.load_data('../data/kanji_freq_grade_novels.csv')
    Kanji, Freq, Grade = zip(*kfg)
    id_to_char = [k for k in Kanji]
    id_to_char.append('々')
    jinmeiyou = toolbox.load_data(IP.JINMEIYOU_PATH)[0]
    id_to_char.extend([j for j in jinmeiyou if j in coocurrence_dict])
    char_to_id = {c: i for i, c in enumerate(id_to_char)}
    freqs = np.zeros(len(coocurrence_dict))
    freqs[:len(Freq)] = np.array(Freq)
    if preview:
        preview = [{char: sorted([(kanji, count) 
                                  for kanji, count in coocurrence_dict[char].items()], 
                                 key=lambda x: -int(x[1]))}
                   for char in id_to_char]
        preview = sorted(preview, key=lambda x: -sum(len(v) for v in x.values()))
        toolbox.scatter([sum(len(values) 
                             for values in x.values()) 
                         for x in preview], marker='.', high_dpi=False)
        plt.title('Number of Coocuring Kanji')
        plt.ylabel('Number of Coocuring Kanji')
        plt.xlabel('Index of Kanji')
        toolbox.save_data(preview, '../data/temp.json')
    return coocurrence_dict, id_to_char, char_to_id, freqs

def build_sparse_matrix(elem_dict, char_to_id, filler=None, fill_deadends=True):
    # A dictionary that maps (id1, id2) -> probability
    coord_to_val = dict()
    filler = (1/len(elem_dict))*np.ones(len(elem_dict)) if filler is None else filler
    filler = filler.reshape(len(elem_dict), 1)
    empty_cols = set()
    for kanji, relations_dict in elem_dict.items():
        if not relations_dict:
            empty_cols.add(char_to_id[kanji])
        total = sum(relations_dict.values())
        for kanji2, count in relations_dict.items():
            coord_to_val[(char_to_id[kanji2], char_to_id[kanji])] = count/total
    coords, values = zip(*coord_to_val.items())
    i_index, j_index = zip(*coords)
    if empty_cols and fill_deadends:
        M = csr_matrix((values, (i_index, j_index)), 
                       shape=(len(elem_dict), len(elem_dict)))
        M = M.tolil()
        for row in empty_cols:
            M[:, row] += filler
        return M.tocsr(), empty_cols
    else:
        return csr_matrix((values, (i_index, j_index)), 
                          shape=(len(elem_dict), len(elem_dict))), empty_cols

def plot_sparce_analysis(sparse_matrix, 
                         title='Sparse analysis of the morphological\n'
                         'relations between Kanji and radicals',
                         markersize=0.2,
                         jk_size=2136):
    plt.spy(sparse_matrix, markersize=markersize)
    mat_size = sparse_matrix.shape[0]
    plt.plot((0, mat_size), (jk_size, jk_size), color='r', linestyle='--')
    plt.plot((jk_size, jk_size), (0, mat_size), color='r', linestyle='--')
    plt.title(title)
    plt.xlabel('Index of character')
    plt.ylabel('Index of character')
    plt.tight_layout()

def page_rank(sparse_matrix, difference_threshold=1e-12, beta=0.85, 
              jump=None):
    curr_dif = np.inf
    size = sparse_matrix.shape[0]
    jump = np.ones(size)/size if jump is None else jump
    importance = np.ones(size)/size
    start = time.clock()
    while curr_dif > difference_threshold:
        new_importance = beta * sparse_matrix * importance + (1 - beta) * jump
        curr_dif = abs(new_importance - importance).sum()
        importance = new_importance
    print('Total elapsed time: %g seconds' % (time.clock() - start))
    return importance

def evaluate_result(importance, id_to_char, char_to_id, jk_size=2136, 
                    title='', ylabel='', xlabel=''):
    kanji_importance = list(zip(id_to_char, importance))
    kanji_importance = [x for x in kanji_importance if x[0] in IS.jk_set]
    kanji_importance = sorted(kanji_importance, key=lambda x: -x[1])
    toolbox.scatter(importance, marker='.', s=2, high_dpi=False)
    top = max(importance) + 0.001
    bottom = -0.001
    plt.plot((jk_size, jk_size), (bottom, top), color='r', linestyle='--')
    plt.ylim([bottom, top])
    plt.title(title)
    plt.ylabel(ylabel)
    plt.xlabel(xlabel)
    char_to_new_id = {k_i[0]: i for i, k_i in enumerate(kanji_importance)}
    kanji_diff = [(kanji, char_to_new_id[kanji] - char_to_id[kanji])
                  for kanji, importance in kanji_importance]
    # toolbox.save_data(kanji_diff, '../data/temp.csv')
    return kanji_diff

def morpho_flow():
    morpho, id_to_char, char_to_id, freqs = create_morphological_graph()
    sp, gaps = build_sparse_matrix(morpho, char_to_id, freqs)
    result = page_rank(sp, jump=freqs)
    kanji_diff = evaluate_result(result, id_to_char, char_to_id, 
                                 title='Importance of Kanji and Radicals\nbased on the morphological graph',
                                 xlabel='Index of Kanji',
                                 ylabel='Importance of character')
    toolbox.save_data(kanji_diff, '../data/morpho_ordering.csv')
    generate_latex_table(kanji_diff)

def cooc_flow(use_log=False):
    cooc, id_to_char, char_to_id, freqs = create_coocurrence_graph(use_log=use_log)
    sp, gaps = build_sparse_matrix(cooc, char_to_id, freqs)
    result = page_rank(sp, jump=freqs)
    kanji_diff = evaluate_result(result, id_to_char, char_to_id, 
                                 title='Importance of Kanji\nbased on the co-ocurrence graph',
                                 xlabel='Index of Kanji',
                                 ylabel='Importance of Kanji')
    toolbox.save_data(kanji_diff, '../data/cooc_ordering.csv')
    generate_latex_table(kanji_diff)

def generate_latex_table(kanji_diff, number_of_columns=28, caption='Caption', 
                         label='the_label', japanese=True, scale=0.6, jk_size=2136):
    problematics = {'剝': '剥', '𠮟': '叱'}
    latex = r"""\begin{table}[ht]
\centering
\caption{%s}
\label{%s}
\scalebox{%.2f}{
\begin{tabular}{""" % (caption, label, scale)
    latex += 'c' * number_of_columns
    latex += '}\n'
    to_add = []
    for i, elem in enumerate(kanji_diff):
        back_color, font_color = _calculate_colors(elem[1], jk_size)
        preamble = r'\cellcolor[HTML]{%s}' % back_color
        letter = problematics.get(elem[0], elem[0])
        letter = '\jap{%s}' % letter
        letter = '{\color[HTML]{%s} %s}' % (font_color, letter)
        to_add.append('%s%s' % (preamble, letter))
        if ((i + 1) % number_of_columns) == 0:
            latex += ' & '.join(to_add) + r'\\' + '\n'
            to_add = []
    to_add.extend('' for i in range(number_of_columns - len(to_add)))
    latex += ' & '.join(to_add) + '\n'
    latex += r"""\end{tabular}
}
\end{table}"""
    toolbox.save_data([latex], '../data/temp.txt')

def _calculate_colors(number, jk_size, negative=0xff0000, middle=0xffffff,
                     positive=0x0000ff):
    middle_tup = _make_color_tuple(middle)
    negative_tup = _make_color_tuple(negative)
    positive_tup = _make_color_tuple(positive)
    new_tup = []
    if number > 0:
        for m, p in zip(middle_tup, positive_tup):
            new_tup.append(round(m + (p - m) * number / jk_size))
    elif number < 0:
        for m, n in zip(middle_tup, negative_tup):
            new_tup.append(round(m + (m - n) * number / jk_size))
    else:
        new_tup = middle_tup
    num = new_tup[0] * (256**2) + new_tup[1] * 256 + new_tup[2]
    back_color = hex(num)[2:].zfill(6).upper()
    font_color = '000000' if sum(new_tup) > 256*1.75 else 'FFFFFF'
    return back_color, font_color

def _make_color_tuple(colorcode):
    return (colorcode // (256**2), 
            (colorcode % (256**2)) // 256, 
            colorcode % 256)