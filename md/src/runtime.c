#include <stddef.h>
void *memset(void *s,int c,size_t n){unsigned char*p=s;while(n--)*p++=(unsigned char)c;return s;}
void *memcpy(void *d,const void *s,size_t n){unsigned char*o=d;const unsigned char*i=s;while(n--)*o++=*i++;return d;}
