main = [0.801]
beta = [0.85 + 0.001 * i for i in range(1, 5)]

class static:
    pass

supporting = [*main, *beta]
supporting.sort()
supporting = [static, *supporting]