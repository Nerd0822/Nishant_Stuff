#include <stdio.h>
#include <stdlib.h>

int main()
{
    char color[20];
    char plural_noun[20];
    char fname[20];
    char sname[20];

    printf("enter a color: ");
    scanf("%s", color); // no need of & when a string
    printf("enter a plural_noun: ");
    scanf("%s", plural_noun);
    printf("enter a name: ");
    scanf("%s %s", fname, sname);

    printf("roses are %s\n", color);
    printf("%s are blue\n", plural_noun);
    printf("i love %s %s", fname, sname);
    return 0;
}