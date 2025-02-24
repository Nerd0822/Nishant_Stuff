#include <stdio.h>
#include <stdlib.h>

int main()
{
    int luckynums[10] = {}; // making a array 

    for (int i = 0; i<10;i++)
    {
        luckynums[i]=i;
        
    }
    for (int j = 0; j<=10;j++)
    {
        printf("%d\n",luckynums[j]);

    }
    return 0;


}