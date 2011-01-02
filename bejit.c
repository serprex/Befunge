#include <stdlib.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#if defined __GNUC__ && __GNUC__*100+__GNUC_MINOR__<405
	#define __builtin_unreachable()
#endif
#define case(x) break;case x:;
struct rn{
	uint8_t o,c;
	int32_t d;
	void*n[4];
};
struct br{
	uint8_t o,c;
	int32_t d;
	void*n[2];
};
struct op{
	uint8_t o,c;
	int32_t d;
	void*n;
};
#define OP(x) ((struct op*)(x))
#define BR(x) ((struct br*)(x))
#define RN(x) ((struct rn*)(x))
const uint8_t at=29,loop=30;
uint16_t*restrict np,ns;
FILE*ran;
int32_t st[65536],*sp=st,ps[2560];
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
void*comp(int i){
	if(pg[i=mv(i)]){
		if(pg[i]!=&at&&pg[i]!=&loop)OP(pg[i])->c=1;
		return pg[i];
	}
	int i2=i,op=opc(ps[i>>2]);
	if(op>=31&&op<=35){
		if(op&32)i2=i&~3|op-32;
		else hash:i2=mv(i);
		for(int j=0;j<ns;j++)
			if(np[j]==i)return pg[i]=(void*)&loop;
		np=realloc(np,2*++ns);
		np[ns-1]=i;
		return pg[i]=comp(i2);
	}
	i2=ns;
	ns=0;
	switch(op){
	default:__builtin_unreachable();
	case-1:ns=i2;return pg[i]=comp(i);
	case 0 ... 9:
		pg[i]=malloc(sizeof(struct op));
		OP(pg[i])->o=0;
		OP(pg[i])->c=0;
		OP(pg[i])->d=op;
		OP(pg[i])->n=comp(i);
		return pg[i];
	case 10 ... 25:
		pg[i]=malloc(sizeof(struct op));
		OP(pg[i])->o=op;
		OP(pg[i])->c=0;
		if(op==24)OP(pg[i])->d=i;
		OP(pg[i])->n=comp(i);
		return pg[i];
	case 26:{
		int j=mv(i);
		if(ps[j>>2]=='"'){
			ns=i2;
			goto hash;
		}
		pg[i]=malloc(sizeof(struct op));
		OP(pg[i])->o=OP(pg[i])->c=0;
		OP(pg[i])->d=ps[j>>2];
		str[j>>5]|=1<<((j>>2)&7);
		struct op*s=pg[i];
		while(ps[(j=mv(j))>>2]!='"'){
			str[j>>5]|=1<<((j>>2)&7);
			s->n=malloc(sizeof(struct op));
			s=s->n;
			s->o=s->c=0;
			s->d=ps[j>>2];
		}
		s->n=comp(j);
		return pg[i];
	}
	case 28:
		pg[i]=pg[i^1]=pg[i^2]=pg[i^3]=malloc(sizeof(struct rn));
		RN(pg[i])->o=28;
		OP(pg[i])->c=0;
		for(int j=0;j<4;j++)RN(pg[i])->n[j]=comp(i^j);
		return pg[i];
	case 29:return pg[i]=(void*)&at;
	case 30:case 27:
		pg[i]=pg[i^1]=pg[i^2]=pg[i^3]=malloc(sizeof(struct br));
		BR(pg[i])->o=27;
		OP(pg[i])->c=0;
		for(int j=0;j<2;j++)BR(pg[i])->n[j]=comp(i&~3|j*2^(op&1?3:0));
		return pg[i];
	}
}
void*next(void*op){
	return OP(OP(op)->n)->c?0:OP(op)->n;
}
void opti(void*op){
	if(OP(op)->c==2||OP(op)->o==29||OP(op)->o==30)return;
	OP(op)->c=2;
	void*nx=next(op);
	if(!nx)goto exit;
	if(OP(nx)->o==29||OP(nx)->o==30)return;
	if(OP(nx)->o==27){
		switch(OP(op)->o){
			case(0)
				OP(op)->n=BR(nx)->n[!!OP(op)->d];
				free(nx);
				if(!(nx=next(op)))goto exit;
			case(16)
				BR(op)->o=27;
				BR(op)->n[0]=BR(nx)->n[1];
				BR(op)->n[1]=BR(nx)->n[0];
				free(nx);
				goto exit;
			case(18)
				BR(op)->o=3;
				BR(op)->n[0]=BR(nx)->n[0];
				BR(op)->n[1]=BR(nx)->n[1];
				free(nx);
				goto exit;
		}
	}
	if(!OP(op)->o){
		switch(OP(nx)->o){
		case(16)
			OP(op)->d=!OP(op)->d;
			OP(op)->n=OP(nx)->n;
			free(nx);
			if(!(nx=next(op)))goto exit;
		case(18)
			OP(nx)->o=0;
			OP(nx)->d=OP(op)->d;
		}
		while(!OP(op)->o&&!OP(nx)->o){
			void*p=op,*n=nx,*o=next(nx);
			if(!o)goto exit;
			while(!OP(o)->o){
				p=n;
				n=o;
				if(!(o=next(o)))goto exit;
				if(OP(o)->o==18){
					OP(o)->o=0;
					OP(o)->d=OP(n)->d;
				}else if(OP(o)->o==16){
					OP(n)->d=!OP(n)->d;
					OP(n)->n=OP(o)->n;
					free(o);
					if(!(o=next(n)))goto exit;
				}
			}
			switch(OP(o)->o){
			default:goto nostr;
			case(10)OP(p)->d+=OP(n)->d;
			case(11)OP(p)->d-=OP(n)->d;
			case(12)OP(p)->d*=OP(n)->d;
			case(13)if(OP(n)->d)OP(p)->d/=OP(n)->d;
			case(14)if(OP(n)->d)OP(p)->d%=OP(n)->d;
			case(15)OP(p)->d=OP(p)->d>OP(n)->d;
			case(19){
				int32_t t=OP(p)->d;
				OP(p)->d=OP(n)->d;
				OP(n)->d=t;
				OP(n)->n=OP(o)->n;
				free(o);
				continue;
			}
			case(24)
				OP(p)->o=2;
				OP(p)->d=OP(o)->d|(OP(p)->d<80&&OP(p)->d>=0?OP(p)->d*32:0)+(OP(n)->d<25&&OP(n)->d>=0?OP(n)->d:0)<<16;
			case(25)
				OP(p)->o=1;
				OP(p)->d=OP(p)->d<80&&OP(p)->d>=0&&OP(n)->d<25&&OP(n)->d>=0?OP(p)->d*32+OP(n)->d:0;
			}
			OP(p)->n=OP(o)->n;
			free(n);
			free(o);
			if(p==op&&!(nx=next(p)))goto exit;
		}
		nostr:if(!OP(op)->o&&OP(nx)->o>=10&&OP(nx)->o<=15){
			OP(op)->o=19-OP(nx)->o;
			OP(op)->n=OP(nx)->n;
			free(nx);
			if(!(nx=next(op)))goto exit;
		}
	}
	exit:switch(OP(op)->o){
	case(28)
		opti(RN(op)->n[3]);
		opti(RN(op)->n[2]);
	case 27:opti(BR(op)->n[1]);
	}
	opti(OP(op)->n);
}
void fropmark(void**opp){
	void*op=*opp;
	if(op==&at||op==&loop)return;
	if(OP(op)->c==3){
		*opp=0;
		return;
	}
	OP(op)->c=3;
	switch(OP(op)->o){
	case(28)
		fropmark(RN(op)->n+3);
		fropmark(RN(op)->n+2);
	case 27:fropmark(BR(op)->n+1);
	}
	fropmark(&OP(op)->n);
}
void fropswep(void*op){
	if(!op||op==&at||op==&loop)return;
	switch(OP(op)->o){
	case(28)
		fropswep(RN(op)->n[3]);
		fropswep(RN(op)->n[2]);
	case 27:fropswep(BR(op)->n[1]);
	}
	fropswep(OP(op)->n);
	free(op);
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
	cknop(0);
	void*op=comp(-128),*rt=op;
	opti(op);
	for(;;){
		switch(OP(op)->o){
		default:__builtin_unreachable();
		case(0)*++sp=OP(op)->d;
		case(1)*++sp=ps[OP(op)->d];
		case(2)goto from2;
		case(3)
			op=BR(op)->n[sp>=st&&*sp];
			continue;
		case(4)if(sp>=st){*sp=*sp>OP(op)->d;}else{st[0]=sp==st&&0>OP(op)->d;sp=st;}
		case(5)if(sp>=st){if(OP(op)->d)*sp%=OP(op)->d;}else*(sp=st)=0;
		case(6)if(sp>=st){if(OP(op)->d)*sp/=OP(op)->d;}else*(sp=st)=0;
		case(7)if(sp>=st){*sp*=OP(op)->d;}else*(sp=st)=0;
		case(8)if(sp>=st){*sp-=OP(op)->d;}else*(sp=st)=-OP(op)->d;
		case(9)if(sp>=st){*sp+=OP(op)->d;}else*(sp=st)=OP(op)->d;
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
			if(0){from2:
				x=OP(op)->d>>16;
				y=ps[x];
				ps[x]=sp>=st?*sp--:0;
			}
			if(!(y==ps[x]||!(str[x>>3]&1<<(x&7))&&(opc(y)==opc(ps[x])||!(pg[x*4]||pg[x*4+1]||pg[x*4+2]||pg[x*4+3])))){
				uint16_t d=OP(op)->d;
				fropmark(&rt);
				fropswep(rt);
				memset(str,0,320);
				for(int j=0;j<80;j++)
					for(int i=0;i<100;i++)ps[i+j*128]=0;
				if(d>>2==x)cknop(d);
				opti(rt=op=comp(d));
				continue;
			}
		case(25)
			if(sp>st){sp--;*sp=*sp<80&&*sp>=0&&sp[1]<25&&sp[1]>=0?ps[*sp*32+sp[1]]:0;}
			else if(sp==st)*sp=*sp<25&&*sp>=0?ps[*sp]:0;else*++sp=ps[0];
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