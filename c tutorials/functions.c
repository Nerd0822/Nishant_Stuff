#include <stdio.h>
#include <stdlib.h>

void sayhi(char name[], int age)
{
    printf("hello %s your age is %d\n", name, age);
}
double cube(double num)
{
    double result = num * num * num;

    return result;
}
int main()
{
    sayhi("nishant", 23);
    printf("%lf",cube(3));
    return 0;
}
