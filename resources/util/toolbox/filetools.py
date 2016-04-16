import json
import csv
from pathlib import Path
from collections import OrderedDict

def load_data_safe(filename, delimiter=','):
    data = load_data(filename, False, delimiter)
    p = Path(filename)
    bkp_filename = str(p.with_name(p.stem + '_bkp' + p.suffix))
    save_data(data, bkp_filename, delimiter)
    return data

def load_data(filename, iterable=False, delimiter=','):
    ext = Path(filename).suffix
    if ext == '.json':
        if iterable:
            return base_iter_loader(filename, transformation= lambda x:
                                    json.loads(x, object_pairs_hook=OrderedDict))
        else:
            return base_loader(filename, transformation= lambda x:
                               json.loads(x, object_pairs_hook=OrderedDict))
    elif ext == '.csv' or ext == '.tsv':
        if iterable:
            return csv_iter_loader(filename, delimiter)
        else:
            return csv_loader(filename, delimiter)
    else:
        if iterable:
            return base_iter_loader(filename)
        else:
            return base_loader(filename)

def save_data(data, filename, delimiter=',', ordered_keys=False):
    ext = Path(filename).suffix
    if ext == '.json':
        return base_saver(data, filename,
                          transformation=lambda x: json.dumps(x, ensure_ascii=False,
                                                              sort_keys=ordered_keys))
    elif ext == '.csv':
        return csv_saver(data, filename, delimiter)
    else:
        return base_saver(data, filename)

def base_loader(filename, transformation=lambda x:x):
    holder = []
    with open(filename) as f:
        for i, line in enumerate(f):
            try:
                holder.append(transformation(line))
            except ValueError:
                raise ValueError("Error to load at line %d" % i+1)
    return holder

def base_iter_loader(filename, transformation=lambda x:x):
    with open(filename) as f:
        for i, line in enumerate(f):
            try:
                yield transformation(line)
            except ValueError:
                raise ValueError("Error to load at line %d" % i+1)

def base_saver(data, filename, transformation=lambda x:x):
    with open(filename, 'w') as f:
        f.writelines(transformation(x)+'\n' for x in data)


def csv_loader(filename, delimiter):
    holder = []
    with open(filename) as f:
        reader = csv.reader(f, delimiter=delimiter)
        for row in reader:
            holder.append(row)
    return holder

def csv_iter_loader(filename, delimiter):
    with open(filename) as f:
        reader = csv.reader(f, delimiter=delimiter)
        for row in reader:
            yield row

def csv_saver(data, filename, delimiter):
    with open(filename, 'w', newline='') as f:
        writer = csv.writer(f, delimiter=delimiter)
        for row in data:
            if type(row) == str:
                writer.writerow([row])
            else:
                writer.writerow(row)

def pipe_filter(in_file, out_file, filter_f, **kwargs):
    source = load_data(in_file, iterable=True, **kwargs)
    save_data(filter(filter_f, source), out_file, **kwargs)

def pipe_transform(in_file, out_file, transformation, **kwargs):
    source = load_data(in_file, iterable=True, **kwargs)
    save_data(map(transformation, source), out_file, **kwargs)
