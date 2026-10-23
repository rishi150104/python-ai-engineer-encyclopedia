a = [1, 2]
b = [1, 2]
c = a
print(a == b, a is b, a is c, id(a) == id(c))

nan = float("nan")
print(nan == nan, nan is nan, [nan] == [nan], nan in [nan])

x = None
print(x is None, x == None)
