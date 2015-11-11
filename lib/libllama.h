/**
 * ----------------------------------------------------------------------
 * libllama.h
 *
 * Llama standard library headers
 * http://courses.softlab.ntua.gr/compilers/2012a/llama2012.pdf
 *
 * Authors: Dimitris Koutsoukos <dim.kou.shmmy@gmail.com>
 *          Nick Korasidis <renelvon@gmail.com>
 * ----------------------------------------------------------------------
 */

#ifndef _LIB_LLAMA_H
#define _LIB_LLAMA_H

#include <math.h>
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef void unit;

// PRINTING TO STDOUT
unit llama_print_int(int n);
unit llama_print_bool(bool b);
unit llama_print_char(char c);
unit llama_print_float(double d);
unit llama_print_string(const char* s);

// READING FROM STDIN
int llama_read_int();
bool llama_read_bool();
char llama_read_char();
double llama_read_float();
unit llama_read_string(char *s, int n);

// BASIC MATH
int llama_abs(int n);
double llama_fabs(double n);
double llama_sqrt(double n);
double llama_sin(double n);
double llama_cos(double n);
double llama_tan(double n);
double llama_atan(double n);
double llama_exp(double n);
double llama_ln(double n);
double llama_pi();

// REFERENCE HANDLING
unit llama_incr(int *n);
unit llama_decr(int *n);

// TYPE CASTS
double llama_float_of_int(int n);
int llama_int_of_float(double d);
int llama_round(double n);
int llama_int_of_char(char c);
char llama_char_of_int(int n);

// STRING MANIPULATION
int llama_strlen(const char *s);
int llama_strcmp(const char *s1, const char *s2);
unit llama_strcpy(char *s1, const char *s2);
unit llama_strcat(char *s1, const char *s2);

#endif /* _LIB_LLAMA_H */
