	OP(p0)*++sp=0;
	nop:LOOP;
	OP(p1)*++sp=1;
	LOOP;
	OP(p2)*++sp=2;
	LOOP;
	OP(p3)*++sp=3;
	LOOP;
	OP(p4)*++sp=4;
	LOOP;
	OP(p5)*++sp=5;
	LOOP;
	OP(p6)*++sp=6;
	LOOP;
	OP(p7)*++sp=7;
	LOOP;
	OP(p8)*++sp=8;
	LOOP;
	OP(p9)*++sp=9;
	LOOP;
	OP(add)if(sp>st){sp--;*sp+=sp[1];}
	LOOP;
	OP(sub)if(sp>st){sp--;*sp-=sp[1];}else if(sp==st)*sp*=-1;
	LOOP;
	OP(mul)if(sp>st){sp--;*sp*=sp[1];}else sp=st-1;
	LOOP;
	OP(dvi)if(sp>st){sp--;
		if(sp[1])*sp/=sp[1];
		}else sp=st-1;
	LOOP;
	OP(mod)if(sp>st){sp--;
		if(sp[1])
		#ifdef FLOAT
		*sp=fmod(*sp,sp[1]);
		#else
		*sp%=sp[1];
		#endif
		}else sp=st-1;
	LOOP;
	OP(not)if(sp>=st)*sp=!*sp;else*(sp=st)=1;
	LOOP;
	OP(gt)if(sp>st){sp--;*sp=*sp>sp[1];}else if(sp==st)*sp=0>*sp;
	LOOP;
	OP(dup)if(sp>=st){sp[1]=*sp;sp++;}
	LOOP;
	OP(pop)sp-=sp>=st;
	LOOP;
	OP(hop)HOP;
	OP(hif)goto*(sp>=st&&*sp--?&&gwe:&&gea);
	OP(vif)goto*(sp>=st&&*sp--?&&gno:&&gso);
	OP(swp)if(sp>st){
		WORD tmp=*sp;
		*sp=sp[-1];
		sp[-1]=tmp;
	}else if(sp==st)*++sp=0;
	LOOP;
	OP(stm)switch(dir){
	default:__builtin_unreachable();
	case 0:for(;;){
		pt+=32;if(pt-pg>=2560)pt-=2560;
		if(ps[pt-pg]=='"'){LOOP;}
		*++sp=ps[pt-pg];
	}
	case 1:for(;;){
		if(!(pt-pg&31))pt+=25;pt--;
		if(ps[pt-pg]=='"'){LOOP;}
		*++sp=ps[pt-pg];
	}
	case 2:for(;;){
		pt-=32;if(pt<pg)pt+=2560;
		if(ps[pt-pg]=='"'){LOOP;}
		*++sp=ps[pt-pg];
	}
	case 3:for(;;){
		pt++;if((pt-pg&31)>24)pt-=25;
		if(ps[pt-pg]=='"'){LOOP;}
		*++sp=ps[pt-pg];
	}
	}
	OP(rnd)RND(
#ifdef FRAND
	getc(rand)
#else
	rand()
#endif
	&3);
	OP(get)
		if(sp>st){
			sp--;
			int x=*sp<<5|sp[1];
			*sp=x>=0&&x<2560?ps[x]:0;
		}else if(sp==st)*sp=*sp<25&&*sp>=0?ps[(int)*sp]:0;else*++sp=ps[0];
	LOOP;
	OP(put)switch(sp-st){
		int x;
		case-1:
			ps[0]=0;
			pg[0]=FT(7);
		break;case 0:
			sp=st-1;
			x=sp[1]<25&&sp[1]>=0?sp[1]:0;
			ps[x]=0;
			pg[x]=FT(7);
		break;case 1:
			sp=st-1;
			x=(sp[1]>=0&&sp[1]<80?sp[1]*32:0)|(sp[2]>=0&&sp[2]<25?sp[2]:0);
			ps[x]=0;
			pg[x]=FT(7);
		break;default:
			sp-=3;
			x=(sp[2]>=0&&sp[2]<80?sp[2]*32:0)|(sp[3]>=0&&sp[3]<25?sp[3]:0);
			ps[x]=sp[1];
			pg[x]=sp[1]>32&&sp[1]<127?FT(sp[1]-33):FT(7);
	}
	LOOP;
	OP(och)putchar(sp>=st?*sp--:0);
	LOOP;
	OP(oin)printf(WFMT" ",sp>=st?*sp--:0);
	LOOP;
	OP(ich)*++sp=getchar();
	LOOP;
	OP(iin)scanf(WFMT,++sp);
	LOOP;