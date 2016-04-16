import matplotlib.pyplot as plt
from collections import Counter

def visualize_bars(iterable, width=0.5, color='b', counter_feed=False, transformation=lambda x:x):
    plt.ion()
    if counter_feed:
        c = iterable
    else:
        c = Counter(iterable)
    x,y = zip(*c.items())
    plt.bar([n-width/2 for n in x], transformation(y), width=width, color=color)
    plt.grid(True)
    return c
