def a():
    b = 2

    def a2():
        c = b + 2
        b = 2
        c = b

    a2()


a()
