(function(){"use strict";
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
	return v;
}


function varuint (v, value, padding) {
	padding |= 0;
	do {
		var b = value & 127;
		value = value >> 7;
		if (value != 0 || padding > 0) {
			b |= 128;
		}
		v.push(b);
		padding--;
	} while (value != 0 || padding > -1);
	return v;
}

function pushString(v, str) {
	for (var i=0; i<str.length; i++) {
		v.push(str.charCodeAt(i));
	}
	return v;
}

function pushArray(sink, data) {
	return Array.prototype.push.apply(sink, data);
}

var novars = [[], [null], [null, null], [null, null, null]];
var metas = [];
function Op(arg, meta) {
	this.n = null;
	this.arg = arg;
	this.vars = novars[meta.siop];
	this.sd = -1;
	this.dep = 0;
	this.si = new Set();
	this.meta = meta;
}
function mkop(op, siop, so, name, ev) {
	var meta = {
		op: op,
		siop: siop,
		so: so,
		name: name,
		eval: ev,
	};
	metas[op] = meta;
	return arg => new Op(arg, meta);
}
var Op0 = mkop(0, 0, 1, "ld", (op, ctx) => {
	ctx.push(op.arg);
	return op.n;
});
var Op1 = mkop(1, 2, 1, "bin", (op, ctx) => {
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
});
var Op2 = mkop(2, 1, 1, "not", (op, ctx) => {
	ctx.push(!ctx.pop());
	return op.n;
});
var Op3 = mkop(3, 1, 0, "pop", (op, ctx) => {
	ctx.pop();
	return op.n;
});
var Op4 = mkop(4, 1, 2, "dup", (op, ctx) => {
	if (ctx.sp) {
		var a = ctx.pop();
		ctx.push(a);
		ctx.push(a);
	}
	return op.n;
});
var Op5 = mkop(5, 2, 2, "swp", (op, ctx) => {
	var a = ctx.pop(), b = ctx.pop();
	ctx.push(a);
	ctx.push(b);
	return op.n;
});
var Op6 = mkop(6, 1, 0, "pr", (op, ctx) => {
	var a = ctx.pop();
	prOut.textContent += (op.arg ? String.fromCharCode(a) : a + " ");
	return op.n;
});
var Op7 = mkop(7, 0, 1, "get", (op, ctx) => {
	ctx.push((op.arg ? ini : inc)());
	return op.n;
});
var Op8 = mkop(8, 2, 1, "rem", (op, ctx) => {
	var y = ctx.pop(), x = ctx.pop();
	if (0 <= x && x < 80 && 0 <= y && y < 25) {
		y=0xce00+((y|x<<5)<<2);
		ctx.push(ctx.mem[y]|ctx.mem[y|1]<<8|ctx.mem[y|2]<<16|ctx.mem[y|3]<<24);
	} else {
		ctx.push(0);
	}
	return op.n;
});
var Op9 = mkop(9, 3, 0, "wem", (op, ctx) => {
	var y = ctx.pop(), x = ctx.pop(), z = ctx.pop();
	if (0 <= x && x < 80 && 0 <= y && y < 25) {
		y=(y|x<<5);
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
});
var Op10 = mkop(10, 0, 0, "jr", (op, ctx) => {
	var a = Math.random()*4&3;
	return a == 3 ? op.n : op.arg[a];
});
var Op11 = mkop(11, 1, 0, "jz", (op, ctx) => {
	return ctx.pop() ? op.n : op.arg;
}); 
var Op12 = mkop(12, 0, 0, "ret", (op, ctx) => {
	return -1;
});
var Op13 = mkop(13, 1, 0, "nop", (op, ctx) => {
	return op.n;
});

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
var ops={64:10,34:9,35:11,38:3,103:4,44:1,126:2,46:0,112:5,124:7,95:8,63:6};
function Tracer(mem){
	this.mem = mem;
	this.pg = [];
	this.node14 = Op12();
}
Tracer.prototype.trace = function(i) {
	function emit(op, arg) {
		pist.length = 0;
		var tail=inst;
		inst=Op13();
		tail.meta=metas[op];
		tail.n=inst;
		tail.arg=arg;
		tail.vars=novars[tail.meta.siop];
		inst.si.add(tail);
		return tail;
	}
	var inst=Op13();
	var head=inst;
	var pist=[]
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
		var i2 = this.mem[0xce00+(i&~3)];
		if (this.mem[0xce01+(i&~3)] || this.mem[0xce02+(i&~3)] || this.mem[0xce03+(i&~3)]) {
			continue;
		}
		else if (48<=i2 && i2<58) { emit(0, i2-48); }
		else if (i2 in mvs) { i=i&~3|mvs[i2]; }
		else if (i2 in bins) { emit(1, bins[i2]); }
		else if (i2 in raw) { emit(raw[i2]); }
		else if (i2 in ops) {
			i2=ops[i2];
			if (i2>8){
				if (i2 == 11) {
					i=mv(i);
				}
				else if (i2 == 9){
					while (true) {
						i=mv(i);
						this.mem[0xf600+(i>>2)]=1;
						var i2 = this.mem[0xce00+(i&~3)]|this.mem[0xce01+(i&~3)]<<8|this.mem[0xce02+(i&~3)]<<16|this.mem[0xce03+(i&~3)]<<24;
						if (i2 == 34) {
							break;
						}
						emit(0, i2);
					}
				} else if (i2 == 10) {
					for (let pi of pist) {
						this.pg[pi]=this.node14;
					}
					if (inst == head) {
						return this.node14;
					}
					for (let si of inst.si) {
						si.n=this.node14;
						this.node14.si.add(si);
					}
					return head;
				}
			} else if (i2<4){
				if (i2<2){
					emit(6, i2);
				}
				else {
					emit(7, i2 == 3);
				}
			} else if (i2>6) {
				var other;
				if (i2 == 7){
					other=3;
					i=i&~3|1;
				} else {
					other=0;
					i=i&~3|2;
				}
				var ifNode = emit(11, this.trace(i&~3|other))
				ifNode.arg.si.add(ifNode)
			} else if (i2 == 5) {
				emit(9, i);
			} else if (i2 == 6) {
				var rngNode = emit(10, [this.trace(i^1), this.trace(i^2), this.trace(i^3)])
				for (let ia of rngNode.arg) {
					ia.si.add(rngNode);
				}
			}
		}
	}
}

function Interpreter(mem, sp){
	this.mem = mem;
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

function bfInterpret(mem, ir, sp) {
	var ctx = new Interpreter(mem, sp);
	while (true) {
		ir = ir.meta.eval(ir, ctx);
		if (typeof ir == "number") return ir;
	}
}

var r4 = () => Math.random()*4&3;
var ini = () => prompt("Number", "")|0;
var inc = () => prompt("Character", "").charCodeAt(0)|0;
var pri = x => prOut.textContent += x + " ";
var prc = x => prOut.textContent += String.fromCharCode(x);
function bfRun(mem, cursor, sp) {
	var code = new Uint8Array(mem.buffer);
	while (true) {
		var tracer = new Tracer(code);
		var ir = tracer.trace(cursor);
		if (false) {
			cursor = bfInterpret(code, ir, sp);
			if (!~cursor) return;
			sp = cursor&65535;
			cursor >>= 16;
		} else {
			return bfCompile(ir, sp).then(m => {
				var f = new WebAssembly.Instance(m, {
				"": {
					pri: pri,
					prc: prc,
					ini: ini,
					inc: inc,
					r4: r4,
					mem: mem,
				}});
				MOD = f; console.log(f, f.exports.mem == mem);
				cursor = f.exports.f();
				console.log(code);
				if (~cursor) {
					sp = cursor&65535;
					cursor >>= 16;
					return bfRun(mem, cursor, sp);
				}
			});
		}
	}
}

function bfCompile(ir, sp) {
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
	varuint(imp, 3);
	pushString(imp, "pri");
	imp.push(0, 0);

	varuint(imp, 0);
	varuint(imp, 3);
	pushString(imp, "prc");
	imp.push(0, 0);

	varuint(imp, 0);
	varuint(imp, 3);
	pushString(imp, "ini");
	imp.push(0, 1);

	varuint(imp, 0);
	varuint(imp, 3);
	pushString(imp, "inc");
	imp.push(0, 1);

	varuint(imp, 0);
	varuint(imp, 2);
	pushString(imp, "r4");
	imp.push(0, 1);


	varuint(imp, 0);
	varuint(imp, 3);
	pushString(imp, "mem");
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

	var exports = [2];

	// entries: repeated export entries as described below

	exports.push(1);
	pushString(exports, "f");
	exports.push(0);
	exports.push(5);

	exports.push(3);
	pushString(exports, "mem");
	exports.push(2);
	exports.push(0);

	varuint(bc, exports.length, 4);
	pushArray(bc, exports);

	bc.push(10); // Codes

	var code = [1];

	var body = [];

	// locals
	varuint(body, 1);
	varuint(body, 2);
	body.push(0x7f);

	body.push(0x41);
	varint(body, sp);
	body.push(0x21, 0);

	var blocks = [];

	function blockpile(blocks, n) {
		var block = [];
		while (true) {
			if (~n.sd) {
				block.push(0x41);
				varint(block, n.sd);
				block.push(0x21, 1);
				blocks.push(block);
				return;
			}
			if (n.si.size > 1) {
				// TODO fallthrough rather than reloop in wasm
				blocks.push(block);
				block.push(0x41);
				varint(block, blocks.length);
				block.push(0x21, 1);
				block = [];
			}
			n.sd = blocks.length;
			if (n.meta.op == 0) {
				block.push(0x20, 0);
				block.push(0x41);
				varint(block, n.arg);
				block.push(0x36, 0, 0);
				block.push(0x20, 0, 0x41, 4, 0x6a, 0x21, 0);
			} else if (n.meta.op == 1) {
				block.push(0x20, 0, 0x04, 0x40);
				switch (n.arg) {
					case "+":
						block.push(0x20, 0, 0x41, 4, 0x47, 0x04, 0x40);
						block.push(0x20, 0, 0x41, 4, 0x6b, 0x21, 0);
						block.push(0x20, 0, 0x41, 4, 0x6b);
						block.push(0x20, 0, 0x28, 0, 0);
						block.push(0x20, 0, 0x41, 4, 0x6b, 0x28, 0, 0);
						block.push(0x6a, 0x36, 0, 0);
						block.push(0x0b);
						break;
					case "-":
						block.push(0x20, 0, 0x41, 4, 0x46, 0x04, 0x40);
						// if sp == 4, *0 = -*0
						block.push(0x41, 0, 0x41, 0, 0x41, 0, 0x28, 0, 0, 0x6b, 0x36, 0, 0);
						block.push(0x05);
						block.push(0x20, 0, 0x41, 4, 0x6b, 0x21, 0);
						block.push(0x20, 0, 0x41, 4, 0x6b);
						block.push(0x20, 0, 0x28, 0, 0);
						block.push(0x20, 0, 0x41, 4, 0x6b, 0x28, 0, 0);
						block.push(0x6b, 0x36, 0, 0);
						block.push(0x0b);
						break;
					case "*":
						block.push(0x20, 0, 0x41, 4, 0x46, 0x04, 0x40);
						// if sp == 4, *0 = 0
						block.push(0x41, 0, 0x41, 0, 0x36, 0, 0);
						block.push(0x05);
						block.push(0x20, 0, 0x41, 4, 0x6b, 0x21, 0);
						block.push(0x20, 0, 0x41, 4, 0x6b);
						block.push(0x20, 0, 0x28, 0, 0);
						block.push(0x20, 0, 0x41, 4, 0x6b, 0x28, 0, 0);
						block.push(0x6c, 0x36, 0, 0);
						block.push(0x0b);
						break;
					case "/":
						block.push(0x20, 0, 0x41, 4, 0x46, 0x04, 0x40);
						// if sp == 4, *0 = 0
						block.push(0x41, 0, 0x41, 0, 0x36, 0, 0);
						block.push(0x05);
						block.push(0x20, 0, 0x41, 4, 0x6b, 0x21, 0);
						block.push(0x20, 0, 0x41, 4, 0x6b);
						block.push(0x20, 0, 0x41, 4, 0x6b, 0x28, 0, 0);
						block.push(0x20, 0, 0x28, 0, 0);
						block.push(0x6d, 0x36, 0, 0);
						block.push(0x0b);
						break;
					case "%":
						block.push(0x20, 0, 0x41, 4, 0x46, 0x04, 0x40);
						// if sp == 4, *0 = 0
						block.push(0x41, 0, 0x41, 0, 0x36, 0, 0);
						block.push(0x05);
						block.push(0x20, 0, 0x41, 4, 0x6b, 0x21, 0);
						block.push(0x20, 0, 0x41, 4, 0x6b);
						block.push(0x20, 0, 0x28, 0, 0);
						block.push(0x20, 0, 0x41, 4, 0x6b, 0x28, 0, 0);
						block.push(0x6f, 0x36, 0, 0);
						block.push(0x0b);
						break;
					case ">":
						block.push(0x20, 0, 0x41, 4, 0x46, 0x04, 0x40);
						// if sp == 4, *0 = 0 > *0
						block.push(0x41, 0, 0x41, 0, 0x41, 0, 0x28, 0, 0, 0x4a, 0x36, 0, 0);
						block.push(0x05);
						block.push(0x20, 0, 0x41, 4, 0x6b, 0x21, 0);
						block.push(0x20, 0, 0x41, 4, 0x6b);
						block.push(0x20, 0, 0x41, 4, 0x6b, 0x28, 0, 0);
						block.push(0x20, 0, 0x28, 0, 0);
						block.push(0x4a, 0x36, 0, 0);
						block.push(0x0b);
						break;
				}
				block.push(0x0b);
			} else if (n.meta.op == 2) {
				block.push(0x20, 0);
				block.push(0x04, 0x40);
				block.push(0x20, 0, 0x41, 4, 0x6b); // s-4
				block.push(0x20, 0, 0x41, 4, 0x6b, 0x28, 0, 0, 0x45); // !*(s-4)
				block.push(0x36, 0, 0);
				block.push(0x05); // else *0=1, sp=4
				block.push(0x41, 0, 0x41, 1, 0x36, 0, 0);
				block.push(0x41, 4, 0x21, 0);
				block.push(0x0b);
			} else if (n.meta.op == 3) {
				block.push(0x20, 0);
				block.push(0x04, 0x40);
				block.push(0x20, 0, 0x41, 4, 0x6b, 0x21, 0);
				block.push(0x0b);
			} else if (n.meta.op == 4) {
				block.push(0x20, 0);
				block.push(0x04, 0x40);
				block.push(0x20, 0);
				block.push(0x20, 0, 0x41, 4, 0x6b, 0x28, 0, 0); // *(s-4)
				block.push(0x36, 0, 0);
				block.push(0x20, 0, 0x41, 4, 0x6a, 0x21, 0);
				block.push(0x0b);
			} else if (n.meta.op == 5) {
				block.push(0x20, 0); // if >0
				block.push(0x04, 0x40);
				block.push(0x20, 0, 0x41, 4, 0x46, 0x04, 0x40);
				// if sp == 4, *4 = 0, sp = 8
				block.push(0x41, 4, 0x41, 0, 0x36, 0, 0);
				block.push(0x20, 0, 0x41, 8, 0x21, 0);
				block.push(0x05); // else swap
				block.push(0x20, 0, 0x41, 8, 0x6b); // sp-8
				block.push(0x20, 0, 0x41, 4, 0x6b, 0x28, 0, 0); // *(sp-4)
				block.push(0x20, 0, 0x41, 4, 0x6b); // sp-4
				block.push(0x20, 0, 0x41, 8, 0x6b, 0x28, 0, 0); // *(sp-8)
				block.push(0x36, 0, 0, 0x36, 0, 0);
				block.push(0x0b, 0x0b);
			} else if (n.meta.op == 6) {
				block.push(0x20, 0); // if >0, pop
				block.push(0x04, 0x7f);
				block.push(0x20, 0, 0x41, 4, 0x6b, 0x22, 0, 0x28, 0, 0); // *(s-=4) 
				block.push(0x05, 0x41, 0); // else 0
				block.push(0x0b);
				block.push(0x10, n.arg?1:0);
			} else if (n.meta.op == 7) {
				block.push(0x20, 0, 0x10, n.arg?2:3, 0x36, 0, 0);
				block.push(0x20, 0, 0x41, 4, 0x6a, 0x21, 0);
			} else if (n.meta.op == 8) {
			} else if (n.meta.op == 9) {
			} else if (n.meta.op == 10) {
				blocks.push(block);
				blockpile(blocks, n.n);
				blockpile(blocks, n.arg[0]);
				blockpile(blocks, n.arg[1]);
				blockpile(blocks, n.arg[2]);
				block.push(0x10, 4, 0x22, 1, 0x04, 0x7f); // tee-if nextblock=r4()
				block.push(0x20, 1, 0x41, 1, 0x46, 0x04, 0x7f, 0x41);
				varint(block, n.arg[0].sd);
				block.push(0x05, 0x20, 1, 0x41, 2, 0x46, 0x04, 0x7f, 0x41);
				varint(block, n.arg[1].sd);
				block.push(0x05, 0x41);
				varint(block, n.arg[2].sd);
				block.push(0x0b, 0x0b);
				block.push(0x05, 0x41);
				varint(block, n.n.sd);
				block.push(0x0b, 0x21, 1);
				return;
			} else if (n.meta.op == 11) {
				blocks.push(block);
				blockpile(blocks, n.n);
				blockpile(blocks, n.arg);
				block.push(0x20, 0, 0x04, 0x7f);
				block.push(0x20, 0, 0x41, 4, 0x6b, 0x22, 0, 0x28, 0, 0); // *(s-=4)
				block.push(0x04, 0x7f, 0x41);
				varint(block, n.n.sd);
				block.push(0x05, 0x41);
				varint(block, n.arg.sd);
				block.push(0x0b);
				block.push(0x05, 0x41);
				varint(block, n.arg.sd);
				block.push(0x0b);
				block.push(0x21, 1);
				return;
			} else if (n.meta.op == 12) {
				block.push(0x41);
				varint(block, -1);
				block.push(0x0f);
				blocks.push(block);
				return;
			}
			n = n.n;
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
	varint(body, blocks.length - 1);
	for (var i=0; i<blocks.length; i++) {
		body.push(i);
	}
	body.push(0x0b);
	for (var i=0; i<blocks.length; i++) {
		pushArray(body, blocks[i]);
		body.push(0xc);
		varuint(body, blocks.length - i);
		body.push(0x0b);
	}
	body.push(0x0b);

	body.push(0);
	body.push(0x0b);

	varuint(code, body.length, 4);

	pushArray(code, body);

	varuint(bc, code.length, 4);
	pushArray(bc, code);

	console.log(bc.length, bc);

	return WebAssembly.compile(new Uint8Array(bc));
}

var btnGo = document.getElementById("btnGo");
var taBoard = document.getElementById("taBoard");
var prOut = document.getElementById("prOut");
btnGo.addEventListener("click", (s, e) => {
	var board = taBoard.value;
	var mem = new WebAssembly.Memory({ initial: 1 });
	// 0000:cdff stack
	// ce00:f5ff source
	// f600:ffff xbits
	var code = new Uint8Array(mem.buffer);
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
	prOut.textContent = "";
	bfRun(mem, 10112, 0);
});
})();
var MOD;
