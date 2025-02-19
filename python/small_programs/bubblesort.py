import random 
import time
def bubblesort(arr):
    n=len(arr)
    for i in range(n):
        for j in range(n-i-1):
            if arr[j]>arr[j+1]:
                arr[j],arr[j+1]=arr[j+1],arr[j]

def sortingALGO(arr,newarr):
    min=0
    for i in arr:
        if i<min:
            min=i
            newarr.append(min)


arr=[]
for i in range(99):
    ele=random.randint(1,100)
    arr.append(ele)

newarr=[]

print(arr)

# bubblesort(arr)
sortingALGO(arr,newarr)
print()
print("this is the sorted array")
print()
# print(arr)
print(newarr)