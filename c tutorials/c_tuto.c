#include <stdio.h> // header files
#include <stdlib.h>
#include <math.h> // header files for mathemetical operations

void datatypes() // datatypes
{
    int integer = 99;
    float num = 9.99;
    double gpa = 3.33333333333333;

    char grade = 'a';
    char name[99] = "nishant";

    printf("my name is %s and my gpa is %.15lf and my grade is %c", name, gpa, grade);
}
void working_with_num()
{
    printf("%.2f\n", pow(5, 2)); // num , power
    printf("%f\n", sqrt(2));     // to find squareroot
    printf("%f\n", ceil(3.9));   // round up the number 3.9 = 4
    printf("%f\n", floor(3.9));  // round down the number 3.9 = 3
}
int main() //------------------------main method-----------------
{

    // datatypes();
    printf("\n");
    working_with_num();
}