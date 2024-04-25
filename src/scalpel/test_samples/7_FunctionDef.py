# Pos not working
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


# vararg not working
def fun4(a, *b):
    pass


# kwarg not working
def fun5(a, **b):
    pass



fun4(1, *b)
fun5(1, **c)
# Keyword after named parameter not working
fun4(a=1, *b)
fun5(a=1, **c)