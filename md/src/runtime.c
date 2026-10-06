#include <stddef.h>
#include <stdint.h>
void *memset(void *s,int c,size_t n){unsigned char*p=s;while(n--)*p++=(unsigned char)c;return s;}
void *memcpy(void *d,const void *s,size_t n){unsigned char*o=d;const unsigned char*i=s;while(n--)*o++=*i++;return d;}
void *memmove(void *d,const void *s,size_t n){
    unsigned char *o=d;const unsigned char *i=s;
    if((uintptr_t)o<(uintptr_t)i){while(n--)*o++=*i++;}
    else if(o!=i){o+=n;i+=n;while(n--)*--o=*--i;}
    return d;
}
