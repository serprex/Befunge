"use strict";
function varint (v, value) {
	while (true) {
		var b = value & 127;
		value >>= 7;
		if ((value == 0 && ((b & 0x40) == 0)) || ((value == -1 && ((b & 0x40) == 0x40)))) {
			return v.push(b);
		}
		else {
			v.push(b | 128);
		}
	}
}


function varuint (v, value, padding) {
	padding |= 0;
	do {
		var b = value & 127;
		value >>= 7;
		if (value != 0 || padding > 0) {
			b |= 128;
		}
		v.push(b);
		padding--;
	} while (value != 0 || padding > -1);
}

function pushString(v, str) {
	for (var i=0; i<str.length; i++) {
		v.push(str.charCodeAt(i));
	}
}

function pushArray(sink, data) {
	return Array.prototype.push.apply(sink, data);
}

var novars = [[], [null], [null, null], [null, null, null]];
function Op(op, arg) {
	this.meta = metas[op];
	this.n = null;
	this.arg = arg;
	this.vars = novars[this.meta.siop];
	this.sd = 0;
	this.dep = 0;
	this.si = new Set();
}
function Meta(op, siop, so, ev) {
	this.op = op;
	this.siop = siop;
	this.so = so;
	this.eval = eval;
}
var metas = [
	new Meta(0, 0, 1, (op, ctx) => {
		ctx.push(op.arg);
		return op.n;
	}),
	new Meta(1, 2, 1, (op, ctx) => {
		var a = ctx.pop(), b = ctx.pop();
		switch (op.arg){
		case "+":b+=a;break;
		case "-":b-=a;break;
		case "*":b*=a;break;
		case "/":b/=a;break;
		case "%":b%=a;break;
		case ">":b=b>a;break;
		}
		ctx.push(b|0);
		return op.n;
	}),
	new Meta(2, 1, 1, (op, ctx) => {
		ctx.push(!ctx.pop());
		return op.n;
	}),
	new Meta(3, 1, 0, (op, ctx) => {
		ctx.pop();
		return op.n;
	}),
	new Meta(4, 1, 2, (op, ctx) => {
		if (ctx.sp) {
			var a = ctx.pop();
			ctx.push(a);
			ctx.push(a);
		}
		return op.n;
	}),
	new Meta(5, 2, 2, (op, ctx) => {
		var a = ctx.pop(), b = ctx.pop();
		ctx.push(a);
		ctx.push(b);
		return op.n;
	}),
	new Meta(6, 1, 0, (op, ctx) => {
		if (op.arg) ctx.imp.q(ctx.pop());
		else ctx.imp.p(ctx.pop());
		return op.n;
	}),
	new Meta(7, 0, 1, (op, ctx) => {
		ctx.push((op.arg ? ctx.imp.i : ctx.imp.c)());
		return op.n;
	}),
	new Meta(8, 2, 1, (op, ctx) => {
		var y = ctx.pop(), x = ctx.pop();
		if (0 <= x && x < 80 && 0 <= y && y < 25) {
			y=0xce00+((y|x<<5)<<2);
			ctx.push(ctx.mem[y]|ctx.mem[y|1]<<8|ctx.mem[y|2]<<16|ctx.mem[y|3]<<24);
		} else {
			ctx.push(0);
		}
		return op.n;
	}),
	new Meta(9, 3, 0, (op, ctx) => {
		var y = ctx.pop(), x = ctx.pop(), z = ctx.pop();
		if (0 <= x && x < 80 && 0 <= y && y < 25) {
			y|=x<<5;
			var proidx = 0xf600 + y;
			y<<=2;
			ctx.mem[0xce00+y]=z;
			ctx.mem[0xce01+y]=z>>8;
			ctx.mem[0xce02+y]=z>>16;
			ctx.mem[0xce03+y]=z>>24;
			if (ctx.mem[proidx]) {
				ctx.mem.fill(0, 0xf600, 0x10000);
				return op.arg<<16|ctx.sp;
			}
		}
		return op.n;
	}),
	new Meta(10, 0, 0, (op, ctx) => {
		var a = ctx.imp.r4();
		return a == 3 ? op.n : op.arg[a];
	}),
	new Meta(11, 1, 0, (op, ctx) => {
		return ctx.pop() ? op.n : op.arg;
	}),
	new Meta(12, 0, 0, (op, ctx) => {
		return -1;
	}),
	new Meta(13, 1, 0, (op, ctx) => {
		return op.n;
	}),
];

