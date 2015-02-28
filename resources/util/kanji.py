import pymongo
import uri

class Kanji:
    SUBSTITUTE = 0
    APPEND = 1
    EXTEND = 2
    UNSET = 3
    to_db = {'_id': '_id', 'kanji': 'k', 'looks_like': 'll', 'meaning_like': 'ml',
              'contains': 'c', 'grade': 'g', 'is_contained': 'ic', 'master_relation': 'mr',
              'num_strokes': 'ns', 'kun_yomi':'kun', 'on_yomi':'on', 'meaning':'m'}
    to_obj = {v:k for k,v in to_db.items()}
    order = ['_id', 'kanji', 'meaning', 'on_yomi', 'kun_yomi', 'master_relation', 'contains',
             'is_contained', 'looks_like', 'meaning_like', 'grade', 'num_strokes']

    exemplified_fields = {'on_yomi':'on_yomi', 'on':'on_yomi',
                          'kun_yomi': 'kun_yomi', 'kun': 'kun_yomi'}

    def __init__(self, _id, kanji, meaning=None, on_yomi=None, kun_yomi=None,
                 looks_like=None, meaning_like=None, contains=None, is_contained=None,
                 grade='0', master_relation='', num_strokes=0):
        # Obrigatory parameters
        self._id = _id
        self.kanji = kanji
        # 'To be filled later'
        self.grade = grade
        self.num_strokes = num_strokes
        self.master_relation = master_relation
        # 'To be filled later' that are mutable
        self.meaning = meaning if meaning is not None else []
        # Optional parameters (that may not be filled later - radicals and CO)
        self.meaning_like = meaning_like if meaning_like is not None else None
        self.is_contained = is_contained if is_contained is not None else None
        self.contains = contains if contains is not None else None
        self.looks_like = looks_like if looks_like is not None else None
        self.on_yomi = on_yomi if on_yomi is not None else None
        self.kun_yomi = kun_yomi if kun_yomi is not None else None
        # Helpers
        self.modified_fields = []
        self.remove_fields = []

    def minify_keys(self):
        return {Kanji.to_db[k]:v for k,v in vars(self).copy().items()
                if v is not None}

    def __str__(self):
        ans = u""
        for k in self.order:
            if vars(self)[k] is not None:
                ans += str(k) + u": " + str(vars(self)[k]) + u"\n"
        return ans

    @staticmethod
    def get_from_db(_id=None, kanji=None):
        ans = None
        if _id is not None:
            with pymongo.MongoClient(uri.uri) as client:
                ans = client['kanji'].joyou.find_one({'_id': _id})
        elif kanji is not None:
            with pymongo.MongoClient(uri.uri) as client:
                ans = client['kanji'].joyou.find_one({'k': kanji})
        else:
            raise ValueError("The id or the literal must be passed")
        return Kanji(**{Kanji.to_obj[k]:v for k,v in ans.items()})

    def save(self):
        if len(self.modified_fields) == 0 and len(self.remove_fields) == 0:
            raise ValueError("No reason to, nothing changed.")
        else:
            update_doc = dict()
            if self.modified_fields:
                update_doc['$set'] = {Kanji.to_db[k]: vars(self)[k] for k in self.modified_fields}
            if self.remove_fields:
                update_doc['$unset'] = {Kanji.to_db[k]: 1 for k in self.remove_fields}
            with pymongo.MongoClient(uri.uri) as client:
                return client['kanji'].joyou.update({'_id':self._id}, update_doc)

    def update(self, field, value, operation=None):
        if field in vars(self) or field in Kanji.to_obj:
            if field in Kanji.to_obj:
                field = Kanji.to_obj[field]
            if operation is None or operation is self.SUBSTITUTE:
                self.modified_fields.append(field)
                vars(self)[field] = value
            elif operation is Kanji.APPEND:
                self.modified_fields.append(field)
                vars(self)[field].append(value)
            elif operation is Kanji.EXTEND:
                vars(self)[field].extend(field)
            elif operation is Kanji.UNSET:
                self.remove_fields.append(field)
                vars(self)[field] = None
            else:
                raise ValueError("Unsuported operation:", operation)
        else:
            raise ValueError("Invalid Field", field)

    def give_example(self, field, *examples):
        """helper for on and kun fields."""
        if field in self.exemplified_fields:
            field = self.exemplified_fields[field]
            new_reading = []
            it = iter(vars(self)[field])
            for example in examples:
                try:
                    reading = next(it)
                    while reading[1] is not "":
                        new_reading.append(reading)
                        reading = next(it)
                    new_reading.append([reading[0], example])
                except StopIteration:
                    raise ValueError("Too much examples.")
            self.update(field, new_reading)
        else:
            raise ValueError("Invalid field:", field)

