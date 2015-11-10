#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <math.h> 

typedef void unit;

// ERROR REPORTING
unit check_err(int ret, const char *s) {
    if (ret < 0){
        perror(s);
        exit(EXIT_FAILURE);
    }
}

// PRINTING TO STDOUT
unit print_int(int n){
    int ret = printf("%d", n);
    check_err(ret, __func__);
}

unit print_bool(bool b){
    int ret = b ? printf("true") : printf("false");
    check_err(ret, __func__);
}

unit print_char(char c){
    int ret = putchar(c);
    check_err(ret, __func__);
}

unit print_float(double d){
    int ret = printf("%lf", d);
    check_err(ret, __func__);
}

unit print_string(const char* s){
    int ret = printf("%s", s);
    check_err(ret, __func__);
}

// READING FROM STDIN
int read_int(){
    int n, ret;
    ret = scanf("%d", &n);
    check_err(ret, __func__);
    return n;
}

bool read_bool(){
    // TODO: This should probably read a string, not an int.
    int n;
    bool b;
    scanf("%d", &n);
    b = n;
    return b;
}

char read_char(){
    int ret = getchar();
    check_err(ret, __func__);
    return (char)ret;
}

double read_float(){
    double d;
    int ret = scanf("%lf", &d);
    check_err(ret, __func__);
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

// BASIC MATH
int abs(int n){
    return abs(n);
}

double fabs(double n){
    return fabs(n);
}

double sqrt(double n){
    return sqrt(n);
}

double sin(double n){
    return sin(n);
}

double cos(double n){
    return cos(n);
}

double tan(double n){
    return tan(n);
}

double atan(double n){
    return atan(n);
}

double exp(double n){
    return exp(n);
}

double ln(double n){
    return log(n);
}

double pi(){
    return M_PI;
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

int round(double n){
    return (int)round(n);
}

int int_of_char(char c){
    return (int)c;
}

char char_of_int(int n){
    return (char)n;
}


