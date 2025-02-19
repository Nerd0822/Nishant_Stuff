#include <stdio.h>

int main()
{
    // basic datatypes

    int num = 9;
    float decimal = 9.987;
    double longer_decimal = 9.99999;
    char letter = 'n';
    
    // derived datatypes
    char name[] = "nishant";


    printf("%d,%f,%.8lf,%c,%s",num,decimal,longer_decimal,letter,name);

    return 0;
}