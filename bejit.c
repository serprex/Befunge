#include <stdlib.h>
#include <stdint.h>
#include <stdio.h>
#if defined __GNUC__ && __GNUC__*100+__GNUC_MINOR__<405
	#define __builtin_unreachable()
#endif
#define case(x) break;case x:;
struct rn{
	uint8_t o;
	void*n[4];
};
struct br{
	uint8_t o;
	void*n[2];
};
struct op{
	uint8_t o;
	uint8_t d0;
	uint16_t d1;
	void*n;
	uint8_t d[];
};
#define OP(x) ((struct op*)(x))
#define BR(x) ((struct br*)(x))
#define RN(x) ((struct rn*)(x))
const uint8_t at=29,loop=30;
uint16_t*restrict np,ns;
FILE*ran;
int st[65536],*sp=st,ps[2560];
uint8_t str[320];
void*pg[10240];
int mv(int i){
	switch(i&3){
	case(0)return i>=10112?i-10112:i+128;
	case(1)return i&124?i-4:i+96;
	case(2)return i<128?i+10112:i-128;
	case(3)return (i+=4)&124?i:i-128;
	}
}
int opc(int i){
	switch(i){
	default:return-1;
	case'0'...'9':return i&15;
	case'+':return 10;
	case'-':return 11;
	case'*':return 12;
	case'/':return 13;
	case'%':return 14;
	case'`':return 15;
	case'!':return 16;
	case'$':return 17;
	case':':return 18;
	case'\\':return 19;
	case'.':return 20;
	case',':return 21;
	case'~':return 22;
	case'&':return 23;
	case'p':return 24;
	case'g':return 25;
	case'"':return 26;
	case'|':return 27;
	case'?':return 28;
	case'@':return 29;
	case'_':return 30;
	case'#':return 31;
	case'>':return 32;
	case'^':return 33;
	case'<':return 34;
	case'v':return 35;
	}
}
void cknop(int i){
	while(opc(ps[(i=mv(i))>>2])==-1);
}
void*compile(int i){
	if(pg[i=mv(i)])return pg[i];
	int i2=i,op=opc(ps[i>>2]);
	if(op>=31&&op<=35){
		if(op&32)i2=i&~3|op-32;
		else hash:i2=mv(i);
		for(int j=0;j<ns;j++)
			if(np[j]==i)return pg[i]=(void*)&loop;
		np=realloc(np,2*++ns);
		np[ns-1]=i;
		return pg[i]=compile(i2);
	}
	i2=ns;
	ns=0;
	switch(op){
	default:__builtin_unreachable();
	case-1:ns=i2;return pg[i]=compile(i);
	case 0 ... 25:
		pg[i]=malloc(sizeof(struct op));
		OP(pg[i])->o=opc(ps[i>>2]);
		OP(pg[i])->n=compile(i);
		if(op==24)OP(pg[i])->d1=i;
		return pg[i];
	case 26:{
		int j=mv(i);
		if(ps[j>>2]=='"'){
			ns=i2;
			goto hash;
		}
		pg[i]=malloc(sizeof(struct op)+1);
		OP(pg[i])->o=26;
		OP(pg[i])->d0=0;
		do if((j&124)<100){
			str[i>>5]|=1<<((i>>2)&7);
			pg[i]=realloc(pg[i],sizeof(struct op)+OP(pg[i])->d0+1);
			OP(pg[i])->d[OP(pg[i])->d0++]=ps[j>>2];
		}while(ps[(j=mv(j))>>2]!='"');
		OP(pg[i])->n=compile(j);
		return pg[i];
	}
	case 28:
		pg[i]=pg[i^1]=pg[i^2]=pg[i^3]=malloc(sizeof(struct rn));
		RN(pg[i])->o=28;
		for(int j=0;j<4;j++)RN(pg[i])->n[j]=compile(i^j);
		return pg[i];
	case 29:return pg[i]=(void*)&at;
	case 30:case 27:
		pg[i]=pg[i^1]=pg[i^2]=pg[i^3]=malloc(sizeof(struct br));
		BR(pg[i])->o=27;
		for(int j=0;j<2;j++)BR(pg[i])->n[j]=compile(i&~3|j*2^(op&1?3:0));
		return pg[i];
	}
}
int main(int argc,char**argv){
	ran=fopen("/dev/urandom","r");
	FILE*prog=fopen(argv[1],"r");
#ifdef SPACE
	for(int i=0;i<2560;i++)ps[i]=SPACE;
#endif
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
	cknop(0);
	void*op=compile(-128);
	for(;;){
		switch(OP(op)->o){
		default:__builtin_unreachable();
		case(0 ... 9)*++sp=OP(op)->o;
		case(10)if(sp>st){sp--;*sp+=sp[1];}else if(sp<st)*++sp=0;
		case(11)if(sp>st){sp--;*sp-=sp[1];}else if(sp==st)*sp*=-1;else*++sp=0;
		case(12)if(sp>st){sp--;*sp*=sp[1];}else*(sp=st)=0;
		case(13)if(sp>st){sp--;if(sp[1])*sp/=sp[1];}else*(sp=st)=0;
		case(14)if(sp>st){sp--;if(sp[1])*sp%=sp[1];}else*(sp=st)=0;
		case(15)if(sp>st){sp--;*sp=*sp>sp[1];}else*sp=sp==st&&0>*sp;
		case(16)*sp=!*sp;
		case(17)sp--;
		case(18)sp[1]=*sp;sp++;
		case(19)
		if(sp>st){
			int tmp=*sp;
			*sp=sp[-1];
			sp[-1]=tmp;
		}else if(sp==st){sp[1]=*sp;*sp++=0;}else{sp=st+1;st[0]=st[1]=0;}
		case(20)printf("%d ",sp>=st?*sp--:0);
		case(21)putchar(sp>=st?*sp--:0);
		case(22)*++sp=getchar();
		case(23)scanf("%d",++sp);
		case(24){
			int x,y;
			switch(sp-st){
			case-1:
				y=ps[0];
				ps[0]=0;
			break;case 0:
				sp=st-1;
				x=sp[1]<25&&sp[1]>=0?sp[1]*32:0;
				y=ps[x];
				ps[x]=0;
			break;case 1:
				sp=st-1;
				x=(sp[1]>=0&&sp[1]<80?sp[1]*32:0)+(sp[2]>=0&&sp[2]<25?sp[2]:0);
				y=ps[x];
				ps[x]=0;
			break;default:
				sp-=3;
				x=(sp[2]>=0&&sp[2]<80?sp[2]*32:0)+(sp[3]>=0&&sp[3]<25?sp[3]:0);
				y=ps[x];
				ps[x]=sp[1];
			}
			if(!(y==ps[x]||!(str[x>>3]&1<<(x&7))&&(opc(y)==opc(ps[x])||!(pg[x*4]||pg[x*4+1]||pg[x*4+2]||pg[x*4+3])))){
				int d1=OP(op)->d1;
				for(int i=0;i<10240;i++)
					if(pg[i]&&pg[i]!=&at&&pg[i]!=&loop){
						void*p=pg[i];
						free(p);
						for(int k=i;k<10240;k++)
							if(pg[k]==p)pg[k]=0;
					}
				for(int i=0;i<320;i++)str[i]=0;
				if(d1>>2==x)cknop(d1);
				op=compile(d1);
				continue;
			}
		case(25)
			if(sp>st){sp--;*sp=*sp<80&&*sp>=0&&sp[1]<25&&sp[1]>=0?ps[(int)*sp*32+(int)sp[1]]:0;}
			else if(sp==st)*sp=*sp<25&&*sp>=0?ps[(int)*sp]:0;else*++sp=ps[0];
		case(26)
			for(int i=0;i<OP(op)->d0;i++)*++sp=OP(op)->d[i];
		case(27)
			op=BR(op)->n[sp>=st&&*sp--];
			continue;
		case(28)
			op=RN(op)->n[getc(ran)&3];
			continue;
		case(29)exit(0);
		case(30)for(;;);
		}
		}
		op=OP(op)->n;
	}
}