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
unit llama_print_int(int n){
    int ret = printf("%d", n);
    check_err(ret, __func__);
}

unit llama_print_bool(bool b){
    int ret = b ? printf("true") : printf("false");
    check_err(ret, __func__);
}

unit llama_print_char(char c){
    int ret = putchar(c);
    check_err(ret, __func__);
}

unit llama_print_float(double d){
    int ret = printf("%lf", d);
    check_err(ret, __func__);
}

unit llama_print_string(const char* s){
    int ret = printf("%s", s);
    check_err(ret, __func__);
}

// READING FROM STDIN
int llama_read_int(){
    int n, ret;
    ret = scanf("%d", &n);
    check_err(ret, __func__);
    return n;
}

bool llama_read_bool(){
    // TODO: This should probably read a string, not an int.
    int n;
    bool b;
    scanf("%d", &n);
    b = n;
    return b;
}

char llama_read_char(){
    int ret = getchar();
    check_err(ret, __func__);
    return (char)ret;
}

double llama_read_float(){
    double d;
    int ret = scanf("%lf", &d);
    check_err(ret, __func__);
    return d;
}

unit llama_read_string(char* s, int n){
    char temp;
    
    for(int i = 0; i < n; ++i){
        temp = (char)getchar();
        if (temp != '\n')
            s[i] = temp;
    }
}

// BASIC MATH
int llama_abs(int n){
    return abs(n);
}

double llama_fabs(double n){
    return fabs(n);
}

double llama_sqrt(double n){
    return sqrt(n);
}

double llama_sin(double n){
    return sin(n);
}

double llama_cos(double n){
    return cos(n);
}

double llama_tan(double n){
    return tan(n);
}

double llama_atan(double n){
    return atan(n);
}

double llama_exp(double n){
    return exp(n);
}

double llama_ln(double n){
    return log(n);
}

double llama_pi(){
    return M_PI;
}

unit llama_incr(int *n){
    (*n)++;
}

unit llama_decr(int *n){
    (*n)--;
}

double llama_float_of_int(int n){
    return (double)n;
}

int llama_int_of_float(double d){
    return (int)trunc(d);
}

int llama_round(double n){
    return (int)round(n);
}

int llama_int_of_char(char c){
    return (int)c;
}

char llama_char_of_int(int n){
    return (char)n;
}


