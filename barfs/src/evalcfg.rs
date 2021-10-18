use crate::cfg::{BinOp, Dir, Instr, Op};
use crate::util::{self, pop, print_stack, push};

pub fn eval(
	cfg: &[Instr],
	progbits: &[u8],
	code: &mut [i32],
	stack: &mut [i32],
	sidx: &mut isize,
) -> Option<(usize, Dir)> {
	let mut n = 0;
	loop {
		let op = &cfg[n];
		if false {
			print_stack(stack.as_ptr(), *sidx);
			println!("{:?}", op);
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
				let a = pop(stack, sidx);
				print!(
					"{}",
					std::char::from_u32(a as u32)
						.unwrap_or(std::char::REPLACEMENT_CHARACTER)
				);
			}
			Op::Rum => {
				push(stack, sidx, util::read_int());
			}
			Op::Wum => {
				let a = pop(stack, sidx);
				print!("{} ", a);
			}
			Op::Rem => {
				let b = pop(stack, sidx);
				let a = pop(stack, sidx);
				let idx = ((a << 5) | b) as usize;
				let c = if idx < 2560 { code[idx] } else { 0 };
				push(stack, sidx, c);
			}
			Op::Wem(xy, dir) => {
				let b = pop(stack, sidx);
				let a = pop(stack, sidx);
				let c = pop(stack, sidx);
				if a >= 0 && a < 80 && b >= 0 && b < 25 {
					let idx = ((a << 5) | b) as usize;
					code[idx] = c;
					if (progbits[idx >> 3] & (1 << (idx & 7))) != 0 {
						return Some((xy, dir));
					}
				}
			}
			Op::Jr(r0, r1, r2) => {
				let r = util::rand_nibble();
				n = match r {
					0 => r0,
					1 => r1,
					2 => r2,
					_ => op.n,
				} as usize;
				continue;
			}
			Op::Jz(rz) => {
				let a = pop(stack, sidx);
				if a == 0 {
					n = rz as usize;
					continue;
				}
			}
			Op::Ret => {
				return None;
			}
			Op::Hcf => loop {},
			Op::Nop => (),
		}
		n = op.n as usize;
	}
}
