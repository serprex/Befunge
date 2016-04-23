#include <stdint.h>
#include <stdio.h>
#if defined __GNUC__ && __GNUC__*100+__GNUC_MINOR__<405
	#define __builtin_unreachable()
#endif
#if WBIT==8
	#ifdef UNSIGN
		#define WORD uint8_t
	#else
		#define WORD int8_t
	#endif
	#define WFMT "%d"
#elif WBIT==16
	#ifdef UNSIGN
		#define WORD uint16_t
	#else
		#define WORD int16_t
	#endif
	#define WFMT "%d"
#elif WBIT==32
	#ifdef UNSIGN
		#define WORD uint32_t
	#else
		#define WORD int32_t
	#endif
	#define WFMT "%d"
#elif WBIT==64
	#ifdef UNSIGN
		#define WORD uint64_t
	#else
		#define WORD int64_t
	#endif
	#define WFMT "%lld"
#elif WFLT
	#define FLOAT
	#define WORD float
	#define WFMT "%f"
#elif WDBL
	#define FLOAT
	#define WORD double
	#define WFMT "%f"
#elif WLDB
	#define FLOAT
	#define WORD long double
	#define WFMT "%Lf"
#endif
#ifdef FLOAT
	#include <math.h>
#endif
#ifndef FRAND
	#include <stdlib.h>
	#ifdef RDTSC
		int rdtsc(){__asm__ __volatile__("rdtsc");}
	#else
		#include <time.h>
	#endif
#endif
#ifndef STACK
	#include <sys/resource.h>
