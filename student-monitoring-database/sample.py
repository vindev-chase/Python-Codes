import math

def get_area():
    while True:
#Input
        r = input("Please enter the radius of the circle")
# Make a judgement. If it is a string, then re-enter
        if not r.isalpha():
      #Data processing
                r = float(r)
                s = math.pi*r**2
      #Result output
                print(f"The area of the circle is: {s:.2f}")
        break
    else:
        print("Your input format is incorrect. Please re-enter!")

def even_print():
    k = [n for n in range(1, 101) if n%2 == 0]
    print(k)

get_area()