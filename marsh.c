#include <stdio.h>
#define likely(x) __builtin_expect((x),1)
#define unlikely(x) __builtin_expect((x),0)
static void*pg[2000],**pt=pg;
static unsigned char ps[2000]={[0 ... 1999]=32};
static inline void gea(){pt++;if(unlikely((pt-pg)%80==0))pt-=80;}
static inline void gwe(){if(unlikely((pt-pg)%80==0))pt+=80;pt--;}
static inline void gso(){pt+=80;if(unlikely(pt-pg>=2000))pt-=2000;}
static inline void gno(){pt-=80;if(unlikely(pt<pg))pt+=2000;}
static void(*const df[])(void)={gea,gno,gwe,gso};
static void(*dir)(void)=gea;
static char fgs[16];
int main(int argc,char**argv){
	FILE*rand=fopen("/dev/urandom","r");
	long st[65536],*sp=st-1;
	void*const ft[127]={
	&&nop,&&nop,&&nop,&&nop,&&nop,&&nop,&&nop,&&nop,&&nop,&&nop,&&nop,
	&&nop,&&nop,&&nop,&&nop,&&nop,&&nop,&&nop,&&nop,&&nop,&&nop,&&nop,
	&&nop,&&nop,&&nop,&&nop,&&nop,&&nop,&&nop,&&nop,&&nop,&&nop,&&nop,
	&&not,&&stm,&&hop,&&pop,&&mod,&&iin,&&nop,&&nop,&&nop,&&mul,&&add,&&och,&&sub,&&oin,&&dvi,
	&&p0,&&p1,&&p2,&&p3,&&p4,&&p5,&&p6,&&p7,&&p8,&&p9,&&dup,&&nop,&&we,&&nop,&&ea,&&rnd,
	&&end,&&nop,&&nop,&&nop,&&nop,&&nop,&&nop,&&nop,&&nop,&&nop,&&nop,&&nop,&&nop,&&nop,&&nop,
	&&nop,&&nop,&&nop,&&nop,&&nop,&&nop,&&nop,&&nop,&&nop,&&nop,&&nop,&&nop,&&nop,&&swp,&&nop,&&no,
	&&hif,&&gt,&&nop,&&nop,&&nop,&&nop,&&nop,&&nop,&&get,&&nop,&&nop,&&nop,&&nop,&&nop,&&nop,&&nop,
	&&nop,&&put,&&nop,&&nop,&&nop,&&nop,&&nop,&&so,&&nop,&&nop,&&nop,&&nop,&&nop,&&vif,&&nop,&&ich};
#ifdef FUNGE
	FILE*prog=fopen(argv[1],"r");
	for(int i=0;i<25;i++){
		for(int j=0;j<80;j++){
			int c=getc(prog);
			if(c=='\n') goto FoundNew;
			if(c==-1) goto RunProg;
			ps[i*80+j]=c;
		}
		for(;;){
			int c=getc(prog);
			if(c=='\n') goto FoundNew;
			if(c==-1) goto RunProg;
		}
		FoundNew:;
	}
	RunProg:
	fclose(prog);
#endif
	for(int i=0;i<2000;i++) pg[i]=ps[i]<127?ft[ps[i]]:&&nop;
	goto**pt;
	p0:*++sp=0;
	nop:dir();goto**pt;
	p1:*++sp=1;
	dir();goto**pt;
	p2:*++sp=2;
	dir();goto**pt;
	p3:*++sp=3;
	dir();goto**pt;
	p4:*++sp=4;
	dir();goto**pt;
	p5:*++sp=5;
	dir();goto**pt;
	p6:*++sp=6;
	dir();goto**pt;
	p7:*++sp=7;
	dir();goto**pt;
	p8:*++sp=8;
	dir();goto**pt;
	p9:*++sp=9;
	dir();goto**pt;
	add:sp--;*sp+=sp[1];
	dir();goto**pt;
	sub:sp--;*sp-=sp[1];
	dir();goto**pt;
	mul:sp--;*sp*=sp[1];
	dir();goto**pt;
	dvi:sp--;*sp/=sp[1];
	dir();goto**pt;
	mod:sp--;*sp%=sp[1];
	dir();goto**pt;
	not:*sp=!*sp;
	dir();goto**pt;
	gt:sp--;*sp=*sp>sp[1];
	dir();goto**pt;
	ea:dir=gea;
	dir();goto**pt;
	we:dir=gwe;
	dir();goto**pt;
	so:dir=gso;
	dir();goto**pt;
	no:dir=gno;
	dir();goto**pt;
	dup:sp[1]=*sp;sp++;
	dir();goto**pt;
	pop:sp--;
	dir();goto**pt;
	hop:dir();
	dir();goto**pt;
	hif:dir=*sp--?gwe:gea;
	dir();goto**pt;
	vif:dir=*sp--?gno:gso;
	dir();goto**pt;
	swp:{
		long tmp=*sp;
		*sp=sp[-1];
		sp[-1]=tmp;
	}
	dir();goto**pt;
	stm:for(;dir(),*pt!=&&stm;*++sp=ps[pt-pg]);
	dir();goto**pt;
	rnd:dir=df[getc(rand)&3];
	dir();goto**pt;
	get:sp--;*sp=ps[*sp+sp[1]*80];
	dir();goto**pt;
	put:
		sp-=3;
		ps[sp[2]+sp[3]*80]=sp[1];
		pg[sp[2]+sp[3]*80]=sp[1]<127?ft[sp[1]]:&&nop;
	dir();goto**pt;
	och:putchar(*sp--);
	dir();goto**pt;
	oin:printf("%ld",*sp--);
	fflush(stdout);
	dir();goto**pt;
	ich:*++sp=getchar();
	dir();goto**pt;
	iin:
	fgets(fgs,16,stdin);
	sscanf(fgs,"%ld",++sp);
	dir();goto**pt;
	end:putchar('\n');return 0;
}
