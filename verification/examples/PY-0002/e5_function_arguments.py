def rebind(items):
    items = [0]               # rebinds the local name only
    return items

def mutate(items):
    items.append(0)           # changes the caller's object

data = [1]
rebind(data)
print(data)
mutate(data)
print(data)


def add_bad(x, bucket=[]):
    bucket.append(x)
    return bucket

print(add_bad(1), add_bad(2), add_bad.__defaults__)


def add_good(x, bucket=None):
    if bucket is None:
        bucket = []
    bucket.append(x)
    return bucket

print(add_good(1), add_good(2), add_good.__defaults__)
