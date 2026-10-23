import copy

nested = [[1, 2], [3]]
shallow = copy.copy(nested)
deep = copy.deepcopy(nested)
nested[0].append(99)
print(shallow, deep)
print(shallow is nested, shallow[0] is nested[0], deep[0] is nested[0])
print(nested[:][0] is nested[0], nested.copy()[0] is nested[0])

trap = [[]] * 3
trap[0].append("x")
print(trap, trap[0] is trap[1])
ok = [[] for _ in range(3)]
ok[0].append("x")
print(ok)

loop = []
loop.append(loop)
dup = copy.deepcopy(loop)
print(dup is not loop, dup[0] is dup)
