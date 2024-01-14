def fun(a, b, c):
    x = 2
    def fun3(a, b, c):
        print('a')
        print(a, b)
        return True
    print('a')
    print(a, b)
    return True


def fun2(a, b):
    print(b)
    print(a, b)
    def fun3(a, b, c):
        print('a')
        print(a, b)
        return True

x = 1
a = 1
c = 2
fun()
fun2(1)