function mv(i) {
	switch (i&3) {
	case 0:return i>=10112?i-10112:i+128;
	case 1:return i&124?i-4:i+96;
	case 2:return i<128?i+10112:i-128;
	case 3:return (i+4&124)<100?i+4:i-96;
	}
}

var bins={37:"%",42:"*",43:"+",45:"-",47:"/",96:">"};
var raw={33:2,36:3,58:4,92:5,103:8};
var mvs={60:2,62:0,94:1,118:3};
var ops={64:9,34:8,35:10,38:3,44:1,126:2,46:0,112:4,124:6,95:7,63:5};
function Tracer(mem){
	this.mem = mem;
	this.pg = [];
}
Tracer.prototype.trace = function(i) {
	function emit(op, arg) {
		pist.length = 0;
		var tail=inst;
		inst=new Op(13);
		tail.meta=metas[op];
		tail.n=inst;
		tail.arg=arg;
		tail.vars=novars[tail.meta.siop];
		inst.si.add(tail);
		return tail;
	}
	var inst=new Op(13), head=inst, pist=[];
	while (true) {
		i=mv(i);
		if (i in this.pg){
			let pgi=this.pg[i];
			if (inst != pgi){
				for (let pi of pist) {
					this.pg[pi]=pgi;
				}
				if (inst == head) {
					return pgi;
				}
				for (let si of inst.si){
					si.n=pgi;
					pgi.si.add(si);
				}
			}
			else {
				inst.n=inst;
			}
			return head;
		}
		this.pg[i]=inst;
		pist.push(i);
		this.mem[0xf600+(i>>2)]=1;
		if (this.mem[0xce01+(i&~3)] || this.mem[0xce02+(i&~3)] || this.mem[0xce03+(i&~3)]) {
			continue;
		}
		var i2 = this.mem[0xce00+(i&~3)];
		if (48<=i2 && i2<58) { emit(0, i2-48); }
		else if (i2 in mvs) { i=i&~3|mvs[i2]; }
		else if (i2 in bins) { emit(1, bins[i2]); }
		else if (i2 in raw) { emit(raw[i2]); }
		else if (i2 in ops) {
			i2=ops[i2];
			switch (i2) {
				case 0:case 1:emit(6, i2);break;
				case 2:case 3:emit(7, i2 == 3);break;
				case 4:emit(9, i);break;
				case 5:
					this.pg[i^1] = this.pg[i^2] = this.pg[i^3] = inst;
					var rngNode = emit(10, [this.trace(i^1), this.trace(i^2), this.trace(i^3)]);
					rngNode.arg[0].si.add(rngNode);
					rngNode.arg[1].si.add(rngNode);
					rngNode.arg[2].si.add(rngNode);
					break;
				case 6:case 7:
					var other;
					if (i2 == 6){
						other=3;
						i=i&~3|1;
					} else {
						other=0;
						i=i&~3|2;
					}
					this.pg[i^1] = this.pg[i^2] = this.pg[i^3] = inst;
					var ifNode = emit(11, this.trace(i&~3|other))
					ifNode.arg.si.add(ifNode)
					break;
				case 8:
					while (true) {
						i=mv(i);
						this.mem[0xf600+(i>>2)]=1;
						var i2 = this.mem[0xce00+(i&~3)]|this.mem[0xce01+(i&~3)]<<8|this.mem[0xce02+(i&~3)]<<16|this.mem[0xce03+(i&~3)]<<24;
						if (i2 == 34) {
							break;
						}
						emit(0, i2);
					}
					break;
				case 9:
					emit(12).n = null;
					return head;
				case 10:i=mv(i);
			}
		}
	}
}

