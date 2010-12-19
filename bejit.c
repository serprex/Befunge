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
	void*n;
	uint8_t d[];
};
#define OP(x) ((struct op*)(x))
#define BR(x) ((struct br*)(x))
#define RN(x) ((struct rn*)(x))
const char at=29,loop=30;
uint16_t*restrict np,ns;
FILE*ran;
int st[65536],*sp=st,ps[2560];
uint8_t str[320];
void*pg[2560][4];
int mv(int i,int d){
	switch(d){
	default:__builtin_unreachable();
	case(0)i+=32;if(i>=2560)i-=2560;
	case(1)if(!(i&31))i+=25;i--;
	case(2)i-=32;if(i<0)i+=2560;
	case(3)i++;if(!(i&31))i-=32;
	}
	return i;
}
void cknop(int i,int d){
	for(;;)switch(ps[i=mv(i,d)]&255){
	case'?':case'_':case'|':case'#':case'>':case'^':case'<':case'v':case'@':case'"':case'p':case'g':case'0'...'9':
	case'.':case',':case'~':case'&':case'$':case'`':case':':case'+':case'-':case'*':case'/':case'%':case'\\':case'!':return;
	}
}
int opc(int i){
	switch(i){
	default:return -1;
	case'0'...'9':return i-'0';
	case'"':return 10;
	case'+':return 11;
	case'-':return 12;
	case'*':return 13;
	case'/':return 14;
	case'%':return 15;
	case'`':return 16;
	case'!':return 17;
	case'$':return 18;
	case':':return 19;
	case'\\':return 20;
	case'.':return 21;
	case',':return 22;
	case'~':return 23;
	case'&':return 24;
	case'p':return 25;
	case'g':return 26;
	case'_':case'|':return 27;
	case'?':return 28;
	case'@':return 29;
	}
}
void*compile(int i,int d){
	if(pg[i][d])return pg[i][d];
	int i2=i,d2=d;
	switch(ps[i]){
	default:goto nxsw;
	case('#')hash:i2=mv(i,d);
	case('>')d2=0;
	case('^')d2=1;
	case('<')d2=2;
	case('v')d2=3;
	}
	for(int j=0;j<ns;j++)
		if(np[j]==(i<<2|d))return pg[i][d]=(void*)&loop;
	np=realloc(np,2*++ns);
	np[ns-1]=i<<2|d;
	return pg[i][d]=compile(mv(i2,d2),d2);
	nxsw:i2=ns;ns=0;
	switch(ps[i]){
	case('0'...'9')
	case'.':case',':case'~':case'&':case'$':case'`':case':':case'+':case'-':case'*':case'/':case'%':case'g':case'\\':case'!':
		pg[i][d]=malloc(sizeof(struct op));
		OP(pg[i][d])->o=opc(ps[i]);
		OP(pg[i][d])->n=compile(mv(i,d),d);
		return pg[i][d];
	case('_')
		pg[i][0]=pg[i][1]=pg[i][2]=pg[i][3]=malloc(sizeof(struct br));
		BR(pg[i][d])->o=27;
		BR(pg[i][d])->n[0]=compile(mv(i,0),0);
		BR(pg[i][d])->n[1]=compile(mv(i,2),2);
		return pg[i][0];
	case('|')
		pg[i][0]=pg[i][1]=pg[i][2]=pg[i][3]=malloc(sizeof(struct br));
		BR(pg[i][d])->o=27;
		BR(pg[i][d])->n[0]=compile(mv(i,3),3);
		BR(pg[i][d])->n[1]=compile(mv(i,1),1);
		return pg[i][0];
	case('?')
		pg[i][0]=pg[i][1]=pg[i][2]=pg[i][3]=malloc(sizeof(struct rn));
		RN(pg[i][d])->o=28;
		for(int j=0;j<4;j++)RN(pg[i][d])->n[j]=compile(mv(i,j),j);
		return pg[i][0];
	case('@')return pg[i][d]=(void*)&at;
	case('"'){
		int j=mv(i,d);
		if(ps[j]=='"'){ns=i2;goto hash;}
		pg[i][d]=malloc(sizeof(struct op)+2);
		OP(pg[i][d])->o=10;
		OP(pg[i][d])->d[0]=0;
		do if((j&31)<25){
			str[i>>3]|=1<<(i&7);
			pg[i][d]=realloc(pg[i][d],sizeof(struct op)+OP(pg[i][d])->d[0]+2);
			OP(pg[i][d])->d[++OP(pg[i][d])->d[0]]=ps[j];
		}while(ps[j=mv(j,d)]!='"');
		OP(pg[i][d])->n=compile(mv(j,d),d);
		return pg[i][d];
	}
	case('p')
		pg[i][d]=malloc(sizeof(struct op)+3);
		OP(pg[i][d])->o=25;
		OP(pg[i][d])->n=compile(mv(i,d),d);
		*(uint16_t*)(OP(pg[i][d])->d)=i;
		OP(pg[i][d])->d[3]=d;
		return pg[i][d];
	default:ns=i2;return pg[i][d]=compile(mv(i,d),d);
	}
}
void eval(void*op){
	for(;;){
		switch(OP(op)->o){
		default:__builtin_unreachable();
		case(0)*++sp=0;
		case(1)*++sp=1;
		case(2)*++sp=2;
		case(3)*++sp=3;
		case(4)*++sp=4;
		case(5)*++sp=5;
		case(6)*++sp=6;
		case(7)*++sp=7;
		case(8)*++sp=8;
		case(9)*++sp=9;
		case(10)
			for(int i=1;i<=OP(op)->d[0];i++)*++sp=OP(op)->d[i];
		case(11)if(sp>st){sp--;*sp+=sp[1];}else if(sp<st)*++sp=0;
		case(12)if(sp>st){sp--;*sp-=sp[1];}else if(sp==st)*sp*=-1;else*++sp=0;
		case(13)if(sp>st){sp--;*sp*=sp[1];}else*(sp=st)=0;
		case(14)if(sp>st){sp--;if(sp[1])*sp/=sp[1];}else*(sp=st)=0;
		case(15)if(sp>st){sp--;if(sp[1])*sp%=sp[1];}else*(sp=st)=0;
		case(16)if(sp>st){sp--;*sp=*sp>sp[1];}else*sp=sp==st&&0>*sp;
		case(17)*sp=!*sp;
		case(18)sp--;
		case(19)sp[1]=*sp;sp++;
		case(20)
		if(sp>st){
			int tmp=*sp;
			*sp=sp[-1];
			sp[-1]=tmp;
		}else if(sp==st){sp[1]=*sp;*sp++=0;}else{sp=st+1;st[0]=st[1]=0;}
		case(21)printf("%d ",sp>=st?*sp--:0);
		case(22)putchar(sp>=st?*sp--:0);
		case(23)*++sp=getchar();
		case(24)scanf("%d",++sp);
		case(25){
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
			if(!(y==ps[x]||!(str[x>>3]&1<<(x&7))&&(opc(y)==opc(ps[x])||!(pg[x][0]||pg[x][1]||pg[x][2]||pg[x][3])))){
				for(int i=0;i<2560;i++)
					for(int j=0;j<4;j++){
						if(pg[i][j]&&pg[i][j]!=&at&&pg[i][j]!=&loop){
							void*p=pg[i][j];
							free(p);
							for(int k=i;k<2560;k++)
								for(int l=0;l<4;l++)
									if(pg[k][l]==p)pg[k][l]=0;
						}
					}
				int a=mv(*(uint16_t*)(OP(op)->d),OP(op)->d[3]),b=OP(op)->d[3];
				cknop(a,b);
				for(int i=0;i<320;i++)str[i]=0;
				op=compile(a,b);
				continue;
			}
		case(26)
			if(sp>st){sp--;*sp=*sp<80&&*sp>=0&&sp[1]<25&&sp[1]>=0?ps[(int)*sp*32+(int)sp[1]]:0;}
			else if(sp==st)*sp=*sp<25&&*sp>=0?ps[(int)*sp]:0;else*++sp=ps[0];
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
	cknop(0,0);
	eval(compile(0,0));
}