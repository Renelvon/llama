#include <assert.h>
#include <stdio.h>
#include <stdlib.h>

#include "libllama.h"

void test_llama_abs() {
    assert(llama_abs(0) == 0);
    assert(llama_abs(42) == 42);
    assert(llama_abs(-42) == 42);
}

void test_llama_fabs() {
    assert(llama_fabs(0.0) == 0.0);
    assert(llama_fabs(-0.0) == +0.0);
    assert(llama_fabs(42.1) == 42.1);
    assert(llama_fabs(-42.1) == 42.1);
}

void test_llama_sqrt() {
    assert(llama_sqrt(0.0) == 0.0);
    assert(llama_sqrt(1.0) == 1.0);
    assert(llama_sqrt(16) == 4.0);
}

void test_incr() {
    int n = 0;
    llama_incr(&n);
    assert(n == 1);
}

void test_decr() {
    int n = 0;
    llama_decr(&n);
    assert(n == -1);
}

int main() {
    test_llama_abs();
    test_llama_fabs();
    test_llama_sqrt();

    test_incr();
    test_decr();

    return EXIT_SUCCESS;
}
