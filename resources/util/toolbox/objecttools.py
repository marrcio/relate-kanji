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
