#ifndef _STRING_H
#define _STRING_H
#include <stddef.h>
void *memset(void *s,int c,size_t n);
void *memcpy(void *d,const void *s,size_t n);
void *memmove(void *d,const void *s,size_t n);
int memcmp(const void *a,const void *b,size_t n);
#endif
