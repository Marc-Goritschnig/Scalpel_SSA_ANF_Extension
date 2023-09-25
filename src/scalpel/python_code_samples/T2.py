import math

while True:
    line = input("enter 3d vector: ")
    xs = line.split(",")
    if len(xs) == 3:
        break
    else:
        print("please try again.")

[x, y, z] = map(int, xs)
n = math.sqrt(x ** 2 + y ** 2 + z ** 2)
print(f"vector length: {n}")
