#include <stdio.h>
#include <stdlib.h>

int sortArray(int arr[10])
{
    for (int t = 0; t < 10; t++)
    {
        for (int i = 0; i < 9; i++)
        {
            if (arr[i] > arr[i + 1])
            {
                int temp1 = arr[i + 1];
                int temp2 = arr[i];
                arr[i] = temp1;
                arr[i + 1] = temp2;
                printf("%d %d\n", temp1, temp2);
            }
        }
    }
    return arr[10];
}
int printArray(int arr[10])
{
    printf("printing the array\n");
    printf("[ ");
    for (int j = 0; j < 9; j++)
    {

        printf("%d ,", arr[j]);
    }
    printf(" ]");
    return 0;
}
int main()
{
    int arr[10] = {8, 9, 5, 4, 3, 1, 6, 2, 7, 0};
    sortArray(arr);
    printArray(arr);
}
// why the 9 is not printing