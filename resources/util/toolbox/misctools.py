step = None

def _paced_return_generator(container, size=1):
    it = iter(container)
    while True:
        result = []
        for i in range(size):
            try:
                result.append(next(it))
            except StopIteration:
                break
        yield result

def paced(container, size=1):
    global step
    step = _paced_return_generator(container, size)
    return next(step)

def walk():
    return next(step)

