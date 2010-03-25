#include <stdio.h>
static void*pg[2000],**pt=pg;
static unsigned char ps[2000]={[0 ... 1999]=32};
static inline void gea(){pt++;if((pt-pg)%80==0)pt-=80;}
static inline void gwe(){if((pt-pg)%80==0)pt+=80;pt--;}
static inline void gso(){pt+=80;if(pt-pg>=2000)pt-=2000;}
static inline void gno(){pt-=80;if(pt<pg)pt+=2000;}
static void(*const df[])(void)={gea,gno,gwe,gso};
static void(*dir)(void)=gea;
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
	add:if(sp>st){sp--;*sp+=sp[1];}else if(sp<st){*++sp=0;}
	dir();goto**pt;
	sub:if(sp>st){sp--;*sp-=sp[1];}else if(sp==st){*sp*=-1;}else{*++sp=0;}
	dir();goto**pt;
	mul:if(sp>st){sp--;*sp*=sp[1];}else{*(sp=st)=0;}
	dir();goto**pt;
	dvi:if(sp>st){sp--;if(!sp[1]) goto iin;*sp/=sp[1];}else goto iin;
	dir();goto**pt;
	mod:if(sp>st){sp--;if(!sp[1]) goto iin;*sp%=sp[1];}else goto iin;
	dir();goto**pt;
	not:*sp=!*sp;
	dir();goto**pt;
	gt:if(sp>st){sp--;*sp=*sp>sp[1];}else{*sp=sp==st&&0>*sp;}
	dir();goto**pt;
	ea:dir=gea;
	dir();goto**pt;
	we:dir=gwe;
	dir();goto**pt;
	so:dir=gso;
	dir();goto**pt;
	no:dir=gno;
	dir();goto**pt;
	dup:if(sp>=st){sp[1]=*sp;sp++;}else{st[0]=0;st[1]=0;sp=st+1;}
	dir();goto**pt;
	pop:if(sp>=st) sp--;
	dir();goto**pt;
	hop:dir();
	dir();goto**pt;
	hif:dir=sp>=st&&*sp--?gwe:gea;
	dir();goto**pt;
	vif:dir=sp>=st&&*sp--?gno:gso;
	dir();goto**pt;
	swp:if(sp>st){
		long tmp=*sp;
		*sp=sp[-1];
		sp[-1]=tmp;
	}else if(sp==st){sp[1]=*sp;*sp++=0;}else{*++sp=0;*++sp=0;}
	dir();goto**pt;
	stm:for(;dir(),*pt!=&&stm;*++sp=ps[pt-pg]);
	dir();goto**pt;
	rnd:dir=df[getc(rand)&3];
	dir();goto**pt;
	get:
		if(sp>st){sp--;*sp<25&&*sp>=0&&sp[1]<80&&sp[1]>=0?*sp=ps[sp[1]+*sp*80]:0;}
		else if(sp==st){*sp=*sp<80&&*sp>=0?ps[*sp]:0;}
		else{*++sp=ps[0];}
	dir();goto**pt;
	put:
		switch(sp-st){
		case 0:
			if(*sp<80&&*sp>=0){
				ps[*sp]=0;
				pg[*sp]=&&nop;
				sp=st-1;
				break;
			}
		case -1:
			ps[0]=0;
			pg[0]=&&nop;
			sp=st-1;
		break;case 1:{
			int x=sp[1]>=0&&sp[1]<80?sp[1]:0,y=*sp>=0&&*sp<25?*sp:0;
			ps[x+y*80]=0;
			pg[x+y*80]=&&nop;
			sp=st-1;}
		break;default:{
			int x=sp[3]>=0&&sp[3]<80?sp[3]:0,y=sp[2]>=0&&sp[2]<25?sp[2]:0;
			sp-=3;
			ps[x+y*80]=sp[1];
			pg[x+y*80]=sp[1]<127?ft[sp[1]]:&&nop;
			}
		}
	dir();goto**pt;
	och:putchar(sp>=st?*sp--:0);
	dir();goto**pt;
	oin:printf("%ld",sp>=st?*sp--:0);
	dir();goto**pt;
	ich:*++sp=getchar();
	dir();goto**pt;
	iin:while(!scanf("%ld",++sp));
	dir();goto**pt;
	end:putchar('\n');return 0;
}
