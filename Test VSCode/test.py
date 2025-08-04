
def testprog():
    x = input("Enter x: ")
    y = input("Enter y: ")

    res = int(x) + int(y)
    print(f"Sum of x and y is: {res}")

    if(res < 4):
        testprog()

testprog()
    