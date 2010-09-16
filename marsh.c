#include <stdio.h>
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
#else
	FILE*rand=fopen("/dev/urandom","r");
#endif
#ifdef SMALL
	void*pg[2560],**pt=pg;
#else
	unsigned char pg[2560],*pt=pg;
#endif
	long long ps[2560]={[0 ... 2559]=
#ifdef FUNGE
	0
#else
	32
#endif
	};
#ifdef SMALL
	void*const df[]={&&gea,&&gno,&&gwe,&&gso};
	void*const ft[]={
	&&not,&&stm,&&hop,&&pop,&&mod,&&iin,&&nop,&&nop,&&nop,&&mul,&&add,&&och,&&sub,&&oin,&&dvi,
	&&p0,&&p1,&&p2,&&p3,&&p4,&&p5,&&p6,&&p7,&&p8,&&p9,&&dup,&&nop,&&we,&&nop,&&ea,&&rnd,
	&&end,&&nop,&&nop,&&nop,&&nop,&&nop,&&nop,&&nop,&&nop,&&nop,&&nop,&&nop,&&nop,&&nop,&&nop,
	&&nop,&&nop,&&nop,&&nop,&&nop,&&nop,&&nop,&&nop,&&nop,&&nop,&&nop,&&nop,&&nop,&&swp,&&nop,&&no,
	&&hif,&&gt,&&nop,&&nop,&&nop,&&nop,&&nop,&&nop,&&get,&&nop,&&nop,&&nop,&&nop,&&nop,&&nop,&&nop,
	&&nop,&&put,&&nop,&&nop,&&nop,&&nop,&&nop,&&so,&&nop,&&nop,&&nop,&&nop,&&nop,&&vif,&&nop,&&ich};
#else
	void*const ft[4][127-33]={
	{&&not0,&&stm0,&&hop0,&&pop0,&&mod0,&&iin0,&&nop0,&&nop0,&&nop0,&&mul0,&&add0,&&och0,&&sub0,&&oin0,&&dvi0,
	&&p00,&&p10,&&p20,&&p30,&&p40,&&p50,&&p60,&&p70,&&p80,&&p90,&&dup0,&&nop0,&&gwe,&&nop0,&&gea,&&rnd0,
	&&end,&&nop0,&&nop0,&&nop0,&&nop0,&&nop0,&&nop0,&&nop0,&&nop0,&&nop0,&&nop0,&&nop0,&&nop0,&&nop0,&&nop0,
	&&nop0,&&nop0,&&nop0,&&nop0,&&nop0,&&nop0,&&nop0,&&nop0,&&nop0,&&nop0,&&nop0,&&nop0,&&nop0,&&swp0,&&nop0,&&gno,
	&&hif0,&&gt0,&&nop0,&&nop0,&&nop0,&&nop0,&&nop0,&&nop0,&&get0,&&nop0,&&nop0,&&nop0,&&nop0,&&nop0,&&nop0,&&nop0,
	&&nop0,&&put0,&&nop0,&&nop0,&&nop0,&&nop0,&&nop0,&&gso,&&nop0,&&nop0,&&nop0,&&nop0,&&nop0,&&vif0,&&nop0,&&ich0},
	{&&not1,&&stm1,&&hop1,&&pop1,&&mod1,&&iin1,&&nop1,&&nop1,&&nop1,&&mul1,&&add1,&&och1,&&sub1,&&oin1,&&dvi1,
	&&p01,&&p11,&&p21,&&p31,&&p41,&&p51,&&p61,&&p71,&&p81,&&p91,&&dup1,&&nop1,&&gwe,&&nop1,&&gea,&&rnd1,
	&&end,&&nop1,&&nop1,&&nop1,&&nop1,&&nop1,&&nop1,&&nop1,&&nop1,&&nop1,&&nop1,&&nop1,&&nop1,&&nop1,&&nop1,
	&&nop1,&&nop1,&&nop1,&&nop1,&&nop1,&&nop1,&&nop1,&&nop1,&&nop1,&&nop1,&&nop1,&&nop1,&&nop1,&&swp1,&&nop1,&&gno,
	&&hif1,&&gt1,&&nop1,&&nop1,&&nop1,&&nop1,&&nop1,&&nop1,&&get1,&&nop1,&&nop1,&&nop1,&&nop1,&&nop1,&&nop1,&&nop1,
	&&nop1,&&put1,&&nop1,&&nop1,&&nop1,&&nop1,&&nop1,&&gso,&&nop1,&&nop1,&&nop1,&&nop1,&&nop1,&&vif1,&&nop1,&&ich1},
	{&&not2,&&stm2,&&hop2,&&pop2,&&mod2,&&iin2,&&nop2,&&nop2,&&nop2,&&mul2,&&add2,&&och2,&&sub2,&&oin2,&&dvi2,
	&&p02,&&p12,&&p22,&&p32,&&p42,&&p52,&&p62,&&p72,&&p82,&&p92,&&dup2,&&nop2,&&gwe,&&nop2,&&gea,&&rnd2,
	&&end,&&nop2,&&nop2,&&nop2,&&nop2,&&nop2,&&nop2,&&nop2,&&nop2,&&nop2,&&nop2,&&nop2,&&nop2,&&nop2,&&nop2,
	&&nop2,&&nop2,&&nop2,&&nop2,&&nop2,&&nop2,&&nop2,&&nop2,&&nop2,&&nop2,&&nop2,&&nop2,&&nop2,&&swp2,&&nop2,&&gno,
	&&hif2,&&gt2,&&nop2,&&nop2,&&nop2,&&nop2,&&nop2,&&nop2,&&get2,&&nop2,&&nop2,&&nop2,&&nop2,&&nop2,&&nop2,&&nop2,
	&&nop2,&&put2,&&nop2,&&nop2,&&nop2,&&nop2,&&nop2,&&gso,&&nop2,&&nop2,&&nop2,&&nop2,&&nop2,&&vif2,&&nop2,&&ich2},
	{&&not3,&&stm3,&&hop3,&&pop3,&&mod3,&&iin3,&&nop3,&&nop3,&&nop3,&&mul3,&&add3,&&och3,&&sub3,&&oin3,&&dvi3,
	&&p03,&&p13,&&p23,&&p33,&&p43,&&p53,&&p63,&&p73,&&p83,&&p93,&&dup3,&&nop3,&&gwe,&&nop3,&&gea,&&rnd3,
	&&end,&&nop3,&&nop3,&&nop3,&&nop3,&&nop3,&&nop3,&&nop3,&&nop3,&&nop3,&&nop3,&&nop3,&&nop3,&&nop3,&&nop3,
	&&nop3,&&nop3,&&nop3,&&nop3,&&nop3,&&nop3,&&nop3,&&nop3,&&nop3,&&nop3,&&nop3,&&nop3,&&nop3,&&swp3,&&nop3,&&gno,
	&&hif3,&&gt3,&&nop3,&&nop3,&&nop3,&&nop3,&&nop3,&&nop3,&&get3,&&nop3,&&nop3,&&nop3,&&nop3,&&nop3,&&nop3,&&nop3,
	&&nop3,&&put3,&&nop3,&&nop3,&&nop3,&&nop3,&&nop3,&&gso,&&nop3,&&nop3,&&nop3,&&nop3,&&nop3,&&vif3,&&nop3,&&ich3}};