function Interpreter(imp, sp){
	this.imp = imp[""];
	this.mem = this.imp.m;
	this.sp = sp;
}
Interpreter.prototype.pop = function() {
	if (!this.sp) return 0;
	this.sp -= 4;
	return this.mem[this.sp]|this.mem[this.sp+1]<<8|this.mem[this.sp+2]<<16|this.mem[this.sp+3]<<24;
}
Interpreter.prototype.push = function(x) {
	this.mem[this.sp]=x;
	this.mem[this.sp+1]=x>>8;
	this.mem[this.sp+2]=x>>16;
	this.mem[this.sp+3]=x>>24;
	this.sp += 4;
}
Interpreter.prototype.eval = function(ir) {
	while (true) {
		ir = ir.meta.eval(ir, this);
		if (typeof ir == "number") return ir;
	}
}

function fakepeep(n) {
	while (true) {
		if (n.sd) return;
		n.sd = -1;
		if (n.meta.op == 10) {
			fakepeep(n.arg[0]);
			fakepeep(n.arg[1]);
			fakepeep(n.arg[2]);
		} else if (n.meta.op == 11) {
			fakepeep(n.arg);
		} else if (n.meta.op == 12) {
			return;
		}
		n = n.n;
	}
}

function peep(n) {
	var cst = [];
	while (true) {
		if (n.sd) return;
		n.sd = -1;
		if (n.meta.op == 0) {
			cst.push(n);
		} else if (n.meta.op == 1) {
			var a = cst.pop();
			var b = cst.pop();
			if (a && b) {
				var c;
				switch (n.arg) {
					case "+":c=b.arg+a.arg;break;
					case "-":c=b.arg-a.arg;break;
					case "*":c=b.arg*a.arg;break;
					case "/":c=a.arg&&b.arg/a.arg;break;
					case "%":c=a.arg&&b.arg%a.arg;break;
					case ">":c=b.arg>a.arg;break;
				}
				n.meta = metas[0];
				n.arg = c;
				a.meta = metas[13];
				b.meta = metas[13];
				cst.push(n);
			} else {
				cst.push(null);
			}
		} else if (n.meta.op == 2) {
			var a = cst.pop();
			if (a) {
				n.meta = metas[0];
				n.arg = a.arg;
				a.meta = metas[13];
			} else {
				cst.push(null);
			}
		} else if (n.meta.op == 3) {
			cst.pop();
		} else if (n.meta.op == 4) {
			var a = cst.pop();
			if (a) {
				n.meta = metas[0];
				n.arg = a.arg;
				cst.push(a, n);
			} else {
				cst.push(null, null);
			}
		} else if (n.meta.op == 5) {
			var a = cst.pop(), b = cst.pop();
			cst.push(null, null);
		} else if (n.meta.op == 6) {
			cst.pop();
		} else if (n.meta.op == 7) {
			cst.push(null);
		} else if (n.meta.op == 8) {
			cst.pop();
			cst.pop();
			cst.push(null);
		} else if (n.meta.op == 9) {
			cst.length = 0;
		} else if (n.meta.op == 10) {
			cst.length = 0;
			peep(n.arg[0]);
			peep(n.arg[1]);
			peep(n.arg[2]);
		} else if (n.meta.op == 11) {
			cst.length = 0;
			peep(n.arg);
		} else if (n.meta.op == 12) {
			return;
		}
		n = n.n;
		if (n.si.size > 1) {
			cst.length = 0;
		}
	}
}

