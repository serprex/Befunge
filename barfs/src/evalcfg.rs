use cfg::{BinOp, Dir, Instr, Op};
use util::{popu32, pushu32, readu32, writeu32};

pub fn eval(
	cfg: &[Instr],
	progbits: &[u8],
	code: &mut [u8],
	stack: &mut [u8],
	sidx: &mut usize,
) -> (usize, Dir) {
	let mut n = 0;
	loop {
		let op = &cfg[n];
		match op.op {
			Op::Ld(val) => pushu32(stack, sidx, val),
			Op::Bin(bop) => {
				let b = popu32(stack, sidx);
				let a = popu32(stack, sidx);
				pushu32(
					stack,
					sidx,
					match bop {
						BinOp::Add => a + b,
						BinOp::Sub => a - b,
						BinOp::Mul => a * b,
						BinOp::Div => a / b,
						BinOp::Mod => a % b,
						BinOp::Cmp => if a > b {
							1
						} else {
							0
						},
					},
				);
			}
			Op::Not => {
				let a = popu32(stack, sidx);
				pushu32(stack, sidx, if a == 0 { 1 } else { 0 });
			}
			Op::Pop => {
				popu32(stack, sidx);
			}
			Op::Dup => {
				let a = popu32(stack, sidx);
				pushu32(stack, sidx, a);
				pushu32(stack, sidx, a);
			}
			Op::Swp => {
				let b = popu32(stack, sidx);
				let a = popu32(stack, sidx);
				pushu32(stack, sidx, b);
				pushu32(stack, sidx, a);
			}
			Op::Rch => {
				pushu32(stack, sidx, b'a' as u32);
			}
			Op::Wch => {
				let a = popu32(stack, sidx);
				print!(
					"{}",
					std::char::from_u32(a).unwrap_or(std::char::REPLACEMENT_CHARACTER)
				);
			}
			Op::Rum => {
				pushu32(stack, sidx, 0);
			}
			Op::Wum => {
				let a = popu32(stack, sidx);
				print!("{}", a);
			}
			Op::Rem => {
				let b = popu32(stack, sidx);
				let a = popu32(stack, sidx);
				let c = readu32(code, ((a << 5) | b) as usize);
				pushu32(stack, sidx, c);
			}
			Op::Wem(xy, dir) => {
				let c = popu32(stack, sidx);
				let b = popu32(stack, sidx);
				let a = popu32(stack, sidx);
				writeu32(code, ((a << 5) | b) as usize, c);
			}
			Op::Jr(r0, r1, r2) => {}
			Op::Jz(rz) => {
				let a = popu32(stack, sidx);
				if a == 0 {
					n = a as usize;
					continue;
				}
			}
			Op::Ret => {
				return (usize::max_value(), Dir::E);
			}
			Op::Hcf => loop {},
			Op::Nop => (),
		}
		n = op.n as usize;
	}
}
