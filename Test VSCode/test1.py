
def testprog():
    x = input("Enter value for x: ")
    y = input("Enter value for y: ")
    res = int(x) + int(y)

    print(f"Value for x & y is: {res}")

    if (res < 10):
        testprog()

testprog()