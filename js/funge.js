"use strict";
function varint (v, value) {
	while (true) {
		let b = value & 127;
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
		let b = value & 127;
		value >>= 7;
		if (value != 0 || padding > 0) {
			b |= 128;
		}
		v.push(b);
		padding--;
	} while (value != 0 || padding > -1);
}

function pushString(v, str) {
	for (let i=0; i<str.length; i++) {
		v.push(str.charCodeAt(i));
	}
}

function pushArray(sink, data) {
	return Array.prototype.push.apply(sink, data);
}

function Op(meta) {
	this.meta = meta;
	this.n = null;
	this.arg = null;
	this.sd = 0;
	this.depo = false;
	this.depi = 0;
	this.si = new Set();
}
function Meta(op, siop, so) {
	this.op = op;
	this.siop = siop;
	this.so = so;
}
const metas = [
	new Meta(0, 0, 1),
	new Meta(1, 2, 1),
	new Meta(2, 1, 1),
	new Meta(3, 1, 0),
	new Meta(4, 1, 2),
	new Meta(5, 2, 2),
	new Meta(6, 1, 0),
	new Meta(7, 0, 1),
	new Meta(8, 2, 1),
	new Meta(9, 3, 0),
	new Meta(10, 0, 0),
	new Meta(11, 1, 0),
	new Meta(12, 0, 0),
	new Meta(13, 1, 0),
], metanop = metas[13];

function mv(i) {
	switch (i&3) {
	case 0:return i>=10112?i-10112:i+128;
	case 1:return i&124?i-4:i+96;
	case 2:return i<128?i+10112:i-128;
	case 3:return (i+4&124)<100?i+4:i-96;
	}
}

