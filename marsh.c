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
#ifdef STDRAND
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
#ifdef STDRAND
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
	&&not0,&&stm0,&&hop0,&&pop0,&&mod0,&&iin0,&&nop0,&&nop0,&&nop0,&&mul0,&&add0,&&och0,&&sub0,&&oin0,&&dvi0,
	&&p00,&&p10,&&p20,&&p30,&&p40,&&p50,&&p60,&&p70,&&p80,&&p90,&&dup0,&&nop0,&&gwe,&&nop0,&&gea,&&rnd0,
	&&end,&&nop0,&&nop0,&&nop0,&&nop0,&&nop0,&&nop0,&&nop0,&&nop0,&&nop0,&&nop0,&&nop0,&&nop0,&&nop0,&&nop0,
	&&nop0,&&nop0,&&nop0,&&nop0,&&nop0,&&nop0,&&nop0,&&nop0,&&nop0,&&nop0,&&nop0,&&nop0,&&nop0,&&swp0,&&nop0,&&gno,
	&&hif0,&&gt0,&&nop0,&&nop0,&&nop0,&&nop0,&&nop0,&&nop0,&&get0,&&nop0,&&nop0,&&nop0,&&nop0,&&nop0,&&nop0,&&nop0,
	&&nop0,&&put0,&&nop0,&&nop0,&&nop0,&&nop0,&&nop0,&&gso,&&nop0,&&nop0,&&nop0,&&nop0,&&nop0,&&vif0,&&nop0,&&ich0,
	&&not1,&&stm1,&&hop1,&&pop1,&&mod1,&&iin1,&&nop1,&&nop1,&&nop1,&&mul1,&&add1,&&och1,&&sub1,&&oin1,&&dvi1,
	&&p01,&&p11,&&p21,&&p31,&&p41,&&p51,&&p61,&&p71,&&p81,&&p91,&&dup1,&&nop1,&&gwe,&&nop1,&&gea,&&rnd1,
	&&end,&&nop1,&&nop1,&&nop1,&&nop1,&&nop1,&&nop1,&&nop1,&&nop1,&&nop1,&&nop1,&&nop1,&&nop1,&&nop1,&&nop1,
	&&nop1,&&nop1,&&nop1,&&nop1,&&nop1,&&nop1,&&nop1,&&nop1,&&nop1,&&nop1,&&nop1,&&nop1,&&nop1,&&swp1,&&nop1,&&gno,
	&&hif1,&&gt1,&&nop1,&&nop1,&&nop1,&&nop1,&&nop1,&&nop1,&&get1,&&nop1,&&nop1,&&nop1,&&nop1,&&nop1,&&nop1,&&nop1,
	&&nop1,&&put1,&&nop1,&&nop1,&&nop1,&&nop1,&&nop1,&&gso,&&nop1,&&nop1,&&nop1,&&nop1,&&nop1,&&vif1,&&nop1,&&ich1,
	&&not2,&&stm2,&&hop2,&&pop2,&&mod2,&&iin2,&&nop2,&&nop2,&&nop2,&&mul2,&&add2,&&och2,&&sub2,&&oin2,&&dvi2,
	&&p02,&&p12,&&p22,&&p32,&&p42,&&p52,&&p62,&&p72,&&p82,&&p92,&&dup2,&&nop2,&&gwe,&&nop2,&&gea,&&rnd2,
	&&end,&&nop2,&&nop2,&&nop2,&&nop2,&&nop2,&&nop2,&&nop2,&&nop2,&&nop2,&&nop2,&&nop2,&&nop2,&&nop2,&&nop2,
	&&nop2,&&nop2,&&nop2,&&nop2,&&nop2,&&nop2,&&nop2,&&nop2,&&nop2,&&nop2,&&nop2,&&nop2,&&nop2,&&swp2,&&nop2,&&gno,
	&&hif2,&&gt2,&&nop2,&&nop2,&&nop2,&&nop2,&&nop2,&&nop2,&&get2,&&nop2,&&nop2,&&nop2,&&nop2,&&nop2,&&nop2,&&nop2,
	&&nop2,&&put2,&&nop2,&&nop2,&&nop2,&&nop2,&&nop2,&&gso,&&nop2,&&nop2,&&nop2,&&nop2,&&nop2,&&vif2,&&nop2,&&ich2,
	&&not3,&&stm3,&&hop3,&&pop3,&&mod3,&&iin3,&&nop3,&&nop3,&&nop3,&&mul3,&&add3,&&och3,&&sub3,&&oin3,&&dvi3,
	&&p03,&&p13,&&p23,&&p33,&&p43,&&p53,&&p63,&&p73,&&p83,&&p93,&&dup3,&&nop3,&&gwe,&&nop3,&&gea,&&rnd3,
	&&end,&&nop3,&&nop3,&&nop3,&&nop3,&&nop3,&&nop3,&&nop3,&&nop3,&&nop3,&&nop3,&&nop3,&&nop3,&&nop3,&&nop3,
	&&nop3,&&nop3,&&nop3,&&nop3,&&nop3,&&nop3,&&nop3,&&nop3,&&nop3,&&nop3,&&nop3,&&nop3,&&nop3,&&swp3,&&nop3,&&gno,
	&&hif3,&&gt3,&&nop3,&&nop3,&&nop3,&&nop3,&&nop3,&&nop3,&&get3,&&nop3,&&nop3,&&nop3,&&nop3,&&nop3,&&nop3,&&nop3,
	&&nop3,&&put3,&&nop3,&&nop3,&&nop3,&&nop3,&&nop3,&&gso,&&nop3,&&nop3,&&nop3,&&nop3,&&nop3,&&vif3,&&nop3,&&ich3};
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
	#define OP(x) x
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
	no:if(!(pt-pg&31))pt+=32;pt--;goto**pt;
	gwe:dir=2;
	we:pt-=32;if(pt<pg)pt+=2560;goto**pt;
	gso:dir=3;
	so:pt++;if(!(pt-pg&31))pt-=32;goto**pt;
	#include "marsh.h"
