use fnv::{FnvHashMap, FnvHashSet};
use util;

#[derive(Copy, Clone, Debug)]
pub enum BinOp {
	Add,
	Sub,
	Mul,
	Div,
	Mod,
	Cmp,
}

#[derive(Copy, Clone, Eq, PartialEq, Hash, Debug)]
pub enum Dir {
	E,
	N,
	W,
	S,
}

#[derive(Copy, Clone, Debug)]
pub enum Op {
	Ld(i32),
	Bin(BinOp),
	Not,
	Pop,
	Dup,
	Swp,
	Rch,
	Wch,
	Rum,
	Wum,
	Rem,
	Wem(usize, Dir),
	Jr(u32, u32, u32),
	Jz(u32),
	Ret,
	Hcf,
	Nop,
}

#[derive(Debug)]
pub struct Instr {
	pub op: Op,
	pub n: u32,
	pub var: Vec<i32>,
	pub si: Vec<u32>,
	pub dep: u32,
	pub sd: bool,
}

impl Instr {
	pub fn new(op: Op) -> Self {
		Self {
			op: op,
			n: 0,
			var: Vec::new(),
			si: Vec::new(),
			dep: 0,
			sd: false,
		}
	}
	pub fn si_add(&mut self, n: u32) -> () {
		if !self.si.contains(&n) {
			self.si.push(n);
		}
	}

	pub fn si_has(&self, n: u32) -> bool {
		self.si.contains(&n)
	}
}

fn emit(
	cfg: &mut Vec<Instr>,
	previnst: &mut usize,
	ret: &mut usize,
	pgmap: &mut FnvHashMap<(usize, Dir), u32>,
	pastspot: &mut FnvHashSet<(usize, Dir)>,
	mut inst: Instr,
) -> () {
	let instidx = cfg.len();
	if *previnst != usize::max_value() {
		cfg[*previnst].n = instidx as u32;
		inst.si_add(*previnst as u32);
	} else {
		*ret = instidx;
	}
	cfg.push(inst);
	*previnst = instidx;
	for &spot in pastspot.iter() {
		pgmap.insert(spot, instidx as u32);
	}
	pastspot.clear();
}

fn mv(xy: usize, dir: Dir) -> usize {
	match dir {
		Dir::E => if xy >= 2528 {
			xy - 2528
		} else {
			xy + 32
		},
		Dir::N => if (xy & 31) != 0 {
			xy - 1
		} else {
			xy + 24
		},
		Dir::W => if xy < 32 {
			xy + 2528
		} else {
			xy - 32
		},
		Dir::S => if (xy + 1 & 31) < 25 {
			xy + 1
		} else {
			xy - 24
		},
	}
}

pub fn create_cfg(code: &[i32], xy: usize, dir: Dir) -> (Vec<Instr>, Vec<u8>) {
	let mut pgmap: FnvHashMap<(usize, Dir), u32> = FnvHashMap::default();
	let mut cfg = vec![];
	compile(&mut cfg, code, &mut pgmap, xy, dir);
	let mut pg = vec![0; 320];
	for &(idx, _dir) in pgmap.keys() {
		pg[idx as usize >> 3] |= 1 << (idx as usize & 7) as u8;
	}
	(cfg, pg)
}

