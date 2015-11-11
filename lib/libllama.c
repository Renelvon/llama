#include "libllama.h"

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

unit llama_read_string(char *s, int n){
    for (unsigned int i = 0; i < n - 1; ++i){
        int ret = getchar();
        if (EOF == ret) {
            break;
        }
        check_err(ret, __func__);
        char temp = ret;
        if (temp == '\n') {
            s[i] = '\0';
            break;
        }
        s[i] = temp;
    }
    s[n - 1] = '\0';
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

// STRING MANIPULATION
int llama_strlen(const char *s) {
    return strlen(s);
}

int llama_strcmp(const char *s1, const char *s2){
    // TODO: use strncmp
    return strcmp(s1, s2);
}

unit llama_strcpy(char *s1, const char *s2){
    // TODO: use strncpy
    (void)strcpy(s1, s2);
}

unit llama_strcat(char *s1, const char *s2){
    // TODO: use strncat
    (void)strcat(s1, s2);
}
