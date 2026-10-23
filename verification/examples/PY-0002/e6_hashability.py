from dataclasses import dataclass, field


class Point:
    def __init__(self, x):
        self.x = x

    def __eq__(self, other):
        return self.x == other.x


print(Point.__hash__ is None)
try:
    {Point(1): "a"}
except TypeError:
    print("Point is unhashable")

print({1: "a"}.get(1.0), {True: "t"}.get(1))

try:
    @dataclass
    class Bad:
        tags: list = []
except ValueError:
    print("dataclass rejects mutable default")


@dataclass
class Good:
    tags: list = field(default_factory=list)


print(Good().tags is Good().tags)
