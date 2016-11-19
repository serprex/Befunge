#include <stdlib.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <time.h>

#include <stack>
#include <vector>
#include <unordered_map>

#if defined __GNUC__ && __GNUC__*100+__GNUC_MINOR__<405
	#define __builtin_unreachable()
#endif
#define case(x) break;case x:;

struct coord {
	int32_t x, y;

	bool operator==(const coord &other) const {
		return x == other.x && y == other.y;
	}
};
struct cell {
	size_t joff[4];
	int32_t val;
	bool exec;

	cell(){
		joff[0] = -1;
		joff[1] = -1;
		joff[2] = -1;
		joff[3] = -1;
		val = 0;
		exec = false;
	}

	cell(int v){
		joff[0] = -1;
		joff[1] = -1;
		joff[2] = -1;
		joff[3] = -1;
		val = v;
		exec = false;
	}
};

struct hash_coord {
	size_t operator()(const coord &xy) const
	{
		uint64_t xy64 = *(uint64_t*)&xy;
		if (sizeof(size_t) == 8) {
			return (size_t)xy64;
		} else {
			return std::hash<uint64_t>()(xy64);
		}
	}
};

std::stack<int> st;
std::vector<uint8_t> code;
std::unordered_map<coord, cell, hash_coord> ps;
int32_t mnx, mny, mxx, mxy;

int opc(int i){
	static const uint8_t loc[]={16,29,31,17,14,23,36,36,36,12,10,21,11,20,13,0,1,2,3,4,5,6,7,8,9,18,36,34,36,32,26,30,36,36,36,36,36,36,36,36,36,36,36,36,36,36,36,36,36,36,36,36,36,36,36,36,36,36,36,19,36,33,28,15,36,36,36,36,36,36,24,36,36,36,36,36,36,36,36,25,36,36,36,36,36,35,36,36,36,36,36,27,36,22};
	return i<33||i>126?36:loc[i-33];
}

int pop() {
	if (st.empty()) return 0;
	int v = st.top();
	st.pop();
	return v;
}

size_t readsize(size_t offs){
	size_t ret = 0;
	for (size_t i=0; i<sizeof(size_t); i++) {
		ret <<= 8;
		ret |= code[offs+sizeof(size_t)-1-i];
	}
	return ret;
}
void writesize(size_t offs, size_t val){
	for (size_t i=0; i<sizeof(size_t); i++) {
		code[offs+i] = val & 255;
		val >>= 8;
	}
}
void pushsize(size_t val){
	for (size_t i=0; i<sizeof(size_t); i++) {
		code.push_back(val & 255);
		val >>= 8;
	}
}
int32_t readint32(size_t offs){
	int32_t ret = 0;
	for (int i=0; i<4; i++) {
		ret <<= 8;
		ret |= code[offs+3-i];
	}
	return ret;
}

void pushint32(int32_t val){
	for (int i=0; i<4; i++) {
		code.push_back(val & 255);
		val >>= 8;
	}
}

coord readcoord(size_t offs){
	coord xy;
	xy.x = readint32(offs);
	xy.y = readint32(offs+4);
	return xy;
}

void pushcoord(coord xy){
	pushint32(xy.x);
	pushint32(xy.y);
}

struct cursor {
	coord xy;
	uint8_t dir;

	void readcurse(size_t offs){
		xy = readcoord(offs);
		dir = code[offs+9];
	}

	void pushcurse(){
		pushcoord(xy);
		code.push_back(dir);
	}

	void mv(){
		switch (dir) {
			default:__builtin_unreachable();
			case(0)xy.x=xy.x==mxx?mnx:xy.x+1;
			case(1)xy.y=xy.y==mny?mxy:xy.y-1;
			case(2)xy.x=xy.x==mnx?mxx:xy.x-1;
			case(3)xy.y=xy.y==mxy?mny:xy.y+1;
		}
	}

