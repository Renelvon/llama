#include <stdbool.h>
#include <stdio.h>
#include <math.h> 

typedef void unit;

unit print_int(int n){
    printf("%d", n);
}

unit print_bool(bool b){
    if (b)
        printf("true");
    else
        printf("false");
}

unit print_char(char c){
    printf("%c", c);
}

unit print_float(double d){
    printf("%lf", d);
}

unit print_string(const char* s){
    printf("%s", s);
}

int read_int(){
    int n;
    scanf("%d", &n);
    return n;
}

bool read_bool(){
    int n;
    bool b;
    scanf("%d", &n);
    b = n;
    return b;
}

char read_char(){
    return (char)getchar();
}

double read_float(){
    double d;
    scanf("%lf", &d);
    return d;
}

unit read_string(char* s, int n){
    char temp;
    
    for(int i = 0; i < n; ++i){
        temp = (char)getchar();
        if (temp != '\n')
            s[i] = temp;
    }
}

int abs(int n){
    return abs(n);
}

double fabs(double n){
    return fabs(n);
}

unit incr(int *n){
    (*n)++;
}

unit decr(int *n){
    (*n)--;
}

double float_of_int(int n){
    return (double)n;
}

int int_of_float(double d){
    return (double)d;
}