#endif
int main(int argc,char**argv){
#ifndef FRAND
	srand(
	#ifdef RDTSC
		rdtsc()
	#else
		time(0)
	#endif
	);
#elif defined NOURANDOM
	FILE*rand=fopen("/dev/random","r");
#else
	FILE*rand=fopen("/dev/urandom","r");
#endif
#ifdef SMALL
	void*pg[2560],**pt=pg;
#else
	unsigned char pg[2560],*pt=pg;
#endif
	WORD ps[2560];
	void*const ft[]={
#ifdef SMALL
	#define FT(x) ft[x]
	&&not,&&stm,&&hop,&&pop,&&mod,&&iin,&&nop,&&nop,&&nop,&&mul,&&add,&&och,&&sub,&&oin,&&dvi,
	&&p0,&&p1,&&p2,&&p3,&&p4,&&p5,&&p6,&&p7,&&p8,&&p9,&&dup,&&nop,&&gwe,&&nop,&&gea,&&rnd,
	&&end,&&nop,&&nop,&&nop,&&nop,&&nop,&&nop,&&nop,&&nop,&&nop,&&nop,&&nop,&&nop,&&nop,&&nop,
	&&nop,&&nop,&&nop,&&nop,&&nop,&&nop,&&nop,&&nop,&&nop,&&nop,&&nop,&&nop,&&nop,&&swp,&&nop,&&gno,
	&&hif,&&gt,&&nop,&&nop,&&nop,&&nop,&&nop,&&nop,&&get,&&nop,&&nop,&&nop,&&nop,&&nop,&&nop,&&nop,
	&&nop,&&put,&&nop,&&nop,&&nop,&&nop,&&nop,&&gso,&&nop,&&nop,&&nop,&&nop,&&nop,&&vif,&&nop,&&ich};
	void*const df[]={&&ea,&&no,&&we,&&so};
#else
	#define FT(x) x
	&&not0,&&stm0,&&hop0,&&pop0,&&mod0,&&iin0,&&gea,&&gea,&&gea,&&mul0,&&add0,&&och0,&&sub0,&&oin0,&&dvi0,
	&&p00,&&p10,&&p20,&&p30,&&p40,&&p50,&&p60,&&p70,&&p80,&&p90,&&dup0,&&gea,&&gwe,&&gea,&&gea,&&rnd0,
	&&end,&&gea,&&gea,&&gea,&&gea,&&gea,&&gea,&&gea,&&gea,&&gea,&&gea,&&gea,&&gea,&&gea,&&gea,
	&&gea,&&gea,&&gea,&&gea,&&gea,&&gea,&&gea,&&gea,&&gea,&&gea,&&gea,&&gea,&&gea,&&swp0,&&gea,&&gno,
	&&hif0,&&gt0,&&gea,&&gea,&&gea,&&gea,&&gea,&&gea,&&get0,&&gea,&&gea,&&gea,&&gea,&&gea,&&gea,&&gea,
	&&gea,&&put0,&&gea,&&gea,&&gea,&&gea,&&gea,&&gso,&&gea,&&gea,&&gea,&&gea,&&gea,&&vif0,&&gea,&&ich0,
	&&not1,&&stm1,&&hop1,&&pop1,&&mod1,&&iin1,&&gno,&&gno,&&gno,&&mul1,&&add1,&&och1,&&sub1,&&oin1,&&dvi1,
	&&p01,&&p11,&&p21,&&p31,&&p41,&&p51,&&p61,&&p71,&&p81,&&p91,&&dup1,&&gno,&&gwe,&&gno,&&gea,&&rnd1,
	&&end,&&gno,&&gno,&&gno,&&gno,&&gno,&&gno,&&gno,&&gno,&&gno,&&gno,&&gno,&&gno,&&gno,&&gno,
	&&gno,&&gno,&&gno,&&gno,&&gno,&&gno,&&gno,&&gno,&&gno,&&gno,&&gno,&&gno,&&gno,&&swp1,&&gno,&&gno,
	&&hif1,&&gt1,&&gno,&&gno,&&gno,&&gno,&&gno,&&gno,&&get1,&&gno,&&gno,&&gno,&&gno,&&gno,&&gno,&&gno,
	&&gno,&&put1,&&gno,&&gno,&&gno,&&gno,&&gno,&&gso,&&gno,&&gno,&&gno,&&gno,&&gno,&&vif1,&&gno,&&ich1,
	&&not2,&&stm2,&&hop2,&&pop2,&&mod2,&&iin2,&&gwe,&&gwe,&&gwe,&&mul2,&&add2,&&och2,&&sub2,&&oin2,&&dvi2,
	&&p02,&&p12,&&p22,&&p32,&&p42,&&p52,&&p62,&&p72,&&p82,&&p92,&&dup2,&&gwe,&&gwe,&&gwe,&&gea,&&rnd2,
	&&end,&&gwe,&&gwe,&&gwe,&&gwe,&&gwe,&&gwe,&&gwe,&&gwe,&&gwe,&&gwe,&&gwe,&&gwe,&&gwe,&&gwe,
	&&gwe,&&gwe,&&gwe,&&gwe,&&gwe,&&gwe,&&gwe,&&gwe,&&gwe,&&gwe,&&gwe,&&gwe,&&gwe,&&swp2,&&gwe,&&gno,
	&&hif2,&&gt2,&&gwe,&&gwe,&&gwe,&&gwe,&&gwe,&&gwe,&&get2,&&gwe,&&gwe,&&gwe,&&gwe,&&gwe,&&gwe,&&gwe,
	&&gwe,&&put2,&&gwe,&&gwe,&&gwe,&&gwe,&&gwe,&&gso,&&gwe,&&gwe,&&gwe,&&gwe,&&gwe,&&vif2,&&gwe,&&ich2,
	&&not3,&&stm3,&&hop3,&&pop3,&&mod3,&&iin3,&&gso,&&gso,&&gso,&&mul3,&&add3,&&och3,&&sub3,&&oin3,&&dvi3,
	&&p03,&&p13,&&p23,&&p33,&&p43,&&p53,&&p63,&&p73,&&p83,&&p93,&&dup3,&&gso,&&gwe,&&gso,&&gea,&&rnd3,
	&&end,&&gso,&&gso,&&gso,&&gso,&&gso,&&gso,&&gso,&&gso,&&gso,&&gso,&&gso,&&gso,&&gso,&&gso,
	&&gso,&&gso,&&gso,&&gso,&&gso,&&gso,&&gso,&&gso,&&gso,&&gso,&&gso,&&gso,&&gso,&&swp3,&&gso,&&gno,
	&&hif3,&&gt3,&&gso,&&gso,&&gso,&&gso,&&gso,&&gso,&&get3,&&gso,&&gso,&&gso,&&gso,&&gso,&&gso,&&gso,
	&&gso,&&put3,&&gso,&&gso,&&gso,&&gso,&&gso,&&gso,&&gso,&&gso,&&gso,&&gso,&&gso,&&vif3,&&gso,&&ich3};
