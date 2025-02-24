#include <stdio.h>
#include <stdlib.h>
#include <math.h>

int main()
{
    double num1;
    double num2;

    printf("enter the first number =>");
    scanf("%lf", &num1);

    printf("enter the second number => ");
    scanf("%lf", &num2);

    printf("answer : %lf " , num1 + num2);
    return 0;
}