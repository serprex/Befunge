use std::collections::{HashMap, HashSet};
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
	Ld(u32),
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
	pub var: Vec<u32>,
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
	pgmap: &mut HashMap<(usize, Dir), usize>,
	pastspot: &mut HashSet<(usize, Dir)>,
	inst: Instr,
) -> () {
	let instidx = cfg.len();
	cfg.push(inst);
	if *previnst != usize::max_value() {
		cfg[*previnst].n = instidx as u32;
		*ret = instidx;
	}
	*previnst = instidx;
	for &spot in pastspot.iter() {
		pgmap.insert(spot, instidx);
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
		Dir::N => if (xy & 31) == 0 {
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

pub fn create_cfg(code: &[u8], xy: usize, dir: Dir) -> (Vec<Instr>, Vec<u8>) {
	let mut pgmap: HashMap<(usize, Dir), usize> = HashMap::new();
	let mut cfg = vec![];
	compile(&mut cfg, code, &mut pgmap, xy, dir);
	let mut pg = vec![0; 320];
	for &(idx, dir) in pgmap.keys() {
		pg[idx >> 3] |= 1 << (idx & 7) as u8;
	}
	(cfg, pg)
}

fn compile(
	cfg: &mut Vec<Instr>,
	code: &[u8],
	pgmap: &mut HashMap<(usize, Dir), usize>,
	mut xy: usize,
	mut dir: Dir,
) -> usize {
	let mut tail = usize::max_value();
	let mut head = 0;
	let mut pastspot: HashSet<(usize, Dir)> = HashSet::new();
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
		let ch = util::readu32(code, xy);
		if ch < 127 {
			match ch as u8 {
				b'0'...b'9' => emit(
					cfg,
					&mut tail,
					&mut head,
					pgmap,
					&mut pastspot,
					Instr::new(Op::Ld(ch - 48)),
				),
				b':' => emit(
					cfg,
					&mut tail,
					&mut head,
					pgmap,
					&mut pastspot,
					Instr::new(Op::Dup),
				),
				b'\\' => emit(
					cfg,
					&mut tail,
					&mut head,
					pgmap,
					&mut pastspot,
					Instr::new(Op::Swp),
				),
				b'$' => emit(
					cfg,
					&mut tail,
					&mut head,
					pgmap,
					&mut pastspot,
					Instr::new(Op::Pop),
				),
				b'g' => emit(
					cfg,
					&mut tail,
					&mut head,
					pgmap,
					&mut pastspot,
					Instr::new(Op::Rem),
				),
				b'p' => emit(
					cfg,
					&mut tail,
					&mut head,
					pgmap,
					&mut pastspot,
					Instr::new(Op::Wem(mv(xy, dir), dir)),
				),
				b'&' => emit(
					cfg,
					&mut tail,
					&mut head,
					pgmap,
					&mut pastspot,
					Instr::new(Op::Rum),
				),
				b'.' => emit(
					cfg,
					&mut tail,
					&mut head,
					pgmap,
					&mut pastspot,
					Instr::new(Op::Wum),
				),
				b'~' => emit(
					cfg,
					&mut tail,
					&mut head,
					pgmap,
					&mut pastspot,
					Instr::new(Op::Rch),
				),
				b',' => emit(
					cfg,
					&mut tail,
					&mut head,
					pgmap,
					&mut pastspot,
					Instr::new(Op::Wch),
				),
				b'+' => emit(
					cfg,
					&mut tail,
					&mut head,
					pgmap,
					&mut pastspot,
					Instr::new(Op::Bin(BinOp::Add)),
				),
				b'-' => emit(
					cfg,
					&mut tail,
					&mut head,
					pgmap,
					&mut pastspot,
					Instr::new(Op::Bin(BinOp::Sub)),
				),
				b'*' => emit(
					cfg,
					&mut tail,
					&mut head,
					pgmap,
					&mut pastspot,
					Instr::new(Op::Bin(BinOp::Mul)),
				),
				b'/' => emit(
					cfg,
					&mut tail,
					&mut head,
					pgmap,
					&mut pastspot,
					Instr::new(Op::Bin(BinOp::Div)),
				),
				b'%' => emit(
					cfg,
					&mut tail,
					&mut head,
					pgmap,
					&mut pastspot,
					Instr::new(Op::Bin(BinOp::Mod)),
				),
				b'`' => emit(
					cfg,
					&mut tail,
					&mut head,
					pgmap,
					&mut pastspot,
					Instr::new(Op::Bin(BinOp::Cmp)),
				),
				b'!' => emit(
					cfg,
					&mut tail,
					&mut head,
					pgmap,
					&mut pastspot,
					Instr::new(Op::Not),
				),
				b'>' => dir = Dir::E,
				b'^' => dir = Dir::N,
				b'<' => dir = Dir::W,
				b'v' => dir = Dir::S,
				b'#' => xy = mv(xy, dir),
				b'|' => {
					let d = compile(cfg, code, pgmap, mv(xy, Dir::S), Dir::S);
					emit(
						cfg,
						&mut tail,
						&mut head,
						pgmap,
						&mut pastspot,
						Instr::new(Op::Jz(d as u32)),
					);
					cfg[d].n = tail as u32;
					dir = Dir::N;
				}
				b'_' => {
					let d = compile(cfg, code, pgmap, mv(xy, Dir::W), Dir::W);
					emit(
						cfg,
						&mut tail,
						&mut head,
						pgmap,
						&mut pastspot,
						Instr::new(Op::Jz(d as u32)),
					);
					cfg[d].n = tail as u32;
					dir = Dir::E;
				}
				b'?' => {
					let d1 = compile(cfg, code, pgmap, mv(xy, Dir::E), Dir::E);
					let d2 = compile(cfg, code, pgmap, mv(xy, Dir::N), Dir::N);
					let d3 = compile(cfg, code, pgmap, mv(xy, Dir::W), Dir::W);
					emit(
						cfg,
						&mut tail,
						&mut head,
						pgmap,
						&mut pastspot,
						Instr::new(Op::Jr(d1 as u32, d2 as u32, d3 as u32)),
					);
					cfg[d1].n = tail as u32;
					cfg[d2].n = tail as u32;
					cfg[d3].n = tail as u32;
					dir = Dir::S;
				}
				b'@' => {
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
				_ => (),
			}
		}
		xy = mv(xy, dir);
	}
}