#endif
#ifdef STACK
	WORD st[STACK
#else
	struct rlimit ss;
	getrlimit(RLIMIT_STACK,&ss);
	WORD st[(ss.rlim_cur-sizeof(pg)-sizeof(ft)-sizeof(ps)
	#ifdef SMALL
	-sizeof(df)
	#endif
	)/sizeof(WORD)-4096
#endif
	],*sp=st-1;
#ifdef SPACE
	for(int i=0;i<2560;i++)ps[i]=SPACE;
#endif
	FILE*prog=fopen(argv[1],"r");
	for(int i=0;i<25;i++){
		for(int j=0;j<80;j++){
			int c=getc(prog);
			if(c=='\n')goto FoundNew;
			if(c==-1)goto RunProg;
			ps[i+j*32]=c;
		}
		for(;;){
			int c=getc(prog);
			if(c=='\n')goto FoundNew;
			if(c==-1)goto RunProg;
		}
		FoundNew:;
	}
	RunProg:fclose(prog);
	for(int i=0;i<2560;i++)pg[i]=ps[i]>32&&ps[i]<127?FT(ps[i]-33):FT(7);
#ifdef SMALL
	int dir=0;
	goto**pt;
	#define OP(x) x:
	#define LOOP goto*df[dir]
	#define HOP switch(dir){\
	case 0:pt+=64;if(pt-pg>=2560)pt-=2560;\
	goto**pt;case 1:if((pt-pg&31)<2)pt+=32;pt-=2;\
	goto**pt;case 2:pt-=64;if(pt<pg)pt+=2560;\
	goto**pt;case 3:pt+=2;if((pt-pg&31)<2)pt-=32;\
	goto**pt;default:__builtin_unreachable();}
	#define RND(x) goto*df[dir=x]
	gea:dir=0;
	ea:pt+=32;if(pt-pg>=2560)pt-=2560;goto**pt;
	gno:dir=1;
	no:if(!(pt-pg&31))pt+=25;pt--;goto**pt;
	gwe:dir=2;
	we:pt-=32;if(pt<pg)pt+=2560;goto**pt;
	gso:dir=3;
	so:pt++;if(!(pt-pg&31))pt-=32;goto**pt;
	#include "marsh.h"
#else
	goto*ft[*pt];
	#define RND(x) switch(x){case 0:goto gea;case 1:goto gno;case 2:goto gwe;case 3:goto gso;default:__builtin_unreachable();}
	#define dir 0
	#define nop gea
	#define OP(x) x##0:
	#define LOOP pt+=32;if(pt-pg>=2560)pt-=2560;goto*ft[*pt]
	#define HOP pt+=64;if(pt-pg>=2560)pt-=2560;goto*ft[*pt]
	#include "marsh.h"
	#undef dir
	#undef nop
	#undef OP
	#undef LOOP
	#undef HOP
	#define dir 1
	#define nop gno
	#define OP(x) x##1:
	#define LOOP if(!(pt-pg&31))pt+=25;pt--;goto*ft[94+*pt]
	#define HOP if((pt-pg&31)<2)pt+=25;pt-=2;goto*ft[94+*pt]
	#include "marsh.h"
	#undef dir
	#undef nop
	#undef OP
	#undef LOOP
	#undef HOP
	#define dir 2
	#define nop gwe
	#define OP(x) x##2:
	#define LOOP pt-=32;if(pt<pg)pt+=2560;goto*ft[188+*pt]
	#define HOP pt-=64;if(pt<pg)pt+=2560;goto*ft[188+*pt]
	#include "marsh.h"
	#undef dir
	#undef nop
	#undef OP
	#undef LOOP
	#undef HOP
	#define dir 3
	#define nop gso
	#define OP(x) x##3:
	#define LOOP pt++;if(!(pt-pg&31))pt-=32;goto*ft[282+*pt]
	#define HOP pt+=2;if((pt-pg&31)<2)pt-=32;goto*ft[282+*pt]
	#include "marsh.h"
#endif
	end:;
}