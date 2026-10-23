s = "ab"
t = s
s += "c"                      # str is immutable: += rebinds s to a new object
print(s, t, s is t)

lst = [1]
alias = lst
lst += [2]                    # list += extends in place: alias sees it
print(lst, alias, lst is alias)
lst = lst + [3]               # + builds a new list and rebinds lst
print(lst, alias, lst is alias)
