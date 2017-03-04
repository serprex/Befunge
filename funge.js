(function(){"use strict";
function signedLEB128 (v, value) {
	while (true) {

		// get 7 least significant bits
		var b = value & 127;
		// left shift value 7 bits
		value >>= 7;

		// sign bit of byte is second high order bit
		if ((value == 0 && ((b & 0x40) == 0)) || ((value == -1 && ((b & 0x40) == 0x40)))) {
			return v.push(b);
		}
		else {
			v.push(b | 128);
		}
	}

	return v;
}


function unsignedLEB128 (v, value, padding) {
	// no padding unless specified
	padding = padding || 0;

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

// A Signed LEB128 variable-length integer, limited to int32 values.
function varint32(v, n) {
	if (n < -2147483648 || n > 2147483647) {
		throw new Error('varint32 is limited to [-2147483648, 2147483647]')
	}

	return signedLEB128(v, n);
}

function varuint1(v, n) {
	if (n < 0 || n > 1) {
		throw new Error('varuint1 is limited to [0, 1]')
	}

	v.push(n);
}

// A LEB128 variable-length integer, limited to the values [0, 127]. varuint7 values may contain leading zeros.
function varuint7(v, n) {
	if (n < 0 || n > 127) {
		throw new Error('varuint7 is limited to [0, 127]');
	}

	v.push(n);
}

// A LEB128 variable-length integer, limited to uint32 values. varuint32 values may contain leading zeros.
function varuint32(v, n, padding) {
	if (n < 0 || n > 0xFFFFFFFF) {
		throw new Error('varuint32 is limited to [0, 4294967295]')
	}

	return unsignedLEB128(v, n, padding);
}

// A Signed LEB128 variable-length integer, limited to int64 values.
function varint64(v, n) {
	if (n < -9223372036854775808 || n > 9223372036854775807) {
		throw new Error('varint64 is limited to [-9223372036854775808, 9223372036854775807]')
	}

	return signedLEB128(v, n);
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
	this.sd = false;
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
var Op0 = mkop(0, 0, 1, "ld", (op, st, mem) => {
	st.push(this.arg);
	return op.n;
});
var Op1 = mkop(1, 2, 1, "bin", (op, st, mem) => {
	var a = st.pop()|0, b = st.pop()|0;
	switch (st.arg){
	case "+":b+=a;break;
	case "-":b-=a;break;
	case "*":b*=a;break;
	case "/":b/=a;break;
	case "%":b%=a;break;
	}
	st.push(b|0);
	return op.n;
});
var Op2 = mkop(2, 1, 1, "not", (op, st, mem) => {
	st.push(!st.pop()|0);
	return op.n;
});
var Op3 = mkop(3, 1, 0, "pop", (op, st, mem) => {
	st.pop();
	return op.n;
});
var Op4 = mkop(4, 1, 2, "dup", (op, st, mem) => {
	if (st.length) {
		st.push(st[st.length-1]);
	}
	return op.n;
});
var Op5 = mkop(5, 2, 2, "swp", (op, st, mem) => {
	st.push(st.pop()|0, st.pop()|0);
	return op.n;
});
var Op6 = mkop(6, 1, 0, "pr", (op, st, mem) => {
	var a = st.pop()|0;
	console.log(this.arg ? String.fromCharCode(a) : a)
	return op.n;
});
var Op7 = mkop(7, 0, 1, "get", (op, st, mem) => {
	st.push((this.arg ? ini : inc)());
	return op.n;
});
var Op8 = mkop(8, 2, 1, "rem", (op, st, mem) => {
	var y = st.pop()|0;
	var x = st.pop()|0;
	if (0 <= x && x <= 80 && 0 <= y && y <= 25) {
		y=0xce00+((y|x<<5)<<2);
		st.push(mem[y]|mem[y|1]<<8|mem[y|2]<<16|mem[y|3]<<24);
	} else {
		st.push(0);
	}
	return op.n;
});
var Op9 = mkop(9, 3, 0, "wem", (op, st, mem) => {
	var y = st.pop()|0;
	var x = st.pop()|0;
	var z = st.pop()|0;
	if (0 <= x && x <= 80 && 0 <= y && y <= 25) {
		y=(y|x<<5);
		var proidx = 0xf600 + y;
		y=0xce00 + (y<<2);
		mem[y]=z&255;
		mem[y|1]=(z>>8)&255;
		mem[y|2]=(z>>16)&255;
		mem[y|3]=(z>>24)&255;
		if (mem[proidx]) {
			return op.arg;
		}
	}
	return op.n;
});
var Op10 = mkop(10, 0, 0, "jr", (op, st, mem) => {
	var a = Math.random()*4&3;
	return a == 3 ? op.n : op.arg[a];
});
var Op11 = mkop(11, 1, 0, "jz", (op, st, mem) => {
	return st.pop() ? op.n : op.arg;
}); 
var Op12 = mkop(12, 0, 0, "ret", (op, st, mem) => {
	return null;
});
var Op13 = mkop(13, 1, 0, "nop", (op, st, mem) => {
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
var raw={33:2,36:3,58:4,92:5,103:10};
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
					pg[i]=pgi;
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
			return head
		}
		this.pg[i]=inst
		pist.push(i)
		this.mem[0xf600+(i>>2)]=1;
		var i2 = this.mem[0xce00+(i&~3)];
		if (this.mem[0xce01+(i&~3)] || this.mem[0xce02+(i&~3)] || this.mem[0xce03+(i&~3)]) {
			continue;
		}
		else if (48<=i2 && i2<58) { emit(0, i2-48); }
		else if (i2 in mvs) { i=i&~3|i2; }
		else if (i2 in bins) { emit(1, bins[i2]); }
		else if (i2 in raw) { emit(raw[i2]); }
		else if (i2 in ops) {
			i2=ops[i2]
			if (i2>8){
				if (i2 == 11) {
					i=mv(i)
				}
				else if (i2 == 9){
					while (true) {
						i=mv(i);
						pro.add(i);
						i2=ps[i];
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
					}
					this.node14.si.add(i);
					return head
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
					mv=i&~3|1;
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

var ini = () => prompt("Number", "")|0;
var inc = () => prompt("Character", "").charCodeAt(0)|0;
var pri = x => console.log(x);
var prc = x => console.log(String.fromCharCode(x));
function bfRun(mem, cursor) {
	var code = new Uint8Array(mem.buffer);
	var tracer = new Tracer(code);
	var ir = tracer.trace(cursor);
	console.log(ir);
	bfCompile(ir).then(m => {
		var f = new WebAssembly.Instance(m, {
		"": {
			pri: pri,
			prc: prc,
			ini: ini,
			inc: inc,
			mem: mem,
		}});
		MOD = f; console.log(f, f.exports.mem == mem);
		var r = f.exports.f();
		if (~r) return bfRun(f.exports.mem, step(r));
	});
}

function bfCompile() {
	var bc = [0x00, 0x61, 0x73, 0x6d, 0x01, 0x00, 0x00, 0x00];

	// ////////////
	// Type section

	bc.push(1);

	// count: number of type entries to follow
	var type = [2];

	// i32 -> void
	type.push(0x60, 1, 0x7f, 0);
	// void -> i32
	type.push(0x60, 0, 1, 0x7f);

	varuint32(bc, type.length, 4);
	pushArray(bc, type);

	// /////////
	// Import

	console.log("imp", bc.length);
	bc.push(2);

	var imp = [5];
	varuint32(imp, 0);
	varuint32(imp, 3);
	pushString(imp, "pri");
	imp.push(0, 0);

	varuint32(imp, 0);
	varuint32(imp, 3);
	pushString(imp, "prc");
	imp.push(0, 0);

	varuint32(imp, 0);
	varuint32(imp, 3);
	pushString(imp, "ini");
	imp.push(0, 1);

	varuint32(imp, 0);
	varuint32(imp, 3);
	pushString(imp, "inc");
	imp.push(0, 1);

	varuint32(imp, 0);
	varuint32(imp, 3);
	pushString(imp, "mem");
	imp.push(2, 0);
	varuint32(imp, 1);

	varuint32(bc, imp.length, 4);
	pushArray(bc, imp);

	// ////////////////
	// Function section

	console.log("func", bc.length);
	bc.push(3);

	// count: count of signature indices to follow
	var functions = [1];

	// types: sequence of indices into the type section
	varuint32(functions, 1);

	varuint32(bc, functions.length, 4);
	pushArray(bc, functions);

	/*// ////////
	// Memory

	console.log("mem", bc.length);
	bc.push(5);

	var mem = [1, 0];
	varuint32(mem, 1);

	varuint32(bc, mem.length, 4);
	pushArray(bc, mem);
*/
	// //////////////
	// Export section

	console.log("ex", bc.length);

	bc.push(7);

	// count: count of export entries to follow
	var exports = [2];

	// entries: repeated export entries as described below

	exports.push(1);
	pushString(exports, "f");
	exports.push(0);
	exports.push(4);

	exports.push(3);
	pushString(exports, "mem");
	exports.push(2);
	exports.push(0);

	varuint32(bc, exports.length, 4);
	pushArray(bc, exports);

	// ////////////
	// Code section

	console.log("code", bc.length);

	bc.push(10);

	// count: count of function bodies to follow
	var code = [1];

	// bodies: sequence of function bodies

	var body = [];

	// local_count: number of local entries
	varuint32(body, 0);

	/*body.push(0x20);
	varuint32(body, 0);
	body.push(0x10);
	varuint32(body, 0);

	body.push(0x20);
	varuint32(body, 1);
	body.push(0x10);
	varuint32(body, 1);

	body.push(0x20);
	varuint32(body, 0);
	body.push(0x20);
	varuint32(body, 1);
	body.push(0x6a);*/
	body.push(0x41);
	varint32(body, -1);
	body.push(0x0b);

	// body_size: size of function body to follow, in bytes
	varuint32(code, body.length, 4);

	// body
	pushArray(code, body);

	varuint32(bc, code.length, 4);
	pushArray(bc, code);

	console.log(bc.length, bc);

	return WebAssembly.compile(new Uint8Array(bc));
}

var btnGo = document.getElementById("btnGo");
var taBoard = document.getElementById("taBoard");
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
			var ch = taBoard.value.charCodeAt(i++);
			if (ch == 10) {
				for (;x<80; x++) code[0xce00+((y|x<<5)<<2)] = 32;
				break;
			}
			code[0xce00+((y|x<<5)<<2)] = ch;
		}
	}
	console.log(mem, code);
	bfRun(mem, 10112);
});
})();
var MOD;
