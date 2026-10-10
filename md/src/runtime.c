#include <stddef.h>
#include <stdint.h>
#include <string.h>
/* 68000 long accesses require even addresses. Use the compiler's alignment
   so the same implementation also remains valid in host differential tests. */
typedef uint32_t BulkWord __attribute__((__may_alias__));
#define BULK_ALIGN (_Alignof(BulkWord)-1u)
void *memset(void *s,int c,size_t n){
    unsigned char*p=s;unsigned char byte=(unsigned char)c;
    while(n&&((uintptr_t)p&BULK_ALIGN)){*p++=byte;--n;}
    BulkWord value=(BulkWord)byte*0x01010101u;
    while(n>=4u){*(BulkWord*)p=value;p+=4;n-=4;}
    while(n--)*p++=byte;
    return s;
}
void *memcpy(void *d,const void *s,size_t n){
    unsigned char*o=d;const unsigned char*i=s;
    if(!(((uintptr_t)o^(uintptr_t)i)&BULK_ALIGN)){
        while(n&&((uintptr_t)o&BULK_ALIGN)){*o++=*i++;--n;}
        while(n>=4u){*(BulkWord*)o=*(const BulkWord*)i;o+=4;i+=4;n-=4;}
    }
    while(n--)*o++=*i++;
    return d;
}
int memcmp(const void *a,const void *b,size_t n){
    const unsigned char *x=a,*y=b;
    if(!(((uintptr_t)x^(uintptr_t)y)&BULK_ALIGN)){
        while(n&&((uintptr_t)x&BULK_ALIGN)){
            if(*x!=*y)return (int)*x-(int)*y;
            ++x;++y;--n;
        }
        while(n>=4u&&*(const BulkWord*)x==*(const BulkWord*)y){x+=4;y+=4;n-=4;}
    }
    while(n--){if(*x!=*y)return (int)*x-(int)*y;++x;++y;}
    return 0;
}
void *memmove(void *d,const void *s,size_t n){
    unsigned char *o=d;const unsigned char *i=s;
    if((uintptr_t)o<(uintptr_t)i){while(n--)*o++=*i++;}
    else if(o!=i){o+=n;i+=n;while(n--)*--o=*--i;}
    return d;
}
