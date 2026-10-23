t = ([1],)
t[0].append(2)                # allowed: the tuple still holds the same list
print(t)
try:
    t[0] += [3]               # extends the list in place, then fails storing into the tuple
except TypeError as e:
    print("TypeError")
print(t)
try:
    {t: 1}
except TypeError:
    print("unhashable key")
