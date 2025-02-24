#include <stdio.h> // header files
#include <stdlib.h>
#include <math.h> // header files for mathemetical operations

void datatypes(void) // datatypes
{
    int integer = 99;
    float num = 9.99;
    double gpa = 3.123456789;

    char grade = 'a';
    char name[99] = "nishant";

    printf("my name is %s and my gpa is %.15lf and my grade is %c \n", name, gpa, grade);
}
void working_with_num()
{
    printf("%.2f\n", pow(5, 2)); // num , power
    printf("%f\n", sqrt(2));     // to find squareroot
    printf("%f\n", ceil(3.9));   // round up the number 3.9 = 4
    printf("%f\n", floor(3.9));  // round down the number 3.9 = 3
}
void constant()
{
    const int num = 9;
    printf("%d\n", num);
}
void get_user_input()
{
    int age;

    printf("please enter your age => ");
    scanf("%d", &age);

    printf("your age is %d", age);
}
void string()
{
    char name[20];
    // printf("enter your name => ");
    // scanf("%s", name);

    // printf("your name is %s\n", name);

    printf("this is using the fgets function \n");
    // can acces the whole name and from the stdin(the console that takes our input)
    printf("enter your name => ");
    fgets(name, 20, stdin); // must be used in place of scanf
    printf("your name is %s abvcd", name);
}
int main() //------------------------main method-----------------
{

    // datatypes();
    // working_with_num();
    // constant();
    // get_user_input();
    string();
    return 0;
}