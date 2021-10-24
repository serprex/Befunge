use crate::cfg::{BinOp, Instr, Op};
use crate::util::{self, pop, print_stack, push};

pub fn eval(
	cfg: &[Instr],
	progbits: &[u8],
	code: &mut [i32],
	stack: &mut [i32],
	sidx: &mut isize,
) -> u32 {
	let mut n = 0;
	loop {
		let op = &cfg[n as usize];
		if false {
			print_stack(stack.as_ptr(), *sidx);
			println!("{} {:?}", n, op);
		}
		match op.op {
			Op::Ld(val) => push(stack, sidx, val),
			Op::Bin(bop) => {
				let b = pop(stack, sidx);
				let a = pop(stack, sidx);

				push(
					stack,
					sidx,
					match bop {
						BinOp::Add => a.wrapping_add(b),
						BinOp::Sub => a.wrapping_sub(b),
						BinOp::Mul => a.wrapping_mul(b),
						BinOp::Div => {
							if b == 0 {
								0
							} else {
								a / b
							}
						}
						BinOp::Mod => {
							if b == 0 {
								0
							} else {
								a % b
							}
						}
						BinOp::Cmp => (a > b) as i32,
					},
				);
			}
			Op::Not => {
				let a = pop(stack, sidx);
				push(stack, sidx, (a == 0) as i32);
			}
			Op::Pop => {
				pop(stack, sidx);
			}
			Op::Dup => {
				let a = pop(stack, sidx);
				push(stack, sidx, a);
				push(stack, sidx, a);
			}
			Op::Swp => {
				let b = pop(stack, sidx);
				let a = pop(stack, sidx);
				push(stack, sidx, b);
				push(stack, sidx, a);
			}
			Op::Rch => {
				push(stack, sidx, util::read_char());
			}
			Op::Wch => {
				util::putch(pop(stack, sidx));
			}
			Op::Rum => {
				push(stack, sidx, util::read_int());
			}
			Op::Wum => {
				let a = pop(stack, sidx);
				print!("{} ", a);
			}
			Op::Rem(None) => {
				let b = pop(stack, sidx);
				let a = pop(stack, sidx);
				let idx = ((a << 5) | b) as usize;
				let c = if idx < 2560 { code[idx] } else { 0 };
				push(stack, sidx, c);
			}
			Op::Rem(Some(off)) => {
				push(stack, sidx, code[off as usize]);
			}
			Op::Wem(xydir, None) => {
				let b = pop(stack, sidx);
				let a = pop(stack, sidx);
				let c = pop(stack, sidx);
				if a >= 0 && a < 80 && b >= 0 && b < 25 {
					let idx = ((a << 5) | b) as usize;
					code[idx] = c;
					if (progbits[idx >> 3] & (1 << (idx & 7))) != 0 {
						return xydir;
					}
				}
			}
			Op::Wem(xydir, Some(idx)) => {
				let c = pop(stack, sidx);
				let idx = idx as usize;
				code[idx] = c;
				if (progbits[idx >> 3] & (1 << (idx & 7))) != 0 {
					return xydir;
				}
			}
			Op::Jr(ref rs) => {
				let r = util::rand_nibble();
				n = if r < 3 { rs[r as usize] } else { op.n };
				continue;
			}
			Op::Jz(rz) => {
				let a = pop(stack, sidx);
				if a == 0 {
					n = rz;
					continue;
				}
			}
			Op::Ret => {
				return u32::max_value();
			}
			Op::Hcf => loop {},
			Op::Nop => (),
		}
		n = op.n;
	}
}
