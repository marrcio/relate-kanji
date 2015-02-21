class Kanji:
    to_db = {'_id': '_id', 'kanji': 'k', 'looks_like': 'll', 'meaning_like': 'ml',
              'contains': 'c', 'grade': 'g', 'is_contained': 'ic', 'master_relation': 'mr',
              'frequency': 'f', 'num_strokes': 'ns'}
    to_obj = {v:k for k,v in to_db.items()}

    def __init__(self, _id, kanji, looks_like=None, meaning_like=None, contains=None, grade='0',
                 is_contained=None, master_relation='', frequency=0, num_strokes=0):
        self._id = _id
        self.kanji = kanji
        self.grade = grade
        self.master_relation = master_relation
        self.frequency = frequency
        self.num_strokes = num_strokes
        self.meaning_like = meaning_like if meaning_like is not None else []
        self.is_contained = is_contained if is_contained is not None else []
        self.contains = contains if contains is not None else []
        self.looks_like = looks_like if looks_like is not None else []

    def minify_keys(self):
        return {Kanji.to_db[k]:v for k,v in vars(self).copy().items()}
