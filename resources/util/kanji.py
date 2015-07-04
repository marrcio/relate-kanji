class Kanji:
    minify_map = {'kanji': 'k', 'meaning':'m', 'on_yomi':'on', 'kun_yomi':'kun',
                  'master_relation': 'mr', 'contains': 'c', 'contains_all': 'ca',
                  'is_contained': 'ic', 'is_contained_all': 'ica', 'looks_like': 'll',
                  'grade': 'g', 'strokes': 'ns', 'value': 'v', 'rank': 'r', 'cdf': 'cd'}
    verbose_map = {v:k for k,v in minify_map.items()}
    order = ['kanji', 'meaning', 'on_yomi', 'kun_yomi', 'master_relation', 'contains',
             'contains_all', 'is_contained', 'is_contained_all', 'looks_like',
             'grade', 'strokes', 'value', 'rank', 'cdf']

    def __init__(self, kanji, meaning=None, on_yomi=None, kun_yomi=None,
                 master_relation='', contains=None, contains_all=None,
                 is_contained=None, is_contained_all=None, looks_like=None,
                 grade='0', strokes=0, value=0, rank=-1, cdf=0):
        # Obrigatory parameters
        self.kanji = kanji
        # Placeholders parameters
        self.master_relation = master_relation
        self.grade = grade
        self.strokes = strokes
        self.value = value
        self.rank = rank
        self.cdf = cdf
        # Placeholders that are mutable
        self.meaning = meaning if meaning is not None else []
        self.on_yomi = on_yomi if on_yomi is not None else []
        self.kun_yomi = kun_yomi if kun_yomi is not None else []
        self.contains = contains if contains is not None else []
        self.contains_all = contains_all if contains_all is not None else []
        self.is_contained = is_contained if is_contained is not None else []
        self.is_contained_all = is_contained_all if is_contained_all is not None else []
        self.looks_like = looks_like if looks_like is not None else []

    def get_minified_object(self):
        return {Kanji.minify_map[k]:v for k,v in vars(self).copy().items()
                if v is not []}

    def get_verbose_object(self):
        return {k:v for k,v in vars(self).copy().items()}

    def __str__(self):
        ans = u""
        for k in self.order:
            if vars(self)[k] is not None:
                ans += str(k) + u": " + str(vars(self)[k]) + u"\n"
        return ans