#endif
#ifdef STACK
	long long st[STACK
#else
	struct rlimit ss;
	getrlimit(RLIMIT_STACK,&ss);
	long long st[(ss.rlim_cur-sizeof(pg)-sizeof(ft)-sizeof(ps)
#ifdef SMALL
	-sizeof(df)
#endif
	)/sizeof(long long)-4096
#endif
	],*sp=st-1;
#ifdef FUNGE
#ifdef SPACE
	for(int i=0;i<2560;i++)ps[i]=' ';
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
#endif
	for(int i=0;i<2560;i++)pg[i]=ps[i]>32&&ps[i]<127?
#ifdef SMALL
	ft[ps[i]-33]:&&nop;
	int dir=0;
	goto**pt;
	gea:pt+=32;if(pt-pg>=2560)pt-=2560;
	goto**pt;
	gno:if(!(pt-pg&31))pt+=32;pt--;
	goto**pt;
	gwe:pt-=32;if(pt<pg)pt+=2560;
	goto**pt;
	gso:pt++;if(!(pt-pg&31))pt-=32;
	goto**pt;
	p0:*++sp=0;
	nop:goto*df[dir];
	p1:*++sp=1;
	goto*df[dir];
	p2:*++sp=2;
	goto*df[dir];
	p3:*++sp=3;
	goto*df[dir];
	p4:*++sp=4;
	goto*df[dir];
	p5:*++sp=5;
	goto*df[dir];
	p6:*++sp=6;
	goto*df[dir];
	p7:*++sp=7;
	goto*df[dir];
	p8:*++sp=8;
	goto*df[dir];
	p9:*++sp=9;
	goto*df[dir];
	add:if(sp>st){sp--;*sp+=sp[1];}else if(sp<st)*++sp=0;
	goto*df[dir];
	sub:if(sp>st){sp--;*sp-=sp[1];}else if(sp==st)*sp*=-1;else*++sp=0;
	goto*df[dir];
	mul:if(sp>st){sp--;*sp*=sp[1];}else*(sp=st)=0;
	goto*df[dir];
	dvi:if(sp>st){sp--;*sp=sp[1]?*sp/sp[1]:*sp+(*sp>0)-(*sp<0);}else*(sp=st)=0;
	goto*df[dir];
	mod:if(sp>st){sp--;if(sp[1])*sp%=sp[1];}else*(sp=st)=0;
	goto*df[dir];
	not:*sp=!*sp;
	goto*df[dir];
	gt:if(sp>st){sp--;*sp=*sp>sp[1];}else*sp=sp==st&&0>*sp;
	goto*df[dir];
	ea:goto*df[dir=0];
	we:goto*df[dir=2];
	so:goto*df[dir=3];
	no:goto*df[dir=1];
	dup:if(sp>=st){sp[1]=*sp;sp++;}else{sp=st+1;st[0]=st[1]=0;}
	goto*df[dir];
	pop:sp-=sp>=st;
	goto*df[dir];
	hop:switch(dir){
	case 0:pt+=64;if(pt-pg>=2560)pt-=2560;
	goto**pt;case 1:if((pt-pg&31)<2)pt+=32;pt-=2;
	goto**pt;case 2:pt-=64;if(pt<pg)pt+=2560;
	goto**pt;case 3:pt+=2;if((pt-pg&31)<2)pt-=32;
	goto**pt;default:__builtin_unreachable();
	}
	hif:goto*df[dir=sp>=st&&*sp--?2:0];
	vif:goto*df[dir=sp>=st&&*sp--?1:3];
	swp:if(sp>st){
		long tmp=*sp;
		*sp=sp[-1];
		sp[-1]=tmp;
	}else if(sp==st){sp[1]=*sp;*sp++=0;}else{sp=st+1;st[0]=st[1]=0;}
	goto*df[dir];
	stm:switch(dir){
	case 0:for(;;){
		pt+=32;if(pt-pg>=2560)pt-=2560;
		if(ps[pt-pg]=='"')goto*df[dir];
		*++sp=ps[pt-pg];
	}
	case 1:for(;;){
		if(!(pt-pg&31))pt+=32;pt--;
		if(ps[pt-pg]=='"')goto*df[dir];
		*++sp=ps[pt-pg];
	}
	case 2:for(;;){
		pt-=32;if(pt<pg)pt+=2560;
		if(ps[pt-pg]=='"')goto*df[dir];
		*++sp=ps[pt-pg];
	}
	case 3:for(;;){
		pt++;if(!(pt-pg&31))pt-=32;
		if(ps[pt-pg]=='"')goto*df[dir];
		*++sp=ps[pt-pg];
	}
	default:__builtin_unreachable();
	}
	rnd:goto*df[dir=
#ifdef STDRAND
	rand()
#else
	getc(rand)
#endif
	&3];
	get:
		if(sp>st){sp--;*sp=*sp<80&&*sp>=0&&sp[1]<25&&sp[1]>=0?ps[*sp*32+sp[1]]:0;}
		else if(sp==st)*sp=*sp<25&&*sp>=0?ps[*sp]:0;else*++sp=ps[0];
	goto*df[dir];
	put:
		switch(sp-st){
		int x;
		case-1:
			ps[0]=0;
			pg[0]=&&nop;
		break;case 0:
			sp=st-1;
			x=sp[1]<25&&sp[1]>=0?sp[1]*32:0;
			ps[x]=0;
			pg[x]=&&nop;
		break;case 1:
			sp=st-1;
			x=(sp[1]>=0&&sp[1]<80?sp[1]*32:0)+(sp[2]>=0&&sp[2]<25?sp[2]:0);
			ps[x]=0;
			pg[x]=&&nop;
		break;default:
			sp-=3;
			x=(sp[2]>=0&&sp[2]<80?sp[2]*32:0)+(sp[3]>=0&&sp[3]<25?sp[3]:0);
			ps[x]=sp[1];
			pg[x]=sp[1]>32&&sp[1]<127?&&nop:ft[sp[1]-33];
		}
	goto*df[dir];
	och:putchar(sp>=st?*sp--:0);
	goto*df[dir];
	oin:printf("%lld ",sp>=st?*sp--:0);
	goto*df[dir];
	ich:*++sp=getchar();
	goto*df[dir];
	iin:scanf("%lld",++sp);
	goto*df[dir];
#else
	ps[i]-33:7;
	#define DIR 0
	#define OP(x) x##0
	#define LOOP pt+=32;if(pt-pg>=2560)pt-=2560;goto*ft[0][*pt];
	goto*ft[0][*pt];gea:LOOP;
	#include "marsh.h"
	#undef DIR
	#undef OP
	#undef LOOP
	#define DIR 1
	#define OP(x) x##1
	#define LOOP if(!(pt-pg&31))pt+=32;pt--;goto*ft[1][*pt];
	gno:LOOP;
	#include "marsh.h"
	#undef DIR
	#undef OP
	#undef LOOP
	#define DIR 2
	#define OP(x) x##2
	#define LOOP pt-=32;if(pt<pg)pt+=2560;goto*ft[2][*pt];
	gwe:LOOP;
	#include "marsh.h"
	#undef DIR
	#undef OP
	#undef LOOP
	#define DIR 3
	#define OP(x) x##3
	#define LOOP pt++;if(!(pt-pg&31))pt-=32;goto*ft[3][*pt];
	gso:LOOP;
	#include "marsh.h"
#endif
	end:;
}