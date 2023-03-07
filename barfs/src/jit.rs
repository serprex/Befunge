use cranelift::prelude::types::{I64, I32, I8};
use cranelift::prelude::*;
use cranelift_codegen::ir::Inst;
use cranelift_codegen::settings::{self, Configurable};
use cranelift_jit::{JITBuilder, JITModule};
use cranelift_module::{default_libcall_names, Linkage, Module};
use fxhash::FxHashMap;

use crate::cfg::{BinOp, Instr, Op};

use crate::{util, CellInt};

enum JumpEntry {
	J1(Inst, u32),
	J2(Inst, u32, u32),
}

const CELL_SIZE: i64 = std::mem::size_of::<CellInt>() as i64;
const CELL_TYPE: Type = if CELL_SIZE == 4 { I32 } else { I64 };

pub fn execute(
	cfg: &[Instr],
	progbits: &[u8],
	code: &mut [CellInt],
	stack: &mut [CellInt],
	stackidx: &mut isize,
) -> Result<u32, String> {
	let mut flag_builder = settings::builder();
	flag_builder.set("use_colocated_libcalls", "false").unwrap();
	flag_builder.set("is_pic", "false").unwrap();
	let isa_builder = cranelift_native::builder().expect("unsupported host machine");
	let isa_flags = settings::Flags::new(flag_builder);
	let isa = isa_builder
		.finish(isa_flags)
		.expect("unsupported flags for host machine");
	let mut func_ctx = FunctionBuilderContext::new();
	let mut jit_builder = JITBuilder::with_isa(isa, default_libcall_names());
	jit_builder.symbol("pc", util::putch as *const u8);
	jit_builder.symbol("pn", util::putnum as *const u8);
	jit_builder.symbol("gn", util::read_int as *const u8);
	jit_builder.symbol("r", util::rand_nibble as *const u8);
	jit_builder.symbol("ps", util::print_stack as *const u8);

	let mut module = JITModule::new(jit_builder);
	let mut ctx = module.make_context();
	let tptr = module.target_config().pointer_type();

	{
		let mut builder = FunctionBuilder::new(&mut ctx.func, &mut func_ctx);

		let mut aligned = MemFlags::new();
		aligned.set_aligned();

		let mut putsig = module.make_signature();
		putsig.params.push(AbiParam::new(CELL_TYPE));
		let putcharfn = module
			.declare_function("pc", Linkage::Import, &putsig)
			.unwrap();
		let putchar = module.declare_func_in_func(putcharfn, &mut builder.func);

		let mut getsig = module.make_signature();
		getsig.returns.push(AbiParam::new(CELL_TYPE));
		let getcharfn = module
			.declare_function("getchar", Linkage::Import, &getsig)
			.unwrap();
		let getchar = module.declare_func_in_func(getcharfn, &mut builder.func);

		let putnumfn = module
			.declare_function("pn", Linkage::Import, &putsig)
			.unwrap();
		let putnum = module.declare_func_in_func(putnumfn, &mut builder.func);

		let getnumfn = module
			.declare_function("gn", Linkage::Import, &getsig)
			.unwrap();
		let getnum = module.declare_func_in_func(getnumfn, &mut builder.func);

		let mut randsig = module.make_signature();
		randsig.returns.push(AbiParam::new(I8));
		let randfn = module
			.declare_function("r", Linkage::Import, &randsig)
			.unwrap();
		let rand = module.declare_func_in_func(randfn, &mut builder.func);

		let mut pssig = module.make_signature();
		pssig.params.push(AbiParam::new(tptr));
		pssig.params.push(AbiParam::new(tptr));
		let psfn = module
			.declare_function("ps", Linkage::Import, &pssig)
			.unwrap();
		let ps = module.declare_func_in_func(psfn, &mut builder.func);

		let mut block_filled = false;
		let entry_bb = builder.create_block();
		builder.switch_to_block(entry_bb);

		let zero = builder.ins().iconst(CELL_TYPE, 0);
		let zero8 = builder.ins().iconst(I8, 0);
		let one8 = builder.ins().iconst(I8, 1);
		let _one32 = builder.ins().iconst(I32, -1);
		let two8 = builder.ins().iconst(I8, 2);
		let twofivesixzero = builder.ins().iconst(I32, 2560);
		let null = builder.ins().iconst(tptr, 0);
		let stackidxconst = builder.ins().iconst(tptr, (*stackidx * 4) as i64);
		let vstack = builder.ins().iconst(tptr, stack.as_ptr() as i64);
		let vcode = builder.ins().iconst(tptr, code.as_ptr() as i64);
		let vprogbits = builder.ins().iconst(tptr, progbits.as_ptr() as i64);
		let vsidx = Variable::new(0);
		builder.declare_var(vsidx, tptr);
		builder.def_var(vsidx, stackidxconst);

		let mut valmap = FxHashMap::default();

		let clpush = |builder: &mut FunctionBuilder, val: Value| {
			let stidx = builder.use_var(vsidx);
			let newstidx = builder.ins().iadd_imm(stidx, CELL_SIZE);
			let slotptr = builder.ins().iadd(vstack, newstidx);
			builder.ins().store(aligned, val, slotptr, 0);
			builder.def_var(vsidx, newstidx);
		};

		let clpop = |builder: &mut FunctionBuilder, dep: isize| {
			let bb = builder.create_block();
			builder.append_block_param(bb, CELL_TYPE);

			let stidx = builder.use_var(vsidx);
			if dep == 0 {
				let bbpop = builder.create_block();
				let icmp = builder.ins().icmp(IntCC::SignedLessThan, stidx, null);
				builder.ins().brif(icmp, bb, &[zero], bbpop, &[]);
				builder.switch_to_block(bbpop);
				let newstidx = builder.ins().iadd_imm(stidx, -CELL_SIZE);
				let slotptr = builder.ins().iadd(vstack, newstidx);
				builder.def_var(vsidx, newstidx);
				let loadres = builder.ins().load(CELL_TYPE, aligned, slotptr, CELL_SIZE as i32);
				builder.ins().jump(bb, &[loadres]);
				builder.switch_to_block(bb);
				builder.block_params(bb)[0]
			} else {
				let newstidx = builder.ins().iadd_imm(stidx, -CELL_SIZE);
				let slotptr = builder.ins().iadd(vstack, newstidx);
				builder.def_var(vsidx, newstidx);
				builder.ins().load(CELL_TYPE, aligned, slotptr, CELL_SIZE as i32)
			}
		};

		let mut compstack = vec![0u32];
		let mut bbmap = FxHashMap::default();
		let mut jumpmap = Vec::with_capacity(
			cfg.iter()
				.map(|op| match op.op {
					Op::Jz(..) => 1,
					Op::Jr(..) => 3,
					_ => 0,
				})
				.sum(),
		);
		let mut dep = *stackidx;
		while let Some(n) = compstack.pop() {
			let op = &cfg[n as usize];

			macro_rules! push {
				($num:expr, $val:expr) => {
					if (op.depo & 1 << $num) != 0 {
						valmap.insert(n << 2 | $num, $val);
					} else {
						dep += 1;
						clpush(&mut builder, $val);
					}
				};
			}

			macro_rules! pop {
				($idx:expr) => {
					if let Some(&val) = op.depi.get($idx).and_then(|depi| valmap.get(depi)) {
						val
					} else {
						let val = clpop(&mut builder, dep);
						if dep > 0 {
							dep -= 1;
						}
						val
					}
				};
			}

			if op.block {
				if op.si.len() > 1 {
					dep = 0;
					if let Some(&bbref) = bbmap.get(&n) {
						if !block_filled {
							builder.ins().jump(bbref, &[]);
							block_filled = true;
						}
						continue;
					}
				}

				let newbb = builder.create_block();
				if !block_filled {
					builder.ins().jump(newbb, &[]);
				}
				block_filled = false;
				builder.switch_to_block(newbb);
				bbmap.insert(n, newbb);
			}
			debug_assert!(!block_filled);

			if false {
				let stidx = builder.use_var(vsidx);
				let stidx = builder.ins().sdiv_imm(stidx, CELL_SIZE);
				builder.ins().call(ps, &[vstack, stidx]);
			}

			match op.op {
				Op::Ld(val) => {
					let num = if val == 0 { zero } else { builder.ins().iconst(CELL_TYPE, val as i64) };
					push!(0, num);
				}
				Op::Bin(bop) => {
					let b = pop!(0);
					let a = pop!(1);
					let num = match bop {
						BinOp::Add => builder.ins().iadd(a, b),
						BinOp::Sub => builder.ins().isub(a, b),
						BinOp::Mul => builder.ins().imul(a, b),
						BinOp::Div => {
							let divbb = builder.create_block();
							let bb = builder.create_block();
							builder.append_block_param(bb, CELL_TYPE);
							builder.ins().brif(b, divbb, &[], bb, &[zero]);
							builder.switch_to_block(divbb);
							let num = builder.ins().sdiv(a, b);
							builder.ins().jump(bb, &[num]);
							builder.switch_to_block(bb);
							builder.block_params(bb)[0]
						}
						BinOp::Mod => {
							let divbb = builder.create_block();
							let bb = builder.create_block();
							builder.append_block_param(bb, CELL_TYPE);
							builder.ins().brif(b, divbb, &[], bb, &[zero]);
							builder.switch_to_block(divbb);
							let num = builder.ins().srem(a, b);
							builder.ins().jump(bb, &[num]);
							builder.switch_to_block(bb);
							builder.block_params(bb)[0]
						}
						BinOp::Cmp => builder.ins().icmp(IntCC::SignedGreaterThan, a, b),
					};
					push!(0, num);
				}
				Op::Not => {
					let a = pop!(0);
					let eq = builder.ins().icmp_imm(IntCC::Equal, a, 0);
					push!(0, eq);
				}
				Op::Pop => {
					if op.depi.is_empty() {
						if dep == 0 {
							let bb = builder.create_block();
							builder.append_block_param(bb, tptr);
							let stidx = builder.use_var(vsidx);
							let newstidx = builder.ins().iadd_imm(stidx, -CELL_SIZE);
							let cmp = builder.ins().icmp(IntCC::SignedLessThan, stidx, null);
							builder.ins().brif(cmp, bb, &[stidx], bb, &[newstidx]);
							builder.switch_to_block(bb);
							let newstidx = builder.block_params(bb)[0];
							builder.def_var(vsidx, newstidx);
						} else {
							dep -= 1;
							let stidx = builder.use_var(vsidx);
							let newstidx = builder.ins().iadd_imm(stidx, -CELL_SIZE);
							builder.def_var(vsidx, newstidx);
						}
					}
				}
				Op::Dup => {
					let a = pop!(0);
					push!(0, a);
					push!(1, a);
				}
				Op::Swp => {
					let b = pop!(0);
					let a = pop!(1);
					push!(0, b);
					push!(1, a);
				}
				Op::Rch => {
					let inst = builder.ins().call(getchar, &[]);
					let a = builder.inst_results(inst)[0];
					push!(0, a);
				}
				Op::Wch => {
					let a = pop!(0);
					builder.ins().call(putchar, &[a]);
				}
				Op::Rum => {
					let inst = builder.ins().call(getnum, &[]);
					let a = builder.inst_results(inst)[0];
					push!(0, a);
				}
				Op::Wum => {
					let a = pop!(0);
					builder.ins().call(putnum, &[a]);
				}
				Op::Rem(None) => {
					let b = pop!(0);
					let a = pop!(1);
					let idxbb = builder.create_block();
					let bb = builder.create_block();
					builder.append_block_param(bb, CELL_TYPE);
					let a5 = builder.ins().ishl_imm(a, 5);
					let ab = builder.ins().bor(a5, b);
					let cmp = builder
						.ins()
						.icmp(IntCC::UnsignedLessThan, ab, twofivesixzero);
					builder.ins().brif(cmp, idxbb, &[], bb, &[zero]);
					builder.switch_to_block(idxbb);
					let ab = if tptr.bits() > 32 {
						builder.ins().uextend(tptr, ab)
					} else {
						ab
					};
					let ab = builder.ins().imul_imm(ab, CELL_SIZE);
					let vcodeab = builder.ins().iadd(vcode, ab);
					let result = builder.ins().load(CELL_TYPE, aligned, vcodeab, 0);
					builder.ins().jump(bb, &[result]);
					builder.switch_to_block(bb);
					let val = builder.block_params(bb)[0];
					push!(0, val);
				}
				Op::Rem(Some(off)) => {
					let result = builder.ins().load(CELL_TYPE, aligned, vcode, off as i32 * 4);
					push!(0, result);
				}
				Op::Wem(xydir, None) => {
					let b = pop!(0);
					let a = pop!(1);
					let c = pop!(2);
					let bbwrite = builder.create_block();
					let bbexit = builder.create_block();
					let bb = builder.create_block();
					let a80 = builder.ins().icmp_imm(IntCC::UnsignedLessThan, a, 0);
					let b25 = builder.ins().icmp_imm(IntCC::UnsignedLessThan, b, 25);
					let ab8025 = builder.ins().band(a80, b25);
					builder.ins().brif(ab8025, bbwrite, &[], bb, &[]);
					builder.switch_to_block(bbwrite);
					let a5 = builder.ins().ishl_imm(a, 5);
					let ab = builder.ins().bor(a5, b);
					let ab = if tptr.bits() > 32 {
						builder.ins().uextend(tptr, ab)
					} else {
						ab
					};
					let ab4 = builder.ins().imul_imm(ab, CELL_SIZE);
					let vcodeab = builder.ins().iadd(vcode, ab4);
					builder.ins().store(aligned, c, vcodeab, 0);
					let ab3 = builder.ins().ushr_imm(ab, 3);
					let vprogbitsab3 = builder.ins().iadd(vprogbits, ab3);
					let progbitsread = builder.ins().load(I8, aligned, vprogbitsab3, 0);
					let ab7 = builder.ins().band_imm(ab, 7);
					let ab7 = builder.ins().ireduce(I8, ab7);
					let bit = builder.ins().ishl(one8, ab7);
					let bitcheck = builder.ins().band(progbitsread, bit);
					builder.ins().brif(bitcheck, bbexit, &[], bb, &[]);
					builder.switch_to_block(bbexit);
					let stidx = builder.use_var(vsidx);
					let stidx = builder.ins().sdiv_imm(stidx, CELL_SIZE);
					builder.ins().store(aligned, stidx, stackidxconst, 0);
					let rstate = builder.ins().iconst(I32, xydir as i64);
					builder.ins().return_(&[rstate]);
					builder.switch_to_block(bb);
				}
				Op::Wem(xydir, Some(off)) => {
					let c = pop!(0);
					builder.ins().store(aligned, c, vcode, off as i32 * 4);
					if progbits[off as usize >> 3] & 1 << (off & 7) != 0 {
						let stidx = builder.use_var(vsidx);
						let stidx = builder.ins().sdiv_imm(stidx, CELL_SIZE);
						builder.ins().store(aligned, stidx, stackidxconst, 0);
						let rstate = builder.ins().iconst(I32, xydir as i64);
						builder.ins().return_(&[rstate]);
						block_filled = true;
						continue;
					}
				}
				Op::Jr(ref rs) => {
					let [r0, r1, r2] = **rs;
					let inst = builder.ins().call(rand, &[]);
					let a = builder.inst_results(inst)[0];
					let cmp = builder.ins().icmp(IntCC::Equal, a, zero8);
					let bb = builder.create_block();
					let j = builder.ins().brif(cmp, Block::from_u32(0), &[], bb, &[]);
					jumpmap.push(JumpEntry::J1(j, r0));
					compstack.push(r0);
					builder.switch_to_block(bb);
					let cmp = builder.ins().icmp(IntCC::Equal, a, one8);
					let bb = builder.create_block();
					let j = builder.ins().brif(cmp, Block::from_u32(0), &[], bb, &[]);
					jumpmap.push(JumpEntry::J1(j, r1));
					compstack.push(r1);
					builder.switch_to_block(bb);
					let cmp = builder.ins().icmp(IntCC::Equal, a, two8);
					let j =
						builder
							.ins()
							.brif(cmp, Block::from_u32(1), &[], Block::from_u32(0), &[]);
					jumpmap.push(JumpEntry::J2(j, r2, op.n));
					compstack.push(r2);
					block_filled = true;
				}
				Op::Jz(rz) => {
					let a = pop!(0);
					let j = builder
						.ins()
						.brif(a, Block::from_u32(1), &[], Block::from_u32(0), &[]);
					jumpmap.push(JumpEntry::J2(j, op.n, rz));
					compstack.push(rz);
					block_filled = true;
				}
				Op::Ret => {
					builder.ins().return_(&[_one32]);
					block_filled = true;
					continue;
				}
				Op::Hcf => {
					let bb = builder.current_block().unwrap();
					builder.ins().jump(bb, &[]);
					block_filled = true;
					continue;
				}
				Op::Nop => {}
			}
			compstack.push(op.n);
		}

		if !block_filled {
			builder.ins().return_(&[_one32]);
		}

		for jump in jumpmap.iter() {
			match *jump {
				JumpEntry::J1(inst, loc) => builder.change_jump_destination(
					inst,
					Block::from_u32(0),
					*bbmap.get(&loc).unwrap(),
				),
				JumpEntry::J2(inst, loctrue, locfalse) => {
					builder.change_jump_destination(
						inst,
						Block::from_u32(1),
						*bbmap.get(&loctrue).unwrap(),
					);
					builder.change_jump_destination(
						inst,
						Block::from_u32(0),
						*bbmap.get(&locfalse).unwrap(),
					)
				}
			}
		}

		builder.seal_all_blocks();
	}

	ctx.func.signature.returns.push(AbiParam::new(I32));
	if false {
		println!("{:?}", ctx.func);
		let isa_flags = settings::Flags::new(settings::builder());
		cranelift_codegen::verifier::verify_function(&ctx.func, &isa_flags)
			.map_err(|e| e.to_string())?;
	}
	let id = module
		.declare_function("f", Linkage::Export, &ctx.func.signature)
		.map_err(|e| e.to_string())?;
	module
		.define_function(id, &mut ctx)
		.map_err(|e| e.to_string())?;
	module.clear_context(&mut ctx);
	module.finalize_definitions().map_err(|e| e.to_string())?;

	let func = module.get_finalized_function(id);
	let result = unsafe { std::mem::transmute::<_, fn() -> u32>(func) }();
	unsafe {
		module.free_memory();
	}
	Ok(result)
}
