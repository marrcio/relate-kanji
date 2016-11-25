import matplotlib.pyplot as plt
from collections import Counter

plt.ion()

def visualize_bars(iterable, width=0.5, color='b', counter_feed=False, high_dpi=True, transformation=lambda x:x):
    if counter_feed:
        c = iterable
    else:
        c = Counter(iterable)
    if high_dpi:
        plt.figure(dpi=200)
    x,y = zip(*c.items())
    plt.bar([n-width/2 for n in x], transformation(y), width=width, color=color)
    plt.grid(True)
    ax = plt.axes()
    rects = ax.patches
    for rect, number in zip(rects, y):
        height = rect.get_height()
        ax.text(rect.get_x() + rect.get_width()/2, height + 5, '%d' % number, ha='center', va='bottom')
    return c


def plot(X, Y=None, high_dpi=True, start_on_one=False, **kwargs):
    if high_dpi:
        plt.figure(dpi=200)
    if Y:
        plt.plot(X, Y, **kwargs)
    elif start_on_one:
        plt.plot(range(1, len(X) + 1), X, **kwargs)
    else:
        plt.plot(X, **kwargs)


def scatter(X, Y=None, high_dpi=True, dilog=False, **kwargs):
    if high_dpi:
        plt.figure(dpi=200)
    if Y:
        plt.scatter(X, Y, **kwargs)
    else:
        # if no Y is given, we actually want no X:
        Y = X
        X = range(1, len(X) + 1)
        plt.scatter(X, Y, **kwargs)
    if dilog:
        plt.xscale('log')
        plt.yscale('log')

def reference(ref, scatter=False, xmode=False, **kwargs):
    """Draws a reference line to the closest point to X"""
    axes = plt.gca()
    xy = axes.collections[0].get_offsets() if scatter else axes.get_lines()[0].get_xydata()
    for x, y in xy:
        if xmode:
            if x >= ref:
                break
        else:
            if y >= ref:
                break
    plt.plot((0, x), (y, y), **kwargs)
    plt.plot((x, x), (0, y), **kwargs)
    plt.xticks(list(plt.xticks()[0]) + [x])
    plt.yticks(list(plt.yticks()[0]) + [y])
    return (x, y)