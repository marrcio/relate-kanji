from structures import IP, IS
import matplotlib.pyplot as plt
import toolbox
from collections import Counter

def make_components_graphs(minimum=False):
	if minimum:
		components_c = Counter([
			component for value in IS.jk_d.values() for component in value.get('c+', value['c'])])	
	else:
		components_c = Counter([
			component for value in IS.jk_d.values() for component in value['c']])
	component_counts = [tup for tup in components_c.items()]
	component_counts = sorted(component_counts, key=lambda x: -x[1])
	component_internal = [tup for tup in component_counts if tup[0] in IS.jk_set]
	component_external = [tup for tup in component_counts if tup[0] not in IS.jk_set]
	subtitles = ['Full view', 'Only Jouyou Kanji Components', 'Only Radical Components']
	component_lists = [component_counts,
					   component_internal,
					   component_external]
	for component_pair, subtitle in zip(component_lists, subtitles):
		Kanji, Count = zip(*component_pair)
		plt.figure()
		toolbox.scatter(Count, high_dpi=False, marker='.')
		plt.title('Number of Kanji that share a same component\n' + subtitle)
		plt.ylabel('Number of Kanji')
		plt.xlabel('Index of component')
	return component_lists

def make_histograms():
	toolbox.visualize_bars([len(jk['c']) for jk in IS.jk], high_dpi=False)
	plt.title('Number of Components in Jouyou Kanji')
	plt.ylabel('Number of Kanji')
	plt.ylabel('Number of Components')
	plt.figure()
	toolbox.visualize_bars([len(jk.get('c+', jk['c'])) for jk in IS.jk], high_dpi=False)
	plt.title('Number of Minimum Components in Jouyou Kanji')
	plt.ylabel('Number of Kanji')
	plt.ylabel('Number of Components')