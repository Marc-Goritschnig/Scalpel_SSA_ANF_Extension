def fun(a, b, c):
    x = 2

    def fun3(a, b, c):
        print('a')
        print(a, b)
        return True

    print('a')
    print(a, b)
    fun3(1, 2, 3)
    return True


x = 1
a = 1
a = 2
c = 2
fun()
fun(1)
