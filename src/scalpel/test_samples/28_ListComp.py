x = [1, 2, 3, 4, 5]
y = [i if i == 1 else i + i for i in x for y in [1, 2, 3, 4, 5]]
y = [i.b() if i == 1 else i + i for i in x for y in [1, 2, 3, 4, 5]]
print(y)