#else
	goto*ft[*pt];
	#define RND(x) switch(x){case 0:goto gea;case 1:goto gno;case 2:goto gwe;case 3:goto gso;}
	#define dir 0
	#define OP(x) x##0
	#define LOOP pt+=32;if(pt-pg>=2560)pt-=2560;goto*ft[*pt]
	#define HOP pt+=64;if(pt-pg>=2560)pt-=2560;goto*ft[*pt]
	gea:LOOP;
	#include "marsh.h"
	#undef dir
	#undef OP
	#undef LOOP
	#undef HOP
	#define dir 1
	#define OP(x) x##1
	#define LOOP if(!(pt-pg&31))pt+=32;pt--;goto*ft[94+*pt]
	#define HOP if((pt-pg&31)<2)pt+=32;pt-=2;goto*ft[94+*pt]
	gno:LOOP;
	#include "marsh.h"
	#undef dir
	#undef OP
	#undef LOOP
	#undef HOP
	#define dir 2
	#define OP(x) x##2
	#define LOOP pt-=32;if(pt<pg)pt+=2560;goto*ft[188+*pt]
	#define HOP pt-=64;if(pt<pg)pt+=2560;goto*ft[188+*pt]
	gwe:LOOP;
	#include "marsh.h"
	#undef dir
	#undef OP
	#undef LOOP
	#undef HOP
	#define dir 3
	#define OP(x) x##3
	#define LOOP pt++;if(!(pt-pg&31))pt-=32;goto*ft[282+*pt]
	#define HOP pt+=2;if((pt-pg&31)<2)pt-=32;goto*ft[282+*pt]
	gso:LOOP;
	#include "marsh.h"
#endif
	end:;
}