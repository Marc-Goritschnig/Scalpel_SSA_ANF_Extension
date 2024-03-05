for a in range(2):
    print(a)
    for b in range(3):
        print(b)
        for c in range(4):
            print(c)
    print(c)
print('a')
for j, clf in enumerate(clfs):
    for i, (train, test) in enumerate(skf):
        print("Fold", i)