import collections

def dict_by_field(list_of_objects, field, transformation=lambda x:x, list_mode=False):
    """Indexes one of the fields of each object, returns a single dictionary"""
    if list_mode:
        field = int(field)
    return {transformation(entry[field]):entry for entry in list_of_objects}

def remove_duplicates(iterable):
    """Removes duplicates of an iterable without meddling with the order"""
    seen = set()
    seen_add = seen.add # for efficiency, local variable avoids check of binds
    return [x for x in iterable if not (x in seen or seen_add(x))]

def condense_duplicates_dict(list_of_lists):
    """Transforms a list of lists to a dictionary.

    Duplicates in the first element(list[0]) are condensed to a single key,
    contents are fused together by making dict[key].expand(list[1:])
    """
    ans = dict()
    for group in list_of_lists:
        if group[0] not in ans:
            ans[group[0]] = group[1:]
        else:
            ans[group[0]].extend(group[1:])
    return ans

def create_json_lines(dictionary):
    """Creates Json lines from one big dictionary"""
    return [{k:v} for k,v in dictionary.items()]

def compare_dicts(first, second, fine_if_wrong=None):
    """Compare two dictionaries, based on their key, value pairs."""
    total_keys = len(set(first.keys()) | set(second.keys()))
    if fine_if_wrong is None: fine_if_wrong = set()
    resemblance = 0
    differences = dict()
    for key, value in first.items():
        if key not in second or key in fine_if_wrong or second[key] == value:
            resemblance += 1
        elif key in second and second[key] != value:
            differences[key] = (value, second[key])
    for key, value in second.items():
        if key not in first:
            resemblance += 1
    # How I love python3 division... S2
    resemblance /= total_keys
    return resemblance, differences

def compare_strings(first, second):
    """Compare two strings, returning the point of divergence and the equality"""
    big = max(len(first), len(second))
    small = min(len(first), len(second))
    if big == small:
        pairs = [(x,y) for x, y in zip(first, second)]
    else:
        pairs = [(x,y) for i, (x, y) in enumerate(zip(first, second))
                 if i < small - 1]
        pairs.append((first[small - 1:], second[small - 1:]))
    resemblance = sum(x == y for x, y in pairs) / big
    differences = [(x,y) for x,y in pairs if x != y]
    return resemblance, differences

def make_ordered_dict(dictionary, order_list):
    od = collections.OrderedDict()
    for key in order_list:
        od[key] = dictionary[key]
    return od