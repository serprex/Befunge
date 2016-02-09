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
uint16_t pg[10240],rl,ct[65536];
uint8_t pro[640],r[65536];
int mv(int i){
	switch(i&3){
	case 0:return i>=10112?i-10112:i+128;
	case 1:return i&124?i-4:i+96;
	case 2:return i<128?i+10112:i-128;
	case 3:return (i+4&124)<100?i+4:i-96;
	}
}
int opc(int i){
	static const uint8_t loc[]={16,29,31,17,14,23,36,36,36,12,10,21,11,20,13,0,1,2,3,4,5,6,7,8,9,18,36,34,36,32,26,30,36,36,36,36,36,36,36,36,36,36,36,36,36,36,36,36,36,36,36,36,36,36,36,36,36,36,36,19,36,33,28,15,36,36,36,36,36,36,24,36,36,36,36,36,36,36,36,25,36,36,36,36,36,35,36,36,36,36,36,27,36,22};
	return i<33||i>126?36:loc[i-33];
}
int comp(int i){
	int cl=0;
	while(pg[i=mv(i)]==(uint16_t)-1){
		int op=opc(ps[i>>2]);
		pro[i>>4]|=1<<(i>>1&6);
		if(op<30){
			pg[i]=rl;
			ct[cl]=rl;
			ct[cl+1]=i;
			cl+=2;
		}
		switch(op){
		default:__builtin_unreachable();
		case(0 ... 9)
			r[rl]=0;
			rl+=5;
			*++sp=*(int32_t*)(r+rl-4)=op;
		case(10 ... 24)
			r[rl]=op;
			rl++;
			switch(op){
			default:__builtin_unreachable();
			case(10)if(sp>st){sp--;*sp+=sp[1];}else if(sp<st)*++sp=0;
			case(11)if(sp>st){sp--;*sp-=sp[1];}else if(sp==st)*sp*=-1;else*++sp=0;
			case(12)if(sp>st){sp--;*sp*=sp[1];}else*(sp=st)=0;
			case(13)if(sp>st){sp--;if(sp[1])*sp/=sp[1];}else*(sp=st)=0;
			case(14)if(sp>st){sp--;if(sp[1])*sp%=sp[1];}else*(sp=st)=0;
			case(15)if(sp>st){sp--;*sp=*sp>sp[1];}else{st[0]=sp==st&&0>*sp;sp=st;}
			case(16)
			if(sp>=st){
				if(cl>3&&!r[ct[cl-4]]){
					pg[i]=-1;
					cl-=2;
					rl--;
					*(int32_t*)(r+rl-4)=*sp=!*sp;
				}else*sp=!*sp;
			}else*(sp=st)=1;
			case(17)
			if(cl>3&&(!r[ct[cl-4]]||r[ct[cl-4]]==18)){
				pg[i]=-1;
				if(ct[cl-3]!=(uint16_t)-1)pg[ct[cl-3]]=-1;
				rl=ct[cl-4];
				cl-=4;
				sp--;
			}else sp-=sp>=st;
			case(18)if(sp>=st){sp[1]=*sp;sp++;}else{sp=st+1;st[0]=st[1]=0;}
			case(19)
			if(sp>st){
				int32_t t=*sp;
				*sp=sp[-1];
				sp[-1]=t;
				if(cl>5&&!r[ct[cl-4]]&&!r[ct[cl-6]]){
					pg[i]=-1;
					if(ct[cl-3]!=(uint16_t)-1)pg[ct[cl-3]]=-1;
					cl-=2;
					rl--;
					*(int32_t*)(r+rl-4)=*sp;
					*(int32_t*)(r+rl-9)=sp[-1];
				}
			}else if(sp==st){sp[1]=*sp;*sp++=0;}else{sp=st+1;st[0]=st[1]=0;}
			case(20)printf("%d ",sp>=st?*sp--:0);
			case(21)putchar(sp>=st?*sp--:0);
			case(22)*++sp=getchar();
			case(23)scanf("%d",++sp);
			case(24)
				if(sp>st){
					sp--;
					if(*sp<80&&*sp>=0&&sp[1]<25&&sp[1]>=0){
						if(cl>5&&!r[ct[cl-6]]&&!r[ct[cl-4]]){
							pg[i]=-1;
							if(ct[cl-3]!=(uint16_t)-1)pg[ct[cl-3]]=-1;
							cl-=4;
							rl-=8;
							r[rl-3]=1;
							*sp=ps[*(uint16_t*)(r+rl-2)=*sp<<5|sp[1]];
						}else*sp=ps[*sp<<5|sp[1]];
					}else*sp=0;
				}else if(sp==st)*sp=*sp<25&&*sp>=0?ps[*sp]:0;else*++sp=ps[0];
			}
			if(op<16&&cl>3){
				switch(r[ct[cl-4]]){
				case(0)
					pg[i]=-1;
					if(cl>5&&!r[ct[cl-6]]){
						if(ct[cl-3]!=(uint16_t)-1)pg[ct[cl-3]]=-1;
						cl-=4;
						rl-=6;
						*(int32_t*)(r+rl-4)=*sp;
					}else{
						cl-=2;
						rl--;
						r[rl-5]=19-op;
					}
				case(18)
					if(cl>5&&!r[ct[cl-6]]){
						pg[i]=-1;
						if(ct[cl-3]!=(uint16_t)-1)pg[ct[cl-3]]=-1;
						cl-=4;
						rl-=2;
						*(int32_t*)(r+rl-4)=*sp;
					}
				}
			}
		case(25){
			r[rl]=25;
			rl+=3;
			*(uint16_t*)(r+rl-2)=i;
			int x,y;
			switch(sp-st){
			default:
				sp-=3;
				x=(sp[2]>=0&&sp[2]<80?sp[2]<<5:0)|(sp[3]>=0&&sp[3]<25?sp[3]:0);
				y=ps[x];
				ps[x]=sp[1];
			case(-1)
				x=0;
				y=ps[0];
				ps[0]=0;
			case(0)
				sp=st-1;
				x=sp[1]<25&&sp[1]>=0?sp[1]<<5:0;
				y=ps[x];
				ps[x]=0;
			case(1)
				sp=st-1;
				x=(sp[1]>=0&&sp[1]<80?sp[1]<<5:0)|(sp[2]>=0&&sp[2]<25?sp[2]:0);
				y=ps[x];
				ps[x]=0;
			}
			if(y!=ps[x]&&(pro[x>>2]&3<<(x&3)*2)&&((pro[x>>2]&2<<(x&3)*2)||opc(y)!=opc(ps[x]))){
				memset(pro,0,640);
				memset(pg,-1,20480);
				cl=rl=0;
			}else if(cl>5&&!r[ct[cl-6]]&&!r[ct[cl-4]]){
				pg[i]=-1;
				if(ct[cl-3]!=(uint16_t)-1)pg[ct[cl-3]]=-1;
				cl-=4;
				rl-=8;
				r[rl-5]=2;
				*(uint16_t*)(r+rl-4)=x;
				*(uint16_t*)(r+rl-2)=i;
			}
		}
		case(26){
			r[rl]=26;
			rl+=11;
			*(uint16_t*)(r+rl-2)=i&~3;
			memset(r+rl-10,-1,8);
			int j=getc(ran)&3;
			i=i&~3|j;
			*(uint16_t*)(r+rl-10+2*j)=rl;
		}
		case(27 ... 28){
			int j=sp>=st&&*sp--;
			i=i&~3|(op==27?3-j*2:j*2);
			r[rl]=27;
			rl+=7;
			*(uint16_t*)(r+rl-2)=i^2;
			*(uint16_t*)(r+rl-6+2*j)=rl;
			*(uint16_t*)(r+rl-6+2*!j)=-1;
		}
		case(29){
			int j=1;
			while(ps[(i=mv(i))>>2]!='"'){
				j=0;
				pro[i>>4]|=2<<(i>>1&6);
				r[rl]=0;
				rl+=5;
				*++sp=*(int32_t*)(r+rl-4)=ps[i>>2];
				cl+=2;
				ct[cl-1]=-1;
				ct[cl-2]=rl;
			}
			cl-=2;
			pro[i>>4]|=2<<(i>>1&6);
			if(j)pg[ct[cl+1]]=(uint16_t)-1;
		}
		case(30)exit(0);
		case(31)i=mv(i);
		case(32 ... 35)i=i&~3|op&3;
		case(36);
		}
	}
	r[rl]=28;
	rl+=3;
	return*(uint16_t*)(r+rl-2)=pg[i];
}
int main(int argc,char**argv){
	ran=fopen("/dev/urandom","r");
	FILE*prog=fopen(argv[1],"r");
#if SPACE
	for(int j=0;j<80;j++)
		for(int i=0;i<25;i++)ps[i|j<<5]=SPACE;
#endif
	for(int i=0;i<25;i++){
		for(int j=0;j<80;j++){
			int c=getc(prog);
			if(c=='\n')goto FoundNew;
			if(c==-1)goto RunProg;
			ps[i|j<<5]=c;
		}
		for(;;){
			int c=getc(prog);
			if(c=='\n')goto FoundNew;
			if(c==-1)goto RunProg;
		}
		FoundNew:;
	}
	RunProg:fclose(prog);
	memset(pro,0,640);
	memset(pg,-1,20480);
	uint8_t*op=r+comp(10112);
	static void*ft[]={
		&&OP0,&&OP1,&&OP2,0,&&OP4,&&OP5,&&OP6,&&OP7,&&OP8,&&OP9,
		&&OP10,&&OP11,&&OP12,&&OP13,&&OP14,&&OP15,&&OP16,&&OP17,&&OP18,&&OP19,
		&&OP20,&&OP21,&&OP22,&&OP23,&&OP24,&&OP25,&&OP26,&&OP27,&&OP28,
	};
	#define LOOP goto*ft[*op++]
	LOOP;
	OP0:
		*++sp=*(int32_t*)op;
		op+=4;
		LOOP;
	OP1:
		*++sp=ps[*(uint16_t*)op];
		op+=2;
		LOOP;
	OP2:
		op+=2;
		goto from2;
	OP4:
		if(sp>=st)*sp=*sp>*(int32_t*)op;else{st[0]=sp==st&&0>*(int32_t*)op;sp=st;}
		op+=4;
		LOOP;
	OP5:
		if(sp>=st){if(*(int32_t*)op)*sp%=*(int32_t*)op;}else*(sp=st)=0;
		op+=4;
		LOOP;
	OP6:
		if(sp>=st){if(*(int32_t*)op)*sp/=*(int32_t*)op;}else*(sp=st)=0;
		op+=4;
		LOOP;
	OP7:
		if(sp>=st)*sp*=*(int32_t*)op;else*(sp=st)=0;
		op+=4;
		LOOP;
	OP8:
		if(sp>=st)*sp-=*(int32_t*)op;else*(sp=st)=-*(int32_t*)op;
		op+=4;
		LOOP;
	OP9:
		if(sp>=st)*sp+=*(int32_t*)op;else*(sp=st)=*(int32_t*)op;
		op+=4;
		LOOP;
	OP10:if(sp>st){sp--;*sp+=sp[1];}else if(sp<st)*++sp=0;LOOP;
	OP11:if(sp>st){sp--;*sp-=sp[1];}else if(sp==st)*sp*=-1;else*++sp=0;LOOP;
	OP12:if(sp>st){sp--;*sp*=sp[1];}else*(sp=st)=0;LOOP;
	OP13:if(sp>st){sp--;if(sp[1])*sp/=sp[1];}else*(sp=st)=0;LOOP;
	OP14:if(sp>st){sp--;if(sp[1])*sp%=sp[1];}else*(sp=st)=0;LOOP;
	OP15:if(sp>st){sp--;*sp=*sp>sp[1];}else{st[0]=sp==st&&0>*sp;sp=st;}LOOP;
	OP16:if(sp>=st)*sp=!*sp;else*(sp=st)=1;LOOP;
	OP17:sp-=sp>=st;LOOP;
	OP18:if(sp>=st){sp[1]=*sp;sp++;}else{sp=st+1;st[0]=st[1]=0;}LOOP;
	OP19:
	if(sp>st){
		int32_t t=*sp;
		*sp=sp[-1];
		sp[-1]=t;
	}else if(sp==st){sp[1]=*sp;*sp++=0;}else{sp=st+1;st[0]=st[1]=0;}
	LOOP;
	OP20:printf("%d ",sp>=st?*sp--:0);LOOP;
	OP21:putchar(sp>=st?*sp--:0);LOOP;
	OP22:*++sp=getchar();LOOP;
	OP23:scanf("%d",++sp);LOOP;
	OP24:
		if(sp>st){
			sp--;
			int x=*sp<<5|sp[1];
			*sp=x>=0&&x<2560?ps[x]:0;
		}else if(sp==st)*sp=*sp<25&&*sp>=0?ps[*sp]:0;else*++sp=ps[0];
		LOOP;
	OP25:{
		int x,y;
		switch(sp-st){
		default:
			sp-=3;
			x=(sp[2]>=0&&sp[2]<80?sp[2]<<5:0)+(sp[3]>=0&&sp[3]<25?sp[3]:0);
			y=ps[x];
			ps[x]=sp[1];
		case(-1)
			x=0;
			y=ps[0];
			ps[0]=0;
		case(0)
			sp=st-1;
			x=sp[1]<25&&sp[1]>=0?sp[1]<<5:0;
			y=ps[x];
			ps[x]=0;
		case(1)
			sp=st-1;
			x=(sp[1]>=0&&sp[1]<80?sp[1]<<5:0)+(sp[2]>=0&&sp[2]<25?sp[2]:0);
			y=ps[x];
			ps[x]=0;
		}
		if(0){from2:
			x=*(uint16_t*)(op-2);
			y=ps[x];
			ps[x]=sp>=st?*sp--:0;
		}
		if(y!=ps[x]&&pro[x>>2]&3<<(x&3)*2&&(pro[x>>2]&2<<(x&3)*2||opc(y)!=opc(ps[x]))){
			memset(pro,0,640);
			memset(pg,-1,20480);
			rl=0;
			op=r+comp(*(uint16_t*)op);
		}else op+=2;
	}LOOP;
	OP26:{
		int j=getc(ran)&3;
		uint16_t*i=(uint16_t*)(op+j*2);
		if(*i==(uint16_t)-1){
			*i=rl;
			op=r+comp(*(uint16_t*)(op+8)|j);
		}else op=r+*i;
	}LOOP;
	OP27:{
		int j=sp>=st&&*sp--;
		uint16_t*i=(uint16_t*)(op+j*2);
		if(*i==(uint16_t)-1){
			*i=rl;
			op=r+comp(*(uint16_t*)(op+4));
		}else op=r+*i;
	}LOOP;
	OP28:op=r+*(uint16_t*)op;LOOP;
}