const bins={37:0x6f,42:0x6c,43:0x6a,45:0x6b,47:0x6d,96:0x4a};
const raw={33:2,36:3,58:4,92:5,103:8};
const mvs={60:2,62:0,94:1,118:3};
const ops={64:9,34:8,35:10,38:3,44:1,126:2,46:0,112:4,124:6,95:7,63:5};
function Tracer(mem){
	this.mem = mem;
	this.mem32 = new Int32Array(this.mem.buffer);
	this.pg = [];
}
Tracer.prototype.trace = function(i) {
	function emit(op, arg) {
		pist.length = 0;
		const tail=inst;
		inst=new Op(metanop);
		tail.meta=metas[op];
		tail.n=inst;
		tail.arg=arg;
		inst.si.add(tail);
		return tail;
	}
	let inst=new Op(metanop), head=inst;
	const pist = [];
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
		let i2 = this.mem32[0xce00+i>>2];
		if (48<=i2 && i2<58) { emit(0, i2-48); }
		else if (i2 in mvs) { i=i&~3|mvs[i2]; }
		else if (i2 in bins) { emit(1, bins[i2]); }
		else if (i2 in raw) { emit(raw[i2]); }
		else if (i2 in ops) {
			i2=ops[i2];
			switch (i2) {
				case 0:case 1:emit(6, i2);break;
				case 2:case 3:emit(7, i2 == 3);break;
				case 4:emit(9, i<<16);break;
				case 5:
					this.pg[i^1] = this.pg[i^2] = this.pg[i^3] = inst;
					const rngNode = emit(10, [this.trace(i^1), this.trace(i^2), this.trace(i^3)]);
					rngNode.arg[0].si.add(rngNode);
					rngNode.arg[1].si.add(rngNode);
					rngNode.arg[2].si.add(rngNode);
					break;
				case 6:case 7:
					let other;
					if (i2 == 6){
						other=3;
						i=i&~3|1;
					} else {
						other=0;
						i=i&~3|2;
					}
					this.pg[i^1] = this.pg[i^2] = this.pg[i^3] = inst;
					const ifNode = emit(11, this.trace(i&~3|other))
					ifNode.arg.si.add(ifNode)
					break;
				case 8:
					while (true) {
						i=mv(i);
						this.mem[0xf600+(i>>2)]=1;
						i2 = this.mem32[0xce00+i>>2];
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
	this.mem = new Uint8Array(this.imp.m.buffer);
	this.mem32 = new Int32Array(this.imp.m.buffer);
	this.sp = sp;
}
Interpreter.prototype.pop = function() {
	if (!this.sp) return 0;
	this.sp -= 4;
	return this.mem32[this.sp>>2];
}
Interpreter.prototype.push = function(x) {
	this.mem32[this.sp>>2] = x;
	this.sp += 4;
}
Interpreter.prototype.eval = function(op) {
	while (true) {
		let a, b, c;
		switch (op.meta.op) {
			case 0:
				this.push(op.arg);
				break;
			case 1:
				a = this.pop();
				b = this.pop();
				switch (op.arg){
					case 0x6a:b+=a;break;
					case 0x6b:b-=a;break;
					case 0x6c:b*=a;break;
					case 0x6d:b/=a;break;
					case 0x6f:b%=a;break;
					case 0x4a:b=b>a;break;
				}
				this.push(b|0);
				break;
			case 2:
				this.push(!this.pop());
				break;
			case 3:
				this.pop();
				break;
			case 4:
				a = this.pop();
				this.push(a);
				this.push(a);
				break;
			case 5:
				a = this.pop();
				b = this.pop();
				this.push(a);
				this.push(b);
				break;
			case 6:
				c = op.arg&2 ? op.arg>>2 : this.pop();
				if (op.arg&1) this.imp.q(c);
				else this.imp.p(c);
				break;
			case 7:
				this.push((op.arg ? this.imp.i : this.imp.c)());
				break;
			case 8:
				if (op.arg !== null) {
					this.push(this.mem32[0x3380+op.arg]);
				} else {
					let y = this.pop(), x = this.pop();
					if (0 <= x && x < 80 && 0 <= y && y < 25) {
						this.push(this.mem32[0x3380+(y|x<<5)]);
					} else {
						this.push(0);
					}
				}
				break;
			case 9:
				if (op.arg & 0x1000) {
					let z = this.pop();
					const proidx = 0xf600 + (op.arg&0xfff);
					const y = (op.arg&0xfff);
					this.mem32[0x3380+(op.arg&0xfff)]=z;
					if (this.mem[proidx]) {
						this.mem.fill(0, 0xf600);
						return op.arg&0xffff0000|this.sp;
					}
				} else {
					let y = this.pop(), x = this.pop(), z = this.pop();
					if (0 <= x && x < 80 && 0 <= y && y < 25) {
						y|=x<<5;
						const proidx = 0xf600 + y;
						this.mem32[0x3380+y]=z;
						if (this.mem[proidx]) {
							this.mem.fill(0, 0xf600);
							return op.arg&0xffff0000|this.sp;
						}
					}
				}
				break;
			case 10:
				a = this.imp.r4();
				op = a == 3 ? op.n : op.arg[a];
				continue;
			case 11:
				op = this.pop() ? op.n : op.arg;
				continue;
			case 12:
				return -1;
		}
		op = op.n;
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

function peep(n, code) {
	const cst = [];
	while (true) {
		if (n.sd) return;
		n.sd = -1;
		let a, b, c;
		switch (n.meta.op) {
			case 0:
				cst.push(n);
				break;
			case 1:
				a = cst.pop();
				b = cst.pop();
				if (a && b) {
					if (!a.meta.op && !b.meta.op) {
						let t;
						switch (n.arg) {
							case 0x6a:t=b.arg+a.arg;break;
							case 0x6b:t=b.arg-a.arg;break;
							case 0x6c:t=b.arg*a.arg;break;
							case 0x6d:t=a.arg&&b.arg/a.arg;break;
							case 0x6f:t=a.arg&&b.arg%a.arg;break;
							case 0x4a:t=b.arg>a.arg;break;
						}
						n.meta = metas[0];
						n.arg = t;
						a.meta = metanop;
						b.meta = metanop;
					} else {
						a.depo = b.depo = true;
						n.depi = 3;
					}
					cst.push(n);
				} else if (a && b !== undefined) {
					a.depo = true;
					n.depi = 1;
					cst.push(n);
				} else if (b) {
					b.depo = true;
					n.depi = 2;
					cst.push(n);
				} else {
					cst.push(null);
				}
				break;
			case 2:
				a = cst.pop();
				if (a) {
					if (!a.meta.op) {
						a.arg = !a.arg;
						n.meta = metanop;
						cst.push(a);
					} else {
						a.depo = true;
						n.depi = 1;
						cst.push(n);
					}
				} else {
					cst.push(null);
				}
				break;
			case 3:
				a = cst.pop();
				if (a) {
					if (!a.meta.op) {
						a.meta = metanop;
						n.meta = metanop;
					} else {
						a.depo = true;
						n.depi = 1;
					}
				}
				break;
			case 4:
				a = cst.pop();
				if (a) {
					if (!a.meta.op) {
						n.meta = metas[0];
						n.arg = a.arg;
						cst.push(a, n);
					} else {
						a.depo = true;
						n.depi = 1;
						n.arg = [new Op(n.meta), new Op(n.meta)];
						cst.push(n.arg[0], n.arg[1]);
					}
				} else {
					cst.push(null, null);
				}
				break;
			case 5:
				a = cst.pop();
				b = cst.pop();
				if (a && b) {
					if (!a.meta.op && !b.meta.op) {
						let t = a.arg;
						a.arg = b.arg;
						b.arg = t;
						n.meta = metanop;
						cst.push(b, a);
					} else {
						a.depo = b.depo = true;
						n.depi = 3;
						n.arg = [new Op(n.meta), new Op(n.meta)];
						cst.push(n.arg[0], n.arg[1]);
					}
				} else {
					cst.push(null, null);
				}
				break;
			case 6:
				a = cst.pop();
				if (a) {
					if (!a.meta.op) { 
						n.arg |= a.arg<<2 | 2;
						a.meta = metanop;
					} else {
						a.depo = true;
						n.depi = 1;
					}
				}
				break;
			case 7:
				cst.push(n);
				break;
			case 8:
				a = cst.pop();
				b = cst.pop();
				if (a && b) {
					if (!a.meta.op && !b.meta.op) {
						if (a.arg < 0 || a.arg > 24 || b.arg < 0 || b.arg > 79) {
							n.arg = 0;
							n.meta = metas[0];
						} else {
							n.arg = a.arg|b.arg<<5;
						}
						a.meta = metanop;
						b.meta = metanop;
					} else {
						a.depo = b.depo = true;
						n.depi = 3;
					}
					cst.push(n);
				} else {
					cst.push(null);
				}
				break;
			case 9:
				a = cst.pop();
				b = cst.pop();
				c = cst.pop();
				if (a && b) {
					if (!a.meta.op && !b.meta.op) {
						a.meta = metanop;
						b.meta = metanop;
						if (a.arg < 0 || a.arg > 24 || b.arg < 0 || b.arg > 79) {
							n.meta = metas[3];
						} else {
							n.arg |= a.arg | b.arg<<5 | 0x1000;
							if (code[0xf600+(a.arg|b.arg<<5)]) return;
						}
					} else if (c) {
						a.depo = b.depo = c.depo = true;
						n.depi = 7;
					}
				} else {
					cst.length = 0;
				}
				break;
			case 10:
				cst.length = 0;
				peep(n.arg[0], code);
				peep(n.arg[1], code);
				peep(n.arg[2], code);
				break;
			case 11:
				a = cst.pop();
				if (a) {
					if (!a.meta.op) {
						if (!a.arg) n.n = n.arg;
						n.arg.si.delete(n);
						n.arg = null;
						n.meta = metanop;
						a.meta = metanop;
						break;
					} else if (a.meta.op == 2) {
						a.meta = metanop;
						let t = n.n;
						n.n = n.arg;
						n.arg = t;
						n.depi = a.depi;
					} else {
						a.depo = true;
						n.depi = 1;
					}
				}
				cst.length = 0;
				peep(n.arg, code);
				break;
			case 12:
				return;
		}
		if (n.n.si.size > 1) {
			let sis = 0;
			while (sis<cst.length && cst[cst.length - sis - 1]) sis++;
			if (sis && n.n.meta.siop && sis >= n.n.meta.siop) {
				n.n.si.delete(n);
				const nn = new Op(n.n.meta);
				nn.arg = n.n.arg;
				nn.n = n.n.n;
				nn.n.si.add(nn);
				nn.si.add(n);
				n.n = nn;
			} else {
				cst.length = 0;
			}
		}
		n = n.n;
	}
}

function bfRun(imp, cursor, sp) {
	const code = new Uint8Array(imp[""].m.buffer);
	const tracer = new Tracer(code);
	const ir = tracer.trace(cursor);
	peep(ir, code);
	if (false) {
		const ctx = new Interpreter(imp, sp);
		cursor = ctx.eval(ir);
		if (~cursor) {
			code.fill(0, 0xf600);
			return bfRun(imp, cursor>>>16, cursor&65535);
		}
		console.timeEnd("start");
	} else {
		return bfCompile(ir, sp, imp).then(f => {
			cursor = f.instance.exports.f();
			if (~cursor) {
				code.fill(0, 0xf600);
				return bfRun(imp, cursor>>>16, cursor&65535);
			}
			console.timeEnd("start");
		});
	}
}

function bfCompile(ir, sp, imports) {
	const mem = new Uint8Array(imports[""].m.buffer);
	const bc = [0x00, 0x61, 0x73, 0x6d, 0x01, 0x00, 0x00, 0x00];

	bc.push(1); // Types

	const type = [2];

	// i32 -> void
	type.push(0x60, 1, 0x7f, 0);
	// void -> i32
	type.push(0x60, 0, 1, 0x7f);

	varuint(bc, type.length, 4);
	pushArray(bc, type);

	bc.push(2); // Imports

	const imp = [6];
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

	const functions = [1];

	// types: sequence of indices into the type section
	varuint(functions, 1);

	varuint(bc, functions.length, 4);
	pushArray(bc, functions);

	bc.push(7); // Exports

	const exports = [1];

	// entries: repeated export entries as described below

	exports.push(1);
	pushString(exports, "f");
	exports.push(0);
	exports.push(5);

	varuint(bc, exports.length, 4);
	pushArray(bc, exports);

	bc.push(10); // Codes

	const code = [1];

	const body = [];

	// locals
	varuint(body, 1);
	varuint(body, 3);
	body.push(0x7f);

	if (sp) {
		body.push(0x41);
		varint(body, sp);
		body.push(0x21, 0);
	}

	const blocks = [], nobr = new Set();

	const spiller = [0x36, 2, 0, 0x20, 0, 0x41, 4, 0x6a, 0x21, 0];
	function blockpile(blocks, n) {
		if (~n.sd) return;
		let block = [], dep = 0;
		while (true) {
			n.sd = blocks.length;
			switch (n.meta.op) {
				case 0:
					if (n.depo) {
						block.push(0x41);
						varint(block, n.arg);
					} else {
						block.push(0x20, 0, 0x41);
						varint(block, n.arg);
						pushArray(block, spiller);
						dep++;
					}
					break;
				case 1:
					if (n.depi) {
						if (n.depi == 1) {
							block.push(0x21, 1, 0x20, 0, 0x41, 4, 0x6b, 0x22, 0, 0x28, 2, 0, 0x20, 1);
						} else if (n.depi == 2) {
							block.push(0x20, 0, 0x41, 4, 0x6b, 0x22, 0, 0x28, 2, 0);
						}
						block.push(n.arg);
						if (!n.depo) {
							block.push(0x21, 1, 0x20, 0, 0x20, 1);
							pushArray(block, spiller);
							if (n.depi == 3) dep++;
						} else if (n.depi != 3) dep--;
					} else {
						if (dep < 2) {
							if (dep) {
								block.push(0x20, 0);
							} else {
								block.push(0x20, 0, 0x04, 0x40, 0x20, 0);
							}
							block.push(0x41, 4, 0x47, 0x04, 0x40);
						}
						block.push(0x20, 0, 0x41, 8, 0x6b, 0x22, 0, 0x20, 0, 0x28, 2, 0);
						block.push(0x20, 0, 0x41, 4, 0x6a, 0x22, 0, 0x28, 2, 0, n.arg);
						block.push(0x36, 2, 0);
						if (dep < 2) {
							switch (n.arg) {
								case 0x6b: // if sp == 4, *0 = -*0
									block.push(0x05);
									block.push(0x41, 0, 0x41, 0, 0x41, 0, 0x28, 2, 0, 0x6b, 0x36, 2, 0);
									break;
								case 0x6c: // if sp == 4, sp = 0
									block.push(0x05);
									block.push(0x41, 0, 0x21, 0);
									break;
								case 0x6d: // if sp == 4, sp = 0
									block.push(0x05);
									block.push(0x41, 0, 0x21, 0);
									break;
								case 0x6f: // if sp == 4, sp = 0
									block.push(0x05);
									block.push(0x41, 0, 0x21, 0);
									break;
								case 0x4a: // if sp == 4, *0 = 0 > *0
									block.push(0x05);
									block.push(0x41, 0, 0x41, 0, 0x41, 0, 0x28, 2, 0, 0x4a, 0x36, 2, 0);
									break;
							}
							block.push(0x0b);
							if (dep == 0) {
								block.push(0x0b);
							} else if (~"*%/".indexOf(n.arg)) {
								dep = 0;
							}
						} else {
							dep--;
						}
					}
					break;
				case 2:
					if (n.depi) {
						if (!n.depo) block.push(0x20, 0);
						block.push(0x45);
						if (!n.depo) {
							pushArray(block, spiller);
							dep++;
						}
					} else {
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
					}
					break;
				case 3:
					if (n.depi) {
						block.push(0x1a);
					} else {
						if (dep) {
							block.push(0x20, 0, 0x41, 4, 0x6b, 0x21, 0);
							dep--;
						} else {
							block.push(0x20, 0, 0x04, 0x40);
							block.push(0x20, 0, 0x41, 4, 0x6b, 0x21, 0);
							block.push(0x0b);
						}
					}
					break;
				case 4:
					if (n.depi) {
						if (!n.arg[0].depo && !n.arg[1].depo) {
							block.push(0x21, 1, 0x20, 0, 0x20, 0, 0x20, 1, 0x36, 2, 0, 0x20, 1, 0x36, 2, 4, 0x20, 0, 0x41, 8, 0x6a, 0x21, 0);
							dep += 2;
						} else if (n.arg[0].depo && n.arg[1].depo) {
							block.push(0x22, 1, 0x20, 1);
						} else {
							block.push(0x22, 1, 0x20, 0, 0x20, 1, 0x36, 2, 0, 0x20, 0, 0x41, 4, 0x6a, 0x21, 0);
							dep += 1;
						}
					} else {
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
					}
					break;
				case 5:
					if (n.depi) {
						if (!n.arg[0].depo && !n.arg[1].depo) {
							block.push(0x21, 1, 0x20, 0, 0x20, 1, 0x36, 2, 0, 0x21, 1, 0x20, 0, 0x20, 1, 0x36, 2, 4, 0x20, 0, 0x41, 8, 0x6a, 0x21, 0);
							dep += 2;
						} else if (n.arg[0].depo && n.arg[1].depo) {
							block.push(0x21, 1, 0x21, 2, 0x20, 1, 0x20, 2);
						} else if (n.arg[1].depo) {
							block.push(0x21, 1, 0x20, 0, 0x20, 1, 0x36, 2, 0, 0x20, 0, 0x41, 4, 0x6a, 0x21, 0);
							dep++;
						} else {
							block.push(0x21, 2, 0x21, 1, 0x20, 0, 0x20, 1, 0x36, 2, 0, 0x20, 0, 0x41, 4, 0x6a, 0x21, 0, 0x20, 2);
							dep++;
						}
					} else {
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
					}
					break;
				case 6:
					if (!n.depi) {
						if (n.arg & 2) {
							block.push(0x41);
							varint(block, n.arg>>2);
						} else {
							if (dep) {
								block.push(0x20, 0, 0x41, 4, 0x6b, 0x22, 0, 0x28, 2, 0); // *(s-=4) 
								dep--;
							} else {
								block.push(0x20, 0, 0x04, 0x7f); // if >0, pop
								block.push(0x20, 0, 0x41, 4, 0x6b, 0x22, 0, 0x28, 2, 0); // *(s-=4) 
								block.push(0x05, 0x41, 0); // else 0
								block.push(0x0b);
							}
						}
					}
					block.push(0x10, n.arg?1:0);
					break;
				case 7:
					if (n.depo) {
						block.push(0x10, n.arg?2:3);
					} else {
						block.push(0x20, 0, 0x10, n.arg?2:3);
						pushArray(block, spiller);
						dep++;
					}
					break;
				case 8:
					if (n.depi) {
						// TODO bounds checking
						block.push(0x41, 2, 0x74, 0x21, 1, 0x41, 5, 0x74, 0x20, 1, 0x72, 0x28, 2); 
						varint(block, 0xce00);
						if (!n.depo) {
							block.push(0x21, 1, 0x20, 0, 0x20, 1);
							pushArray(block, spiller);
							dep++;
						}
					} else {
						if (n.arg !== null) {
							if (!n.depo) block.push(0x20, 0);
							block.push(0x41);
							varint(block, 0xce00+(n.arg<<2));
							block.push(0x28, 2, 0);
							if (!n.depo) {
								block.push(0x36, 2, 0, 0x20, 0, 0x41, 4, 0x6a, 0x21, 0);
								dep++;
							}
						} else {
							if (dep < 2) {
								if (!dep) {
									block.push(0x20, 0, 0x04, 0x40);
								}
								block.push(0x20, 0, 0x41, 4, 0x46, 0x04, 0x40); // *0 = *(0xce00+(*0<<2))
								if (!n.depo) block.push(0x41, 0);
								block.push(0x41, 0, 0x28, 2, 0, 0x22, 1, 0x41, 0, 0x4d, 0x20, 1, 0x41);
								varint(block, 2560);
								block.push(0x4f, 0x72, 0x04, 0x7f, 0x41, 31, 0x05, 0x20, 1, 0x0b);
								block.push(0x41, 2, 0x74, 0x28, 2);
								varuint(block, 0xce00);
								if (!n.depo) {
									block.push(0x36, 2, 0);
								}
								block.push(0x05); // *(sp-=4) = *(0xce00+((*sp|*(sp-4)<<5)<<2))
							}
							block.push(0x20, 0, 0x41, 4, 0x6b, 0x22, 0, 0x41, 4, 0x6b, 0x20, 0, 0x28, 2, 0,
								0x20, 0, 0x41, 4, 0x6b, 0x28, 2, 0, 0x41, 5, 0x74, 0x72, 0x22, 1, 0x41, 0, 0x4d, 0x20, 1, 0x41);
							varint(block, 2560);
							block.push(0x4f, 0x72, 0x04, 0x7f, 0x41, 31, 0x05, 0x20, 1, 0x0b);
							block.push(0x41, 2, 0x74, 0x28, 2);
							varuint(block, 0xce00);
							if (!n.depo) {
								block.push(0x36, 2, 0);
							}
							if (dep < 2) {
								block.push(0x0b);
								if (!dep) {
									block.push(0x05, 0x41, 0, 0x41);
									varint(block, 0xce00);
									block.push(0x28, 2, 0);
									if (!n.depo) {
										block.push(0x36, 2, 0, 0x41, 4, 0x21, 0);
									}
									block.push(0x0b);
								}
							}
							if (!n.depo) dep = Math.max(dep - 1, 1);
						}
					}
					break;
				case 9:
					if (n.depi) {
						// TODO bounds checking
						block.push(0x41, 2, 0x74, 0x21, 1, 0x41, 5, 0x74, 0x72, 0x21, 1, 0x21, 2, 0x20, 2, 0x20, 1, 0x36, 2);
						varint(block, 0xce00);
					} else {
						if (n.arg & 0x1000) {
							block.push(0x41);
							varint(block, 0xce00+((n.arg&0xfff)<<2));
							if (!dep) {
								block.push(0x20, 0, 0x04, 0x7f);
							}
							block.push(0x20, 0, 0x41, 4, 0x6b, 0x22, 0, 0x28, 2, 0);
							if (!dep) {
								block.push(0x05, 0x41, 0, 0x0b);
							} else dep--;
							block.push(0x36, 2, 0);
							if (mem[0xf600+(n.arg&0xfff)]) {
								block.push(0x41);
								varint(block, n.arg&0xffff0000);
								block.push(0x20, 0, 0x72, 0x0f);
								nobr.add(block);
								return blocks.push(block);
							}
						} else {
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
							varuint(block, n.arg&0xffff0000);
							block.push(0x20, 0, 0x72, 0x0f);
							block.push(0x0b, 0x0b);
						}
					}
					break;
				case 10:
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
						return varuint(block, n.arg[2].sd - n.sd - 1);
					} else {
						block.push(0x41);
						varint(block, n.arg[2].sd);
						block.push(0x41);
						varint(block, n.arg[1].sd);
						block.push(0x41);
						varint(block, n.arg[0].sd);
						block.push(0x41);
						varint(block, n.n.sd);
						return block.push(0x10, 4, 0x22, 1, 0x1b, 0x20, 1, 0x41, 2, 0x46, 0x1b, 0x20, 1, 0x41, 3, 0x46, 0x1b, 0x21, 1);
					}
				case 11:
					blocks.push(block);
					blockpile(blocks, n.n);
					blockpile(blocks, n.arg);
					if (n.depi) {
						block.push(0x21, 1, 0x41);
						varint(block, n.n.sd);
						block.push(0x41);
						varint(block, n.arg.sd);
						return block.push(0x20, 1, 0x1b, 0x21, 1);
					} else {
						if (!dep) {
							block.push(0x20, 0, 0x04, 0x7f);
						}
						block.push(0x41);
						varint(block, n.n.sd);
						block.push(0x41);
						varint(block, n.arg.sd);
						block.push(0x20, 0, 0x41, 4, 0x6b, 0x22, 0, 0x28, 2, 0, 0x1b);
						if (!dep) {
							block.push(0x05, 0x41);
							varint(block, n.arg.sd);
							block.push(0x0b);
						}
						return block.push(0x21, 1);
					}
				case 12:
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
	for (let i=0; i<blocks.length; i++) {
		body.push(0x02, 0x40);
	}
	body.push(0x02, 0x40);
	body.push(0x20, 1);
	body.push(0x0e);
	varuint(body, blocks.length - 1);
	for (let i=0; i<blocks.length; i++) {
		varuint(body, i);
	}
	body.push(0x0b);
	for (let i=0; i<blocks.length; i++) {
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

	return WebAssembly.instantiate(new Uint8Array(bc), imports);
}

exports.r4 = () => Math.random()*4|0;
exports.runSource = function(board, imp){
	// 0000:cdff stack
	// ce00:f5ff source
	// f600:ffff xbits
	console.time("start");
	const code = new Uint8Array(imp[""].m.buffer);
	let i = 0, ch;
	yout:
	for (let y=0; y<25; y++) {
		for (let x=0; x<80; x++) {
			if (i == board.length) {
				for (;x<80; x++) code[0xce00+((y|x<<5)<<2)] = 32;
				for (y++; y<25; y++)
					for (x=0; x<80; x++) code[0xce00+((y|x<<5)<<2)] = 32;
				break yout;
			}
			ch = board.charCodeAt(i++);
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
