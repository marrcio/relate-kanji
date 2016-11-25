import itertools
from structures import IP, IS
import matplotlib.pyplot as plt
import toolbox

def make_frequency_cdf(precision=2):
    kcg = toolbox.load_data('../data/kanji_cdf_grade_novels.csv')
    Kanji, Prob, Grade = zip(*kcg)
    toolbox.plot(Prob, start_on_one=True)
    xs = []
    ys = []
    for freq in [0.25, 0.50, 0.75, 0.90, 0.95, 0.99]:
        x, y = toolbox.reference(freq, linestyle='--', color='r')
        xs.append(x)
        ys.append('{1:.{0}f}'.format(precision, y))
    plt.xticks(xs + [2136])
    plt.xlim((0, 2200))
    ys = [float(y) for y in ys]
    plt.yticks(ys)
    plt.title('Cumulative Distribution Function graph for Kanji\noccurence in Japanese Novels')
    plt.ylabel('Probability')
    plt.xlabel('Kanji index (starts on one)')

def make_grade_cdf(grade_references=True, comparison=True, best_case=True, precision=3):
    xs = []
    ys = []
    kfg = toolbox.load_data('../data/kanji_freq_grade_novels.csv')
    if best_case:
        kfg_bygrade = sorted(kfg, key=lambda x: (int(x[2]), -float(x[1])))
    else:
        kfg_bygrade = sorted(kfg, key=lambda x: (int(x[2]), float(x[1])))
    for tup in kfg_bygrade:
        tup[1] = float(tup[1])
    for behind, front in zip(kfg_bygrade, kfg_bygrade[1:]):
        front[1] += behind[1]
    Kanji, GradeProb, Grade = zip(*kfg_bygrade)
    toolbox.plot(GradeProb, start_on_one=True, label='By grade')
    if comparison:
        kcg = toolbox.load_data('../data/kanji_cdf_grade_novels.csv')
        Kanji, Prob, Grade = zip(*kcg)
        toolbox.plot(Prob, start_on_one=True, high_dpi=False, label='By frequency') # High DPI creates a new figure
        plt.legend(loc=4)
        if best_case:
            plt.title('Comparison of cdfs by Japanese grade\n and by pure frequency (best case)')
        else:
            plt.title('Comparison of cdfs by Japanese grade\n and by pure frequency (worst case)')
    else:
        if best_case:
            plt.title('Cumulative Distribution Function by grade for Kanji\noccurence in Japanese Novels (best case)')
        else:
            plt.title('Cumulative Distribution Function by grade for Kanji\noccurence in Japanese Novels (worst case)')
    if grade_references:
        for rank in itertools.accumulate([80, 160, 200, 200, 185, 181]):
            x, y = toolbox.reference(rank, xmode=True, linestyle='--', color='r')
            xs.append(x)
            ys.append('{1:.{0}f}'.format(precision, y))
    else:
        for freq in [0.25, 0.50, 0.75, 0.90, 0.95, 0.99]:
            x, y = toolbox.reference(freq, linestyle='--', color='r')
            xs.append(x)
            ys.append('{1:.{0}f}'.format(precision, y))
    ys = [float(y) for y in ys]
    plt.xticks(xs + [2136])
    plt.yticks(ys)
    plt.ylabel('Probability')
    plt.xlabel('Kanji index (starts on one)')
    if not grade_references and not best_case:
        xt = list(set(plt.xticks()[0]) - {2136})
        plt.xticks(xt, rotation='vertical')
    plt.ylim([0,1])
    plt.xlim([0,2200])

def make_word_distribution(log=False, filtered=False, lower=1):
    if filtered:
        count_words = toolbox.load_data('../data/word_count_filtered.csv')    
    else:
        count_words = toolbox.load_data('../data/word_count_novels.csv')
    if not filtered:
        count_words = [x for x in count_words if int(x[0]) > lower]
    Counts, Words = zip(*count_words)
    toolbox.scatter(Counts, marker='.')
    if log:
        plt.xscale('log')
        plt.yscale('log')
    if filtered:
        title = 'Count of words containing Kanji in Japanese novels'
    else:
        title = 'Count of word occurrence in Japanese novels'
    xlabel = 'Index of word'
    ylabel = 'Number of occurrences of word'
    if log:
        title = 'Log-Log of ' + title
        xlabel = 'Log of ' + xlabel
        ylabel = 'Log of ' + ylabel
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)

def make_kanji_distribution(log=False):
    Counts = []
    kanji_and_examples = toolbox.load_data(IP.KANJI_AND_EXAMPLES)
    for line in kanji_and_examples:
        for k, v in line.items():
            if k in IS.jk_set:
                Counts.append(v['value'])
    toolbox.scatter(Counts, marker='.')
    if log:
        plt.xscale('log')
        plt.yscale('log')
    title = 'Count of Kanji occurrence in Japanese novels'
    xlabel = 'Index of Kanji'
    ylabel = 'Number of occurrences of Kanji'
    if log:
        title = 'Log-Log of ' + title
        xlabel = 'Log of ' + xlabel
        ylabel = 'Log of ' + ylabel
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)

def produce_zipfian(alpha=1, beta=2.7, size=100000):
    Y = [100*size/(i + beta)**alpha for i in range(1, size+1)]
    toolbox.scatter(Y, dilog=True, marker='.')
    plt.title('Near-zipfian distribution for alpha=%g and beta=%g' % (alpha, beta))
    plt.ylabel('Log of number of occurrences')
    plt.ylabel('Log of element index')


def create_ordering(linesize=8):
    ans = ''
    line = []
    cwg = toolbox.load_data('../data/kanji_cdf_grade_novels.csv')
    Kanji, Perc, Grade = zip(*cwg)
    for i, k, in enumerate(Kanji):
        line.append('%d: \jap{%s}' % (i+1, k))
        if (i+1) % linesize == 0:
            ans += ' & '.join(line)
            ans += r'\\'
            ans += '\n'
            line = []
    return ans