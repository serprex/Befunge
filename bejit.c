#include <stdlib.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#if defined __GNUC__ && __GNUC__*100+__GNUC_MINOR__<405
	#define __builtin_unreachable()
#endif
#define case(x) break;case x:;
FILE*ran;
int32_t ps[2560],st[65536],*sp=st-1;
uint16_t pg[10240],rl;
uint8_t pro[2560],r[65536];
int mv(int i){
	switch(i&3){
	case 0:return i>=10112?i-10112:i+128;
	case 1:return i&124?i-4:i+96;
	case 2:return i<128?i+10112:i-128;
	case 3:return i+4&124?i+4:i-124;
	}
}
uint8_t opc(int i){
	static const uint8_t loc[]={16,28,31,17,14,23,36,36,36,12,10,21,11,20,13,0,1,2,3,4,5,6,7,8,9,18,36,34,36,32,27,29,36,36,36,36,36,36,36,36,36,36,36,36,36,36,36,36,36,36,36,36,36,36,36,36,36,36,36,19,36,33,30,15,36,36,36,36,36,36,25,36,36,36,36,36,36,36,36,24,36,36,36,36,36,35,36,36,36,36,36,26,36,22};
	return __builtin_expect(i<33||i>126,0)?36:loc[i-33];
}
uint16_t comp(int i){
	fprintf(stdout,"\n#\n");
	int32_t op=opc(ps[i>>2]);
	for(;;){
		fprintf(stdout,"\n%d %d %d %d!",op,i,sp-st,rl);
		if(pg[i]!=(uint16_t)-1){
			rl+=3;
			r[rl-3]=28;
			*(uint16_t*)(r+rl-2)=pg[i];
			fprintf(stdout,"\n%d:",rl);
			for(int i=0;i<rl;i++)fprintf(stdout,"%d ",r[i]);
			fprintf(stdout,"\n");
			return pg[i];
		}
		pg[i]=rl;
		if(pro[i>>2]!=2)pro[i>>2]=1;
		switch(op){
		default:__builtin_unreachable();
		case(0 ... 9)
			rl+=5;
			r[rl-5]=0;
			*++sp=*(int32_t*)(r+rl-4)=op;
		case(10 ... 23)case 25:
			rl++;
			r[rl-1]=op;
			switch(op){
			case(10)if(sp>st){sp--;*sp+=sp[1];}else if(sp<st)*++sp=0;
			case(11)if(sp>st){sp--;*sp-=sp[1];}else if(sp==st)*sp*=-1;else*++sp=0;
			case(12)if(sp>st){sp--;*sp*=sp[1];}else*(sp=st)=0;
			case(13)if(sp>st){sp--;if(sp[1])*sp/=sp[1];}else*(sp=st)=0;
			case(14)if(sp>st){sp--;if(sp[1])*sp%=sp[1];}else*(sp=st)=0;
			case(15)if(sp>st){sp--;*sp=*sp>sp[1];}else{st[0]=sp==st&&0>*sp;sp=st;}
			case(16)if(sp>=st)*sp=!*sp;else*(sp=st)=1;
			case(17)sp-=sp>=st;
			case(18)if(sp>=st){sp[1]=*sp;sp++;}else{sp=st+1;st[0]=st[1]=0;}
			case(19)
			if(sp>st){
				int32_t t=*sp;
				*sp=sp[-1];
				sp[-1]=t;
			}else if(sp==st){sp[1]=*sp;*sp++=0;}else{sp=st+1;st[0]=st[1]=0;}
			case(20)printf("%d ",sp>=st?*sp--:0);
			case(21)putchar(sp>=st?*sp--:0);
			case(22)*++sp=getchar();
			case(23)scanf("%d",++sp);
			case(25)
				if(sp>st){sp--;*sp=*sp<80&&*sp>=0&&sp[1]<25&&sp[1]>=0?ps[*sp*32|sp[1]]:0;}
				else if(sp==st)*sp=*sp<25&&*sp>=0?ps[*sp]:0;else*++sp=ps[0];
			}
		case(24){
			rl+=3;
			r[rl-3]=24;
			*(uint16_t*)(r+rl-2)=i;
			int x,y;
			switch(sp-st){
			default:
				sp-=3;
				x=(sp[2]>=0&&sp[2]<80?sp[2]*32:0)|(sp[3]>=0&&sp[3]<25?sp[3]:0);
				y=ps[x];
				ps[x]=sp[1];
			case(-1)
				x=0;
				y=ps[0];
				ps[0]=0;
			case(0)
				sp=st-1;
				x=sp[1]<25&&sp[1]>=0?sp[1]*32:0;
				y=ps[x];
				ps[x]=0;
			case(1)
				sp=st-1;
				x=(sp[1]>=0&&sp[1]<80?sp[1]*32:0)|(sp[2]>=0&&sp[2]<25?sp[2]:0);
				y=ps[x];
				ps[x]=0;
			}
			if(y!=ps[x]&&pro[x]&&(pro[x]==2||opc(y)!=opc(ps[x]))){
				memset(pro,0,2560);
				memset(pg,-1,20480);
				rl=0;
			}
		}
		case(27){
			pg[i^1]=pg[i^2]=pg[i^3]=rl;
			rl+=11;
			r[rl-11]=27;
			*(uint16_t*)(r+rl-2)=i&~3;
			memset(r+rl-10,-1,8);
			int j=getc(ran)&3;
			i=i&~3|j;
			*(uint16_t*)(r+rl-10+2*j)=rl;
		}
		case(28)
			while(ps[(i=mv(i))>>2]!='"'){
				pro[i>>2]=2;
				rl+=5;
				r[rl-5]=0;
				*++sp=*(int32_t*)(r+rl-4)=ps[i>>2];
			}
			pro[i>>2]=2;
		case(29)exit(0);
		case(30)case 26:
			pg[i^1]=pg[i^2]=pg[i^3]=rl;
			rl+=7;
			r[rl-7]=26;
			int j=sp>=st&&*sp--;
			i=i&~3|(op==26?3-j*2:j*2);
			*(uint16_t*)(r+rl-2)=mv(i^2);
			*(uint16_t*)(r+rl-6+2*j)=rl;
			*(uint16_t*)(r+rl-6+2*!j)=-1;
		case(31)i=mv(i);
		case(32 ... 35)
			pg[i^1]=pg[i^2]=pg[i^3]=rl;
			i=i&~3|op&3;
		case(36);
		}
		op=opc(ps[(i=mv(i))>>2]);
	}
}
int main(int argc,char**argv){
	ran=fopen("/dev/urandom","r");
	FILE*prog=fopen(argv[1],"r");
#ifdef SPACE
	for(int j=0;j<80;j++)
		for(int i=0;i<25;i++)ps[i+j*32]=SPACE;
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
	memset(pro,0,2560);
	memset(pg,-1,20480);
	uint8_t*op=r+comp(0);
	for(;;){
		fprintf(stdout,"\n%d %d$",*op,sp-st);
		switch(*op){
		default:__builtin_unreachable();
		case(0)
			*++sp=*(int32_t*)(op+1);
			op+=4;
		case(10)if(sp>st){sp--;*sp+=sp[1];}else if(sp<st)*++sp=0;
		case(11)if(sp>st){sp--;*sp-=sp[1];}else if(sp==st)*sp*=-1;else*++sp=0;
		case(12)if(sp>st){sp--;*sp*=sp[1];}else*(sp=st)=0;
		case(13)if(sp>st){sp--;if(sp[1])*sp/=sp[1];}else*(sp=st)=0;
		case(14)if(sp>st){sp--;if(sp[1])*sp%=sp[1];}else*(sp=st)=0;
		case(15)if(sp>st){sp--;*sp=*sp>sp[1];}else{st[0]=sp==st&&0>*sp;sp=st;}
		case(16)if(sp>=st)*sp=!*sp;else*(sp=st)=1;
		case(17)sp-=sp>=st;
		case(18)if(sp>=st){sp[1]=*sp;sp++;}else{sp=st+1;st[0]=st[1]=0;}
		case(19)
		if(sp>st){
			int32_t t=*sp;
			*sp=sp[-1];
			sp[-1]=t;
		}else if(sp==st){sp[1]=*sp;*sp++=0;}else{sp=st+1;st[0]=st[1]=0;}
		case(20)printf("%d ",sp>=st?*sp--:0);
		case(21)putchar(sp>=st?*sp--:0);
		case(22)*++sp=getchar();
		case(23)scanf("%d",++sp);
		case(24){
			int x,y;
			switch(sp-st){
			default:
				sp-=3;
				x=(sp[2]>=0&&sp[2]<80?sp[2]*32:0)+(sp[3]>=0&&sp[3]<25?sp[3]:0);
				y=ps[x];
				ps[x]=sp[1];
			case(-1)
				x=0;
				y=ps[0];
				ps[0]=0;
			case(0)
				sp=st-1;
				x=sp[1]<25&&sp[1]>=0?sp[1]*32:0;
				y=ps[x];
				ps[x]=0;
			case(1)
				sp=st-1;
				x=(sp[1]>=0&&sp[1]<80?sp[1]*32:0)+(sp[2]>=0&&sp[2]<25?sp[2]:0);
				y=ps[x];
				ps[x]=0;
			}
			if(y!=ps[x]&&pro[x]&&(pro[x]==2||opc(y)!=opc(ps[x]))){
				memset(pro,0,2560);
				memset(pg,-1,20480);
				rl=0;
				op=r+comp(*(uint16_t*)(op+1));
				continue;
			}else op+=2;
		}
		case(25)
			if(sp>st){sp--;*sp=*sp<80&&*sp>=0&&sp[1]<25&&sp[1]>=0?ps[*sp*32+sp[1]]:0;}
			else if(sp==st)*sp=*sp<25&&*sp>=0?ps[*sp]:0;else*++sp=ps[0];
		case(26){
			int j=sp>=st&&*sp--;
			uint16_t*i=(uint16_t*)(op+1+j*2);
			if(*i==(uint16_t)-1){
				*i=rl;
				op=r+comp(*(uint16_t*)(op+5));
			}else op=r+*i;
			continue;
		}
		case(27){
			int j=getc(ran)&3;
			uint16_t*i=(uint16_t*)(op+1+j*2);
			if(*i==(uint16_t)-1){
				*i=rl;
				op=r+comp(mv(*(uint16_t*)(op+9)|j));
			}else op=r+*i;
			continue;
		}
		case(28)
			op=r+*(uint16_t*)(op+1);
			continue;
		}
		op++;
	}
}