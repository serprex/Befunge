use fxhash::{FxHashMap, FxHashSet};

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

impl From<Dir> for u32 {
	fn from(dir: Dir) -> u32 {
		match dir {
			Dir::E => 0,
			Dir::N => 1,
			Dir::W => 2,
			Dir::S => 3,
		}
	}
}

impl Into<Dir> for u32 {
	fn into(self) -> Dir {
		match self & 3 {
			0 => Dir::E,
			1 => Dir::N,
			2 => Dir::W,
			_ => Dir::S,
		}
	}
}

#[derive(Clone, Debug)]
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
	Wem(u32),
	Jr(Box<[u32; 3]>),
	Jz(u32),
	Ret,
	Hcf,
	Nop,
}

impl Op {
	pub fn depth(&self) -> (u8, u8) {
		match self {
			Op::Ld(..) => (0, 1),
			Op::Bin(..) => (2, 1),
			Op::Not => (1, 1),
			Op::Pop => (1, 0),
			Op::Dup => (1, 2),
			Op::Swp => (2, 2),
			Op::Rch => (0, 1),
			Op::Wch => (1, 0),
			Op::Rum => (0, 1),
			Op::Wum => (1, 0),
			Op::Rem => (2, 1),
			Op::Wem(..) => (3, 0),
			Op::Jr(..) => (0, 0),
			Op::Jz(..) => (1, 0),
			Op::Ret => (0, 0),
			Op::Hcf => (0, 0),
			Op::Nop => (0, 0),
		}
	}

	pub fn io(&self) -> bool {
		matches!(self, Op::Rch | Op::Wch | Op::Rum | Op::Wum | Op::Wem(..) | Op::Jz(..) | Op::Jr(..))
	}
}

#[derive(Clone, Debug)]
pub struct Instr {
	pub op: Op,
	pub n: u32,
	pub si: Vec<u32>,
	pub depi: Vec<(u32, u8)>,
	pub depo: u8,
	pub block: bool,
}

impl Instr {
	pub fn new(op: Op) -> Self {
		let block = matches!(op, Op::Hcf);
		Self {
			op,
			n: 0,
			si: Vec::new(),
			depi: Vec::new(),
			depo: 0,
			block,
		}
	}

	pub fn si_add(&mut self, n: u32, force_block: bool) -> () {
		if !self.si.contains(&n) {
			self.si.push(n);
		}

		if force_block || self.si.len() > 1 {
			self.block = true;
		}
	}
}

fn emit(
	cfg: &mut Vec<Instr>,
	previnst: &mut u32,
	ret: &mut u32,
	pgmap: &mut FxHashMap<u32, u32>,
	pastspot: &mut FxHashSet<u32>,
	mut inst: Instr,
) -> () {
	let instidx = cfg.len() as u32;
	if *previnst != u32::max_value() {
		let mut prevop = &mut cfg[*previnst as usize];
		prevop.n = instidx;
		if matches!(prevop.op, Op::Jz(..) | Op::Jr(..)) {
			inst.block = true;
		}
		cfg[*previnst as usize].n = instidx as u32;
		inst.si_add(*previnst as u32, false);
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

fn mv(xy: u32, dir: Dir) -> u32 {
	match dir {
		Dir::E => {
			if xy >= 2528 {
				xy - 2528
			} else {
				xy + 32
			}
		}
		Dir::N => {
			if (xy & 31) != 0 {
				xy - 1
			} else {
				xy + 24
			}
		}
		Dir::W => {
			if xy < 32 {
				xy + 2528
			} else {
				xy - 32
			}
		}
		Dir::S => {
			if (xy + 1 & 31) < 25 {
				xy + 1
			} else {
				xy - 24
			}
		}
	}
}

pub fn create_cfg(code: &[i32], pg: &mut [u8; 320], xy: u32, dir: Dir) -> Vec<Instr> {
	let mut cfg = vec![];
	{
		let mut pgmap: FxHashMap<u32, u32> = FxHashMap::default();
		compile(&mut cfg, code, &mut pgmap, xy, dir);
		for &xydir in pgmap.keys() {
			let idx = xydir >> 2;
			pg[idx as usize >> 3] |= 1u8 << (idx as usize & 7);
		}
	}
	peep(&mut cfg);
	cfg
}

fn compile(
	cfg: &mut Vec<Instr>,
	code: &[i32],
	pgmap: &mut FxHashMap<u32, u32>,
	mut xy: u32,
	mut dir: Dir,
) -> u32 {
	let mut tail = u32::max_value();
	let mut head = 0;
	let mut pastspot: FxHashSet<u32> = FxHashSet::default();
	loop {
		let xydir = (xy << 2) | u32::from(dir);
		if !pastspot.insert(xydir) {
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
		if let Some(&n) = pgmap.get(&xydir) {
			if tail != u32::max_value() {
				cfg[tail as usize].n = n;
				cfg[n as usize].si_add(tail, false);
			} else {
				head = n;
			}
			for &spot in pastspot.iter() {
				pgmap.insert(spot, n);
			}
			return head;
		}
		let ch = code[xy as usize];
		match ch {
			48..=57 => emit(
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
				Instr::new(Op::Wem(mv(xy, dir) << 2 | u32::from(dir))),
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
				pgmap.insert(xydir ^ 1, tail);
				pgmap.insert(xydir ^ 2, tail);
				pgmap.insert(xydir ^ 3, tail);
				let d = compile(cfg, code, pgmap, mv(xy, newdir.0), newdir.0);
				cfg[tail as usize].op = Op::Jz(d as u32);
				cfg[d as usize].si_add(tail as u32, true);
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
				pgmap.insert(xydir ^ 1, tail);
				pgmap.insert(xydir ^ 2, tail);
				pgmap.insert(xydir ^ 3, tail);
				let d1 = compile(cfg, code, pgmap, mv(xy, Dir::E), Dir::E);
				let d2 = compile(cfg, code, pgmap, mv(xy, Dir::N), Dir::N);
				let d3 = compile(cfg, code, pgmap, mv(xy, Dir::W), Dir::W);
				cfg[tail as usize].op = Op::Jr(Box::new([d1, d2, d3]));
				cfg[d1 as usize].si_add(tail, true);
				cfg[d2 as usize].si_add(tail, true);
				cfg[d3 as usize].si_add(tail, true);
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
				let qch = code[xy as usize];
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

fn peep(cfg: &mut Vec<Instr>) {
	let mut cst = Vec::new();
	let mut idx = 0;
	while (idx as usize) < cfg.len() {
		let (isblock, isio, (si, so)) = {
			let op = &mut cfg[idx as usize];
			(op.block, op.op.io(), op.op.depth())
		};
		if isblock {
			cst.clear();
		} else {
			for _ in 0..si {
				if let Some((c, cout)) = cst.pop() {
					cfg[c as usize].depo |= 1u8 << cout;
					cfg[idx as usize].depi.push((c, cout));
				} else {
					break;
				}
			}
			if isio {
				cst.clear();
			}
		}
		for outidx in 0..so {
			cst.push((idx, outidx));
		}
		idx += 1;
	}
}