	size_t compile(){
		while(true){
			cell*ch = &ps[xy];
			if (ch->joff[dir] != (size_t)-1){
				if (ch->joff[dir] == code.size()) {
					while(true);
				}
				code.push_back(30);
				pushsize(ch->joff[dir]);
				return ch->joff[dir];
			}
			int op=opc(ch->val);
			ch->joff[dir] = code.size();
			ch->exec = true;
			switch(op){
			default:__builtin_unreachable();
			case(0 ... 9)
				code.push_back(op);
				st.push(op);
			case(10 ... 24)
				code.push_back(op);
				switch(op){
				default:__builtin_unreachable();
				case(10)st.push(pop()+pop());
				case(11){
					int x=pop();
					int y=pop();
					st.push(y-x);
				}
				case(12)st.push(pop()*pop());
				case(13){
					int x=pop();
					int y=pop();
					st.push(y/x);
				}
				case(14){
					int x=pop();
					int y=pop();
					st.push(y%x);
				}
				case(15){
					int x=pop();
					int y=pop();
					st.push(y>x);
				}
				case(16)st.push(!pop());
				case(17)if(!st.empty())st.pop();
				case(18){
					int x = pop();
					st.push(x);
					st.push(x);
				}
				case(19){
					int x=pop();
					int y=pop();
					st.push(x);
					st.push(y);
				}
				case(20)printf("%d ",pop());
				case(21)putchar(pop());
				case(22)st.push(getchar());
				case(23){
					int x;
					scanf("%d",&x);
					st.push(x);
				}
				case(24){
					coord getxy;
					getxy.y=pop();
					getxy.x=pop();
					st.push(ps[getxy].val);
				}
				}
			case(25){
				coord putxy;
				putxy.y=pop();
				putxy.x=pop();
				int z=pop();
				cell*ch=&ps[putxy];
				ch->val = z;
				if (ch->exec){
					code.clear();
					for (auto& kv : ps) {
						kv.second.joff[0] = (size_t)-1;
						kv.second.joff[1] = (size_t)-1;
						kv.second.joff[2] = (size_t)-1;
						kv.second.joff[3] = (size_t)-1;
						kv.second.exec = false;
					}
				} else {
					code.push_back(25);
					pushcurse();
				}
			}
			case(26){
				dir=rand()&3;
				code.push_back(26);
				pushcoord(xy);
				size_t jo = code.size();
				for (size_t i=0; i<sizeof(size_t)*4; i++){
					code.push_back(-1);
				}
				writesize(jo + 8 + dir * sizeof(size_t), code.size());
			}
			case(27 ... 28){
				int32_t x = pop();
				dir=x?(op==27?1:2):(op==27?3:0);
				code.push_back(op);
				size_t jo = code.size();
				pushcoord(xy);
				for (size_t i=0; i<sizeof(size_t)*2; i++){
					code.push_back(-1);
				}
				writesize((x ? jo : jo+sizeof(size_t)) + 8, code.size());
			}
			case(29){
				while(true){
					mv();
					cell*sch=&ps[xy];
					sch->exec=true;
					if (sch->val == '"')break;
					st.push(sch->val);
					code.push_back(29);
					pushint32(sch->val);
				}
			}
			case(30)exit(0);
			case(31)mv();
			case(32 ... 35)dir=op&3;
			case(36);
			}
			mv();
		}
	}
};

int main(int,char**argv){
	srand(time(NULL));
	FILE*prog=fopen(argv[1],"r");
	coord readxy;
	readxy.x = 0;
	readxy.y = 0;
	for(;;){
		int c=getc(prog);
		if(c=='\n') {
			readxy.x=0;
			readxy.y++;
			continue;
		} else if(c==-1) break;
		ps[readxy] = cell(c);
		readxy.x++;
		if (readxy.x>mxx)mxx=readxy.x;
	}
	fclose(prog);
	mxy=readxy.y;
	cursor curse;
	curse.xy.x=0;
	curse.xy.y=0;
	curse.dir=0;
	size_t pc = curse.compile();
	while (true) {
		//printf("%ld\t%d\t:%ld\n", pc, code[pc], st.size());
		switch (code[pc++]) {
		default:__builtin_unreachable();
		case(0 ... 9) st.push(code[pc-1]);
		case(10)st.push(pop()+pop());
		case(11){
			int x=pop();
			int y=pop();
			st.push(y-x);
		}
		case(12)st.push(pop()*pop());
		case(13){
			int x=pop();
			int y=pop();
			st.push(y/x);
		}
		case(14){
			int x=pop();
			int y=pop();
			st.push(y%x);
		}
		case(15){
			int x=pop();
			int y=pop();
			st.push(y>x);
		}
		case(16)st.push(!pop());
		case(17)if(!st.empty())st.pop();
		case(18){
			int x = pop();
			st.push(x);
			st.push(x);
		}
		case(19){
			int x=pop();
			int y=pop();
			st.push(x);
			st.push(y);
		}
		case(20)printf("%d ",pop());
		case(21)putchar(pop());
		case(22)st.push(getchar());
		case(23){
			int x;
			scanf("%d",&x);
			st.push(x);
		}
		case(24){
			coord getxy;
			getxy.y=pop();
			getxy.x=pop();
			st.push(ps[getxy].val);
		}
		case(25){
			coord putxy;
			putxy.y=pop();
			putxy.x=pop();
			int z=pop();
			cell*ch=&ps[putxy];
			ch->val = z;
			if (ch->exec){
				curse.readcurse(pc);
				code.clear();
				for (auto& kv : ps) {
					kv.second.joff[0] = (size_t)-1;
					kv.second.joff[1] = (size_t)-1;
					kv.second.joff[2] = (size_t)-1;
					kv.second.joff[3] = (size_t)-1;
					kv.second.exec = false;
				}
				curse.mv();
				pc = curse.compile();
			} else {
				pc += 9;
			}
		}
		case(26){
			int dir=rand()&3;
			size_t jo = readsize(pc + 8 + dir*sizeof(size_t));
			if (jo == (size_t)-1){
				writesize(pc + 8 + dir*sizeof(size_t), code.size());
				curse.xy = readcoord(pc);
				curse.dir = dir;
				curse.mv();
				pc = curse.compile();
			} else {
				pc = jo;
			}
		}
		case(27 ... 28){
			int32_t x = pop();
			size_t jo = readsize((x?pc:pc+sizeof(size_t))+8);
			if (jo == (size_t)-1){
				writesize((x?pc:pc+sizeof(size_t))+8, code.size());
				curse.xy = readcoord(pc);
				curse.dir = x?(code[pc-1]==27?1:2):(code[pc-1]==27?3:0);
				curse.mv();
				pc = curse.compile();
			} else {
				pc = jo;
			}
		}
		case(29){
			st.push(readint32(pc));
			pc += 4;
		}
		case(30){
			pc = readsize(pc);
		}
		}
	}
	return 0;
}