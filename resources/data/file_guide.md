## essential_words.csv
A list of words that appear at least once as an example in kanji_and_examples.json.

## file_guide.md
This file.

## jmdict.json
A subset of the JMdict_e.xml file that only contains entries that refer to at least one word that is formed **solely** of hiragana/katakana/Jouyou Kanji.

## jmdict_clean.json
A filtering over jmdict, removing out dated kanji representations and archaisms.

## JMdict_DTD.xml
Just the header of JMdict_e.xml.

## JMdict_e.xml
The full JMdict in English language.

## jmdict_essential.json
A subset of entries from jmdict.json that has entries in essential_words.csv.

## jmndict.json
A filtering, in a similar fashion of jmdict.json, of the JMNdict, a dictionary of names.

## jmndict_filtered.json
A filtering from the names dict that takes out all entries related to first/last personal names.

## jmndict_essential.json
A filtering, in a similar fashion of jmdict_essential.json of the jmndict.json.

## jouyou_kanji.json
The master file of this project, that contains most of the important information about the 2,136 Jouyou Kanji, such as its contents, look-a-likes, meaning and mnemonics.

## kanji_and_examples.json
A mapping from Kanjis to its relevant examples, where its frequency also appears. The examples from the kanji were taken from a filtering of the Japanese Wikipedia word count (present in word_count_filtered.json) that follow three rules:
* Entries should have at least 5 examples (will be less if it doesn't even have this many)
* Entries should have a maximum of 50 examples.
* Examples will stop to be taken if a representation of 80% or more was achieved. For example, let's say X appears 1000 times. If we have examples with this order of occurrences: 200, 200, 100, 100, 100, 50, 50... the first 7 examples would be enough to give us our 80% representation.

## kanji_cdf.csv
A cumulative frequency distribution of the appearance of Kanji, ordered by most common Kanji to least.

## kanji_cdf_grade.csv
Equivalent to kanji_cdf.csv, but with an additional field portraying the grade at which this Kanji is taught in Japan.

## kanji_perc.csv
The percentage of appearance of every Kanji. Used to make the kanji_cdf.json.

## kanji_perc2.csv
Equivalent to kanji_perc.csv, but with an additional field portraying the relative frequency to the percentage if the distribution was homogeneous.

## kanjidic2.xml
The kanjidic project, used to take information from Kanji such as stroke count, some meanings, grade and etc.

## kanjivg.xml
The Kanjivg project, used to take stroke order from the kanji.

## radicals.json
Equivalent to the jouyou_kanji.json, but contains information of radicals used to describe some of the Jouyou Kanji.

## word_count_filtered.csv
Word count from the Japanese Wikipedia counting that contain at least one Jouyou Kanji.

## word_count_filtered_in_dicts.csv
Entries from the word_count_filtered.csv that appear either in JMdict or JMNdict.

## word_count_filtered_teacheable.csv
A filtering that maintains only entries that are composed purely of hiragana, katakana and Jouyou Kanji, therefore taking out totally alien characters as alfa and beta and Kanjis outside from the Jouyou Kanji.

## words_in_dict.csv
A list of words that appear in either JMdict or JMNdict(filtered version).