function bfRun(imp, cursor, sp) {
	console.time("built");
	console.time("build");
	var code = new Uint8Array(imp[""].m.buffer);
	var tracer = new Tracer(code);
	var ir = tracer.trace(cursor);
	peep(ir);
	if (false) {
		console.timeEnd("build");
		var ctx = new Interpreter(imp, sp);
		console.timeEnd("built");
		cursor = ctx.eval(ir);
		if (~cursor) {
			code.fill(0, 0xf600);
			return bfRun(imp, cursor>>16, cursor&65535);
		}
		console.timeEnd("start");
	} else {
		console.timeEnd("build");
		return bfCompile(ir, sp, imp).then(f => {
			console.timeEnd("built");
			cursor = f.instance.exports.f();
			if (~cursor) {
				code.fill(0, 0xf600);
				return bfRun(imp, cursor>>16, cursor&65535);
			}
			console.timeEnd("start");
		});
	}
}

function bfCompile(ir, sp, imports) {
	var bc = [0x00, 0x61, 0x73, 0x6d, 0x01, 0x00, 0x00, 0x00];

	bc.push(1); // Types

	var type = [2];

	// i32 -> void
	type.push(0x60, 1, 0x7f, 0);
	// void -> i32
	type.push(0x60, 0, 1, 0x7f);

	varuint(bc, type.length, 4);
	pushArray(bc, type);

	bc.push(2); // Imports

	var imp = [6];
	varuint(imp, 0);
	varuint(imp, 1);
	pushString(imp, "p");
	imp.push(0, 0);

	varuint(imp, 0);
	varuint(imp, 1);
	pushString(imp, "q");
	imp.push(0, 0);

	varuint(imp, 0);
	varuint(imp, 1);
	pushString(imp, "i");
	imp.push(0, 1);

	varuint(imp, 0);
	varuint(imp, 1);
	pushString(imp, "c");
	imp.push(0, 1);

	varuint(imp, 0);
	varuint(imp, 1);
	pushString(imp, "r");
	imp.push(0, 1);


	varuint(imp, 0);
	varuint(imp, 1);
	pushString(imp, "m");
	imp.push(2, 0);
	varuint(imp, 1);

	varuint(bc, imp.length, 4);
	pushArray(bc, imp);

	bc.push(3); // Funcs

	var functions = [1];

	// types: sequence of indices into the type section
	varuint(functions, 1);

	varuint(bc, functions.length, 4);
	pushArray(bc, functions);

	bc.push(7); // Exports

	var exports = [1];

	// entries: repeated export entries as described below

	exports.push(1);
	pushString(exports, "f");
	exports.push(0);
	exports.push(5);

	varuint(bc, exports.length, 4);
	pushArray(bc, exports);

	bc.push(10); // Codes

	var code = [1];

	var body = [];

	// locals
	varuint(body, 1);
	varuint(body, 2);
	body.push(0x7f);

	if (sp) {
		body.push(0x41);
		varint(body, sp);
		body.push(0x21, 0);
	}

	var blocks = [], nobr = new Set();

	function blockpile(blocks, n) {
		if (~n.sd) return;
		var block = [], dep = 0;
		while (true) {
			n.sd = blocks.length;
			if (n.meta.op == 0) {
				block.push(0x20, 0, 0x41);
				varint(block, n.arg);
				block.push(0x36, 2, 0, 0x20, 0, 0x41, 4, 0x6a, 0x21, 0);
				dep++;
			} else if (n.meta.op == 1) {
				if (dep < 2) {
					if (dep) {
						block.push(0x20, 0);
					} else {
						block.push(0x20, 0, 0x04, 0x40, 0x20, 0);
					}
					block.push(0x41, 4, 0x47, 0x04, 0x40);
				}
				switch (n.arg) {
					case "+":
						block.push(0x20, 0, 0x41, 4, 0x6b, 0x22, 0);
						block.push(0x41, 4, 0x6b);
						block.push(0x20, 0, 0x41, 4, 0x6b, 0x28, 2, 0);
						block.push(0x20, 0, 0x28, 2, 0);
						block.push(0x6a);
						block.push(0x36, 2, 0);
						break;
					case "-":
						// if sp == 4, *0 = -*0
						block.push(0x20, 0, 0x41, 4, 0x6b, 0x22, 0);
						block.push(0x41, 4, 0x6b);
						block.push(0x20, 0, 0x41, 4, 0x6b, 0x28, 2, 0);
						block.push(0x20, 0, 0x28, 2, 0);
						block.push(0x6b);
						block.push(0x36, 2, 0);
						if (dep < 2) {
							block.push(0x05);
							block.push(0x41, 0, 0x41, 0, 0x41, 0, 0x28, 2, 0, 0x6b, 0x36, 2, 0);
						}
						break;
					case "*":
						// if sp == 4, *0 = 0
						block.push(0x20, 0, 0x41, 4, 0x6b, 0x22, 0);
						block.push(0x41, 4, 0x6b);
						block.push(0x20, 0, 0x41, 4, 0x6b, 0x28, 2, 0);
						block.push(0x20, 0, 0x28, 2, 0);
						block.push(0x6c);
						block.push(0x36, 2, 0);
						if (dep < 2) {
							block.push(0x05);
							block.push(0x41, 0, 0x21, 0);
						}
						break;
					case "/":
						// if sp == 4, *0 = 0
						block.push(0x20, 0, 0x41, 4, 0x6b, 0x22, 0);
						block.push(0x41, 4, 0x6b);
						block.push(0x20, 0, 0x41, 4, 0x6b, 0x28, 2, 0);
						block.push(0x20, 0, 0x28, 2, 0);
						block.push(0x6d);
						block.push(0x36, 2, 0);
						if (dep < 2) {
							block.push(0x05);
							block.push(0x41, 0, 0x21, 0);
						}
						break;
					case "%":
						// if sp == 4, *0 = 0
						block.push(0x20, 0, 0x41, 4, 0x6b, 0x22, 0);
						block.push(0x41, 4, 0x6b);
						block.push(0x20, 0, 0x41, 4, 0x6b, 0x28, 2, 0);
						block.push(0x20, 0, 0x28, 2, 0);
						block.push(0x6f);
						block.push(0x36, 2, 0);
						if (dep < 2) {
							block.push(0x05);
							block.push(0x41, 0, 0x21, 0);
						}
						break;
					case ">":
						// if sp == 4, *0 = 0 > *0
						block.push(0x20, 0, 0x41, 4, 0x6b, 0x22, 0);
						block.push(0x41, 4, 0x6b);
						block.push(0x20, 0, 0x41, 4, 0x6b, 0x28, 2, 0);
						block.push(0x20, 0, 0x28, 2, 0);
						block.push(0x4a);
						block.push(0x36, 2, 0);
						if (dep < 2) {
							block.push(0x05);
							block.push(0x41, 0, 0x41, 0, 0x41, 0, 0x28, 2, 0, 0x4a, 0x36, 2, 0);
						}
						break;
				}
				if (dep < 2) {
					block.push(0x0b);
					if (dep == 0) {
						block.push(0x0b);
					} else if (~"*/%".indexOf(n.arg)) {
						dep = 0;
					}
				} else {
					dep--;
				}
			} else if (n.meta.op == 2) {
				if (!dep) {
					block.push(0x20, 0);
					block.push(0x04, 0x40);
				}
				block.push(0x20, 0, 0x41, 4, 0x6b); // s-4
				block.push(0x20, 0, 0x41, 4, 0x6b, 0x28, 2, 0, 0x45); // !*(s-4)
				block.push(0x36, 2, 0);
				if (!dep) {
					block.push(0x05); // else *0=1, sp=4
					block.push(0x41, 0, 0x41, 1, 0x36, 2, 0);
					block.push(0x41, 4, 0x21, 0);
					block.push(0x0b);
				} else {
					dep--;
				}
			} else if (n.meta.op == 3) {
				if (dep) {
					block.push(0x20, 0, 0x41, 4, 0x6b, 0x21, 0);
					dep--;
				} else {
					block.push(0x20, 0, 0x04, 0x40);
					block.push(0x20, 0, 0x41, 4, 0x6b, 0x21, 0);
					block.push(0x0b);
				}
			} else if (n.meta.op == 4) {
				if (!dep) {
					block.push(0x20, 0, 0x04, 0x40);
				}
				block.push(0x20, 0);
				block.push(0x20, 0, 0x41, 4, 0x6b, 0x28, 2, 0); // *(s-4)
				block.push(0x36, 2, 0);
				block.push(0x20, 0, 0x41, 4, 0x6a, 0x21, 0);
				if (!dep) {
					block.push(0x0b);
				} else {
					dep++;
				}
			} else if (n.meta.op == 5) {
				if (dep < 2) {
					if (!dep) block.push(0x20, 0, 0x04, 0x40); // if >0
					block.push(0x20, 0, 0x41, 4, 0x46, 0x04, 0x40);
					// if sp == 4, *4 = 0, sp = 8
					block.push(0x41, 4, 0x41, 0, 0x36, 2, 0);
					block.push(0x41, 8, 0x21, 0);
					block.push(0x05); // else swap
				}
				block.push(0x20, 0, 0x41, 8, 0x6b, 0x22, 1); // sp-8
				block.push(0x20, 1, 0x28, 2, 4); // *(sp-4)
				block.push(0x20, 1); // sp-8
				block.push(0x20, 1, 0x28, 2, 0); // *(sp-8)
				block.push(0x36, 2, 4, 0x36, 2, 0);
				if (dep < 2) {
					block.push(0x0b);
					if (!dep) block.push(0x0b);
					else dep = 2;
				}
			} else if (n.meta.op == 6) {
				if (dep) {
					block.push(0x20, 0, 0x41, 4, 0x6b, 0x22, 0, 0x28, 2, 0); // *(s-=4) 
					dep--;
				} else {
					block.push(0x20, 0, 0x04, 0x7f); // if >0, pop
					block.push(0x20, 0, 0x41, 4, 0x6b, 0x22, 0, 0x28, 2, 0); // *(s-=4) 
					block.push(0x05, 0x41, 0); // else 0
					block.push(0x0b);
				}
				block.push(0x10, n.arg?1:0);
			} else if (n.meta.op == 7) {
				block.push(0x20, 0, 0x10, n.arg?2:3, 0x36, 2, 0);
				block.push(0x20, 0, 0x41, 4, 0x6a, 0x21, 0);
				dep++;
			} else if (n.meta.op == 8) {
				if (dep < 2) {
					if (!dep) {
						block.push(0x20, 0, 0x04, 0x40);
					}
					block.push(0x20, 0, 0x41, 4, 0x46, 0x04, 0x40); // *0 = *(0xce00+(*0<<2))
					block.push(0x41, 0, 0x41, 0, 0x28, 2, 0, 0x22, 1, 0x41, 0, 0x4d, 0x20, 1, 0x41);
					varint(block, 2560);
					block.push(0x4f, 0x72, 0x04, 0x7f, 0x41, 31, 0x05, 0x20, 1, 0x0b);
					block.push(0x41, 2, 0x74, 0x28, 2);
					varuint(block, 0xce00);
					block.push(0x36, 2, 0);
					block.push(0x05); // *(sp-=4) = *(0xce00+((*sp|*(sp-4)<<5)<<2))
				}
				block.push(0x20, 0, 0x41, 4, 0x6b, 0x22, 0, 0x41, 4, 0x6b, 0x20, 0, 0x28, 2, 0,
					0x20, 0, 0x41, 4, 0x6b, 0x28, 2, 0, 0x41, 5, 0x74, 0x72, 0x22, 1, 0x41, 0, 0x4d, 0x20, 1, 0x41);
				varint(block, 2560);
				block.push(0x4f, 0x72, 0x04, 0x7f, 0x41, 31, 0x05, 0x20, 1, 0x0b);
				block.push(0x41, 2, 0x74, 0x28, 2);
				varuint(block, 0xce00);
				block.push(0x36, 2, 0);
				if (dep < 2) {
					block.push(0x0b);
					if (!dep) {
						block.push(0x05, 0x41, 0, 0x41); // else *0 = *0xce00, sp = 4
						varint(block, 0xce00);
						block.push(0x28, 2, 0, 0x36, 2, 0, 0x41, 4, 0x21, 0);
						block.push(0x0b);
					}
				}
				dep = Math.max(dep - 1, 1);
			} else if (n.meta.op == 9) {
				if (dep < 3) {
					block.push(0x20, 0, 0x41, 8, 0x4d, 0x04, 0x40);
					if (dep < 2) block.push(0x20, 0, 0x41, 4, 0x4d, 0x04, 0x40);
					if (!dep) block.push(0x20, 0, 0x45, 0x04, 0x40, 0x41, 0, 0x41, 0, 0x36, 2, 0, 0x0b);
					if (dep < 2) block.push(0x41, 4, 0x41, 0, 0x28, 2, 0, 0x36, 2, 0, 0x41, 0, 0x41, 0, 0x36, 2, 0, 0x0b);
					block.push(0x41, 8, 0x41, 4, 0x28, 2, 0, 0x36, 2, 0, 0x41, 4, 0x41, 0, 0x28, 2, 0, 0x36, 2, 0, 0x41, 0, 0x41, 0, 0x36, 2, 0, 0x41, 12, 0x21, 0, 0x0b);
				}
				dep = Math.max(dep - 3, 0);
				block.push(0x20, 0, 0x41, 12, 0x6b, 0x22, 0);
				block.push(0x28, 2, 4, 0x22, 1, 0x41, 0, 0x4f, 0x20, 1, 0x41);
				varint(block, 80);
				block.push(0x49, 0x71, 0x20, 0, 0x28, 2, 8, 0x22, 1, 0x41, 0, 0x4f, 0x71, 0x20, 1, 0x41, 25, 0x49, 0x71, 0x04, 0x40);
				// *(0xce00 + ((sp[4]<<5|sp[8])<<2)) = sp[0]
				block.push(0x20, 0, 0x28, 2, 4, 0x41, 5, 0x74, 0x20, 0, 0x28, 2, 8, 0x72, 0x22, 1, 0x41, 2, 0x74);
				block.push(0x20, 0, 0x28, 2, 0);
				block.push(0x36, 2);
				varuint(block, 0xce00);
				// if *(0xf600 + %1), ret arg<<16|sp
				block.push(0x20, 1, 0x28, 2);
				varuint(block, 0xf600);
				block.push(0x04, 0x40, 0x41);
				varuint(block, n.arg<<16);
				block.push(0x20, 0, 0x72, 0x0f);
				block.push(0x0b, 0x0b);
			} else if (n.meta.op == 10) {
				blocks.push(block);
				blockpile(blocks, n.n);
				blockpile(blocks, n.arg[0]);
				blockpile(blocks, n.arg[1]);
				blockpile(blocks, n.arg[2]);
				if (n.n.sd > n.sd && n.arg[0].sd > n.sd && n.arg[1].sd > n.sd && n.arg[2].sd > n.sd) {
					nobr.add(block);
					block.push(0x10, 4, 0x0e, 3);
					varuint(block, n.n.sd - n.sd - 1);
					varuint(block, n.arg[0].sd - n.sd - 1);
					varuint(block, n.arg[1].sd - n.sd - 1);
					varuint(block, n.arg[2].sd - n.sd - 1);
				} else {
					block.push(0x10, 4, 0x22, 1, 0x04, 0x7f); // tee-if nextblock=r4()
					block.push(0x20, 1, 0x41, 1, 0x46, 0x04, 0x7f, 0x41);
					varuint(block, n.arg[0].sd);
					block.push(0x05, 0x20, 1, 0x41, 2, 0x46, 0x04, 0x7f, 0x41);
					varint(block, n.arg[1].sd);
					block.push(0x05, 0x41);
					varint(block, n.arg[2].sd);
					block.push(0x0b, 0x0b);
					block.push(0x05, 0x41);
					varint(block, n.n.sd);
					block.push(0x0b, 0x21, 1);
				}
				return;
			} else if (n.meta.op == 11) {
				blocks.push(block);
				blockpile(blocks, n.n);
				blockpile(blocks, n.arg);
				if (!dep) {
					block.push(0x20, 0, 0x04, 0x7f);
				}
				block.push(0x20, 0, 0x41, 4, 0x6b, 0x22, 0, 0x28, 2, 0); // *(s-=4)
				block.push(0x04, 0x7f, 0x41);
				varint(block, n.n.sd);
				block.push(0x05, 0x41);
				varint(block, n.arg.sd);
				block.push(0x0b);
				if (!dep) {
					block.push(0x05, 0x41);
					varint(block, n.arg.sd);
					block.push(0x0b);
				}
				return block.push(0x21, 1);
			} else if (n.meta.op == 12) {
				block.push(0x41, 0x7f, 0x0f);
				nobr.add(block);
				return blocks.push(block);
			}
			n = n.n;
			if (~n.sd) {
				block.push(0x41);
				varint(block, n.sd);
				block.push(0x21, 1);
				return blocks.push(block);
			}
			if (n.si.size > 1) {
				nobr.add(block);
				blocks.push(block);
				block = [];
				dep = 0;
			}
		}
	}
	blockpile(blocks, ir);

	body.push(0x03, 0x40);
	for (var i=0; i<blocks.length; i++) {
		body.push(0x02, 0x40);
	}
	body.push(0x02, 0x40);
	body.push(0x20, 1);
	body.push(0x0e);
	varuint(body, blocks.length - 1);
	for (var i=0; i<blocks.length; i++) {
		varuint(body, i);
	}
	body.push(0x0b);
	for (var i=0; i<blocks.length; i++) {
		pushArray(body, blocks[i]);
		if (!nobr.has(blocks[i])) {
			body.push(0xc);
			varuint(body, blocks.length - i);
		}
		body.push(0x0b);
	}
	body.push(0x0b);

	body.push(0);
	body.push(0x0b);

	varuint(code, body.length, 4);

	pushArray(code, body);

	varuint(bc, code.length, 4);
	pushArray(bc, code);
	//console.log(bc.length);

	return WebAssembly.instantiate(new Uint8Array(bc), imports);
}

exports.r4 = () => Math.random()*4|0;
exports.runSource = function(board, imp){
	// 0000:cdff stack
	// ce00:f5ff source
	// f600:ffff xbits
	console.time("start");
	var code = new Uint8Array(imp[""].m.buffer);
	var i = 0;
	yout:
	for (var y=0; y<25; y++) {
		for (var x=0; x<80; x++) {
			if (i == board.length) {
				for (;x<80; x++) code[0xce00+((y|x<<5)<<2)] = 32;
				for (y++; y<25; y++)
					for (x=0; x<80; x++) code[0xce00+((y|x<<5)<<2)] = 32;
				break yout;
			}
			var ch = board.charCodeAt(i++);
			if (ch == 10) {
				for (;x<80; x++) code[0xce00+((y|x<<5)<<2)] = 32;
				break;
			}
			code[0xce00+((y|x<<5)<<2)] = ch;
		}
		if (ch != 10) {
			i=board.indexOf("\n", i)+1;
			if (!i) {
				for (y++; y<25; y++)
					for (x=0; x<80; x++) code[0xce00+((y|x<<5)<<2)] = 32;
				break;
			}
		}
	}
	bfRun(imp, 10112, 0);
}
