#include <assert.h>
#include <stdint.h>
#include <stddef.h>
#include <stdio.h>
#include <string.h>

void *gaw_md_memcpy(void *,const void *,size_t);
void *gaw_md_memset(void *,int,size_t);
int gaw_md_memcmp(const void *,const void *,size_t);
void *gaw_md_memmove(void *,const void *,size_t);
static unsigned char source[256],actual[256],expected[256],other[256];
static int sign(int value){return (value>0)-(value<0);}

int main(void){
    for(unsigned i=0;i<256u;++i)source[i]=(unsigned char)(i*137u+31u);
    for(unsigned a=0;a<8u;++a)for(unsigned b=0;b<8u;++b)
    for(unsigned n=0;n<=128u;++n){
        memset(actual,0xA5,sizeof actual);memset(expected,0xA5,sizeof expected);
        assert(gaw_md_memcpy(actual+a,source+b,n)==actual+a);
        memcpy(expected+a,source+b,n);assert(!memcmp(actual,expected,sizeof actual));
        assert(gaw_md_memset(actual+a,0x1F3,n)==actual+a);
        memset(expected+a,0x1F3,n);assert(!memcmp(actual,expected,sizeof actual));
        memcpy(other+b,source+a,n);
        assert(gaw_md_memcmp(source+a,other+b,n)==0);
        for(unsigned j=0;j<n;++j){
            other[b+j]^=0x80u;
            assert(sign(gaw_md_memcmp(source+a,other+b,n))==sign(memcmp(source+a,other+b,n)));
            other[b+j]^=0x80u;
        }
        memcpy(actual,source,sizeof actual);memcpy(expected,source,sizeof expected);
        assert(gaw_md_memmove(actual+a,actual+b,n)==actual+a);
        memmove(expected+a,expected+b,n);assert(!memcmp(actual,expected,sizeof actual));
    }
    puts("MD runtime differential tests: OK (8256 aligned/unaligned lengths, every mismatch position and overlapping moves)");
    return 0;
}
