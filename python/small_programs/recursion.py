def factorial(n):
    if n==0:
        return 0
    elif n==1:
        return 1
    else:
        return n*factorial(n-1)
    
def fibonacci(n):
    if n<0:
        return 0
    elif n==1:
        return 0
    elif n==2:
        return 1
    else:
        return fibonacci(n-1)+fibonacci(n-2)
    
    
n=int(input("enter a valid number => "))

print("this is factorial",factorial(n),"this is fibonacci ",fibonacci(n))