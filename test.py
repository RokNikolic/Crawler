if __name__ == "__main__":
    a = range(10)
    b = range(20)

    a_iter = iter(a)
    b_iter = iter(b)

    for i, j in zip(a_iter, b_iter):
        print(i, j)
        if i > 5:
            print(list(a_iter))

