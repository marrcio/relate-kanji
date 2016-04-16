import toolbox as tb
from statistics import Statistics
from collections import defaultdict
import matplotlib.pyplot as plt
plt.ion()
S = Statistics()

entries = tb.load_data(tb.IP.JMDICT_UNWINDED)
kanji_to_results = defaultdict(list)

for entry in entries:
    kanji_to_results[entry['k_ele']['keb']].append(entry)

big_entries = sorted([v for v in kanji_to_results.values() if len(v) > 1], key=lambda x: -len(x))

for k, l in kanji_to_results.items():
    just_priorities = [entry for entry in l if 'ke_pri' in entry['k_ele']] or l
    no_dial = ([entry for entry in just_priorities if any('dial' not in s for s in entry['sense'])]
               or just_priorities)
    kanji_to_results[k] = no_dial


small_entries = sorted([v for v in kanji_to_results.values() if len(v) > 1], key=lambda x: -len(x))

# def show_comparison(step, window_size=50, width=0.7):
#     plt.bar([n-width/2 for n in range(len(big_entries[step:step + window_size]))],
#             [len(x) for x in big_entries[step:step + window_size]],
#             width=width, color='b')

#     plt.bar([n-width/2 for n in range(len(small_entries[step:step + window_size]))],
#             [len(x) for x in small_entries[step:step + window_size]],
#             width=width, color='r')
#     plt.xlim([-1,50])
#     plt.ylim([0,7])

# for step in range(0,len(big_entries), 50):
#     print("Looking from %d to %d" % (step, step+50))
#     show_comparison(step)
#     input()
#     plt.cla()

def collect_
