x = [1,2,3,4,5]
y = [i + y for i in x for y in x]
print(y)