fn compile(
	cfg: &mut Vec<Instr>,
	code: &[i32],
	pgmap: &mut FnvHashMap<(usize, Dir), u32>,
	mut xy: usize,
	mut dir: Dir,
) -> usize {
	let mut tail = usize::max_value();
	let mut head = 0;
	let mut pastspot: FnvHashSet<(usize, Dir)> = FnvHashSet::default();
	loop {
		if !pastspot.insert((xy, dir)) {
			emit(
				cfg,
				&mut tail,
				&mut head,
				pgmap,
				&mut pastspot,
				Instr::new(Op::Hcf),
			);
			return head;
		}
		if let Some(&n) = pgmap.get(&(xy, dir)) {
			if tail != usize::max_value() {
				cfg[tail].n = n;
				cfg[n as usize].si_add(tail as u32);
			} else {
				head = n as usize;
			}
			tail = n as usize;
			for &spot in pastspot.iter() {
				pgmap.insert(spot, n);
			}
			return head;
		}
		let ch = code[xy];
		match ch {
			48...57 => emit(
				cfg,
				&mut tail,
				&mut head,
				pgmap,
				&mut pastspot,
				Instr::new(Op::Ld(ch - 48)),
			),
			58 => emit(
				cfg,
				&mut tail,
				&mut head,
				pgmap,
				&mut pastspot,
				Instr::new(Op::Dup),
			),
			92 => emit(
				cfg,
				&mut tail,
				&mut head,
				pgmap,
				&mut pastspot,
				Instr::new(Op::Swp),
			),
			36 => emit(
				cfg,
				&mut tail,
				&mut head,
				pgmap,
				&mut pastspot,
				Instr::new(Op::Pop),
			),
			103 => emit(
				cfg,
				&mut tail,
				&mut head,
				pgmap,
				&mut pastspot,
				Instr::new(Op::Rem),
			),
			112 => emit(
				cfg,
				&mut tail,
				&mut head,
				pgmap,
				&mut pastspot,
				Instr::new(Op::Wem(mv(xy, dir), dir)),
			),
			38 => emit(
				cfg,
				&mut tail,
				&mut head,
				pgmap,
				&mut pastspot,
				Instr::new(Op::Rum),
			),
			46 => emit(
				cfg,
				&mut tail,
				&mut head,
				pgmap,
				&mut pastspot,
				Instr::new(Op::Wum),
			),
			126 => emit(
				cfg,
				&mut tail,
				&mut head,
				pgmap,
				&mut pastspot,
				Instr::new(Op::Rch),
			),
			44 => emit(
				cfg,
				&mut tail,
				&mut head,
				pgmap,
				&mut pastspot,
				Instr::new(Op::Wch),
			),
			43 => emit(
				cfg,
				&mut tail,
				&mut head,
				pgmap,
				&mut pastspot,
				Instr::new(Op::Bin(BinOp::Add)),
			),
			45 => emit(
				cfg,
				&mut tail,
				&mut head,
				pgmap,
				&mut pastspot,
				Instr::new(Op::Bin(BinOp::Sub)),
			),
			42 => emit(
				cfg,
				&mut tail,
				&mut head,
				pgmap,
				&mut pastspot,
				Instr::new(Op::Bin(BinOp::Mul)),
			),
			47 => emit(
				cfg,
				&mut tail,
				&mut head,
				pgmap,
				&mut pastspot,
				Instr::new(Op::Bin(BinOp::Div)),
			),
			37 => emit(
				cfg,
				&mut tail,
				&mut head,
				pgmap,
				&mut pastspot,
				Instr::new(Op::Bin(BinOp::Mod)),
			),
			96 => emit(
				cfg,
				&mut tail,
				&mut head,
				pgmap,
				&mut pastspot,
				Instr::new(Op::Bin(BinOp::Cmp)),
			),
			33 => emit(
				cfg,
				&mut tail,
				&mut head,
				pgmap,
				&mut pastspot,
				Instr::new(Op::Not),
			),
			62 => dir = Dir::E,
			94 => dir = Dir::N,
			60 => dir = Dir::W,
			118 => dir = Dir::S,
			35 => xy = mv(xy, dir),
			95 | 124 => {
				let newdir = if ch == 95 {
					(Dir::E, Dir::W)
				} else {
					(Dir::S, Dir::N)
				};
				emit(
					cfg,
					&mut tail,
					&mut head,
					pgmap,
					&mut pastspot,
					Instr::new(Op::Nop),
				);
				let d = compile(cfg, code, pgmap, mv(xy, newdir.0), newdir.0);
				cfg[tail].op = Op::Jz(d as u32);
				cfg[d].si_add(tail as u32);
				dir = newdir.1;
			}
			63 => {
				emit(
					cfg,
					&mut tail,
					&mut head,
					pgmap,
					&mut pastspot,
					Instr::new(Op::Nop),
				);
				let d1 = compile(cfg, code, pgmap, mv(xy, Dir::E), Dir::E);
				let d2 = compile(cfg, code, pgmap, mv(xy, Dir::N), Dir::N);
				let d3 = compile(cfg, code, pgmap, mv(xy, Dir::W), Dir::W);
				cfg[tail].op = Op::Jr(d1 as u32, d2 as u32, d3 as u32);
				cfg[d1].si_add(tail as u32);
				cfg[d2].si_add(tail as u32);
				cfg[d3].si_add(tail as u32);
				dir = Dir::S;
			}
			64 => {
				emit(
					cfg,
					&mut tail,
					&mut head,
					pgmap,
					&mut pastspot,
					Instr::new(Op::Ret),
				);
				return head;
			}
			34 => loop {
				xy = mv(xy, dir);
				let qch = code[xy];
				if qch == b'"' as i32 {
					break;
				}
				emit(
					cfg,
					&mut tail,
					&mut head,
					pgmap,
					&mut pastspot,
					Instr::new(Op::Ld(qch)),
				);
			},
			_ => (),
		}
		xy = mv(xy, dir);
	}
}
