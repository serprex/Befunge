use cranelift::prelude::types::{I32, I64, I8};
use cranelift::prelude::*;
use cranelift_codegen::{
	binemit,
	settings::{self, Configurable},
};
use cranelift_jit::{JITBuilder, JITModule};
use cranelift_module::{default_libcall_names, Linkage, Module};
use fxhash::FxHashMap;

use crate::cfg::{BinOp, Dir, Instr, Op};

use crate::util::{print_stack, putnum, rand_nibble, read_int};

pub fn execute(
	cfg: &[Instr],
	progbits: &[u8],
	code: &mut [i32],
	stack: &mut [i32],
	stackidx: &mut isize,
) -> Result<Option<(usize, Dir)>, String> {
	let mut flag_builder = settings::builder();
	flag_builder.set("use_colocated_libcalls", "false").unwrap();
	flag_builder.set("is_pic", "false").unwrap();
	let isa_builder = cranelift_native::builder().expect("unsupported host machine");
	let isa_flags = settings::Flags::new(flag_builder);
	let isa = isa_builder.finish(isa_flags);
	let mut func_ctx = FunctionBuilderContext::new();
	let mut jit_builder = JITBuilder::with_isa(isa, default_libcall_names());
	jit_builder.symbol("pn", putnum as *const u8);
	jit_builder.symbol("gn", read_int as *const u8);
	jit_builder.symbol("r", rand_nibble as *const u8);
	jit_builder.symbol("ps", print_stack as *const u8);

	let mut module = JITModule::new(jit_builder);
	let mut ctx = module.make_context();
	let tptr = module.target_config().pointer_type();

	{
		let mut builder = FunctionBuilder::new(&mut ctx.func, &mut func_ctx);

		let mut aligned = MemFlags::new();
		aligned.set_aligned();

		let mut putcharsig = module.make_signature();
		putcharsig.params.push(AbiParam::new(I32));
		putcharsig.returns.push(AbiParam::new(I32));
		let putcharfn = module
			.declare_function("putchar", Linkage::Import, &putcharsig)
			.unwrap();
		let putchar = module.declare_func_in_func(putcharfn, &mut builder.func);

		let mut getcharsig = module.make_signature();
		getcharsig.returns.push(AbiParam::new(I32));
		let getcharfn = module
			.declare_function("getchar", Linkage::Import, &getcharsig)
			.unwrap();
		let getchar = module.declare_func_in_func(getcharfn, &mut builder.func);

		let mut putnumsig = module.make_signature();
		putnumsig.params.push(AbiParam::new(I32));
		let putnumfn = module
			.declare_function("pn", Linkage::Import, &putnumsig)
			.unwrap();
		let putnum = module.declare_func_in_func(putnumfn, &mut builder.func);

		let mut getnumsig = module.make_signature();
		getnumsig.returns.push(AbiParam::new(I32));
		let getnumfn = module
			.declare_function("gn", Linkage::Import, &getnumsig)
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
		pssig.params.push(AbiParam::new(I64));
		let psfn = module
			.declare_function("ps", Linkage::Import, &pssig)
			.unwrap();
		let ps = module.declare_func_in_func(psfn, &mut builder.func);

		let entry_bb = builder.create_block();
		builder.switch_to_block(entry_bb);

		let stackidxconst = builder.ins().iconst(tptr, (*stackidx * 4) as i64);
		let vsidx = Variable::new(0);
		builder.declare_var(vsidx, I64);
		builder.def_var(vsidx, stackidxconst);

		let clpush = |builder: &mut FunctionBuilder, val: Value| {
			let stidx = builder.use_var(vsidx);
			let newstidx = builder.ins().iadd_imm(stidx, 4);
			let vstack = builder.ins().iconst(tptr, stack.as_ptr() as i64);
			let slotptr = builder.ins().iadd(vstack, newstidx);
			builder.ins().store(aligned, val, slotptr, 0);
			builder.def_var(vsidx, newstidx);
		};

		let clpop = |builder: &mut FunctionBuilder| {
			let bbpop = builder.create_block();
			let zbb = builder.create_block();
			let bb = builder.create_block();
			builder.append_block_param(bb, I32);

			let stidx = builder.use_var(vsidx);
			let zerocc = builder.ins().iconst(I64, 0);
			builder
				.ins()
				.br_icmp(IntCC::SignedLessThan, stidx, zerocc, zbb, &[]);
			builder.ins().jump(bbpop, &[]);
			builder.switch_to_block(bbpop);
			let newstidx = builder.ins().iadd_imm(stidx, -4);
			let vstack = builder.ins().iconst(tptr, stack.as_ptr() as i64);
			let slotptr = builder.ins().iadd(vstack, newstidx);
			builder.def_var(vsidx, newstidx);
			let loadres = builder.ins().load(I32, aligned, slotptr, 4);
			builder.ins().jump(bb, &[loadres]);
			builder.switch_to_block(zbb);
			let zero = builder.ins().iconst(I32, 0);
			builder.ins().jump(bb, &[zero]);
			builder.switch_to_block(bb);
			builder.block_params(bb)[0]
		};

		let mut compstack = vec![0u32];
		let mut bbmap = FxHashMap::default();
		let jumpmapsize = cfg
			.iter()
			.map(|op| match op.op {
				Op::Jz(_) => 2,
				Op::Jr(..) => 4,
				_ => 0,
			})
			.sum();
		let mut jumpmap = Vec::with_capacity(jumpmapsize);
		while let Some(n) = compstack.pop() {
			let op = &cfg[n as usize];
			if op.block {
				if op.si.len() > 1 {
					if let Some(&bbref) = bbmap.get(&n) {
						if !builder.is_filled() {
							builder.ins().jump(bbref, &[]);
						}
						continue;
					}
				}

				let newbb = builder.create_block();
				if !builder.is_filled() {
					builder.ins().jump(newbb, &[]);
				}
				builder.switch_to_block(newbb);
				bbmap.insert(n, newbb);
			}

			if false {
				let vstack = builder.ins().iconst(tptr, stack.as_ptr() as i64);
				let stidx = builder.use_var(vsidx);
				let stidx = builder.ins().sdiv_imm(stidx, 4);
				builder.ins().call(ps, &[vstack, stidx]);
			}

			match op.op {
				Op::Ld(val) => {
					let num = builder.ins().iconst(I32, val as i64);
					clpush(&mut builder, num);
				}
				Op::Bin(bop) => {
					let b = clpop(&mut builder);
					let a = clpop(&mut builder);
					let num = match bop {
						BinOp::Add => builder.ins().iadd(a, b),
						BinOp::Sub => builder.ins().isub(a, b),
						BinOp::Mul => builder.ins().imul(a, b),
						BinOp::Div => builder.ins().sdiv(a, b),
						BinOp::Mod => builder.ins().srem(a, b),
						BinOp::Cmp => {
							let cmp = builder.ins().icmp(IntCC::SignedGreaterThan, a, b);
							builder.ins().bint(I32, cmp)
						}
					};
					clpush(&mut builder, num);
				}
				Op::Not => {
					let a = clpop(&mut builder);
					let eq = builder.ins().icmp_imm(IntCC::Equal, a, 0);
					let eq = builder.ins().bint(I32, eq);
					clpush(&mut builder, eq);
				}
				Op::Pop => {
					clpop(&mut builder);
				}
				Op::Dup => {
					let a = clpop(&mut builder);
					clpush(&mut builder, a);
					clpush(&mut builder, a);
				}
				Op::Swp => {
					let b = clpop(&mut builder);
					let a = clpop(&mut builder);
					clpush(&mut builder, b);
					clpush(&mut builder, a);
				}
				Op::Rch => {
					let inst = builder.ins().call(getchar, &[]);
					let a = builder.inst_results(inst)[0];
					clpush(&mut builder, a);
				}
				Op::Wch => {
					let a = clpop(&mut builder);
					builder.ins().call(putchar, &[a]);
				}
				Op::Rum => {
					let inst = builder.ins().call(getnum, &[]);
					let a = builder.inst_results(inst)[0];
					clpush(&mut builder, a);
				}
				Op::Wum => {
					let a = clpop(&mut builder);
					builder.ins().call(putnum, &[a]);
				}
				Op::Rem => {
					let b = clpop(&mut builder);
					let a = clpop(&mut builder);
					let idxbb = builder.create_block();
					let bb = builder.create_block();
					builder.append_block_param(bb, I32);
					let a5 = builder.ins().ishl_imm(a, 5);
					let ab = builder.ins().bor(a5, b);
					let twofivesixzero = builder.ins().iconst(I32, 2560);
					let zero = builder.ins().iconst(I32, 0);
					builder
						.ins()
						.br_icmp(IntCC::UnsignedLessThan, ab, twofivesixzero, idxbb, &[]);
					builder.ins().jump(bb, &[zero]);
					builder.switch_to_block(idxbb);
					let ab = builder.ins().uextend(I64, ab);
					let ab = builder.ins().imul_imm(ab, 4);
					let vcode = builder.ins().iconst(tptr, code.as_ptr() as i64);
					let vcodeab = builder.ins().iadd(vcode, ab);
					let result = builder.ins().load(I32, aligned, vcodeab, 0);
					builder.ins().jump(bb, &[result]);
					builder.switch_to_block(bb);
					let val = builder.block_params(bb)[0];
					clpush(&mut builder, val);
				}
				Op::Wem(xy, dir) => {
					let b = clpop(&mut builder);
					let a = clpop(&mut builder);
					let c = clpop(&mut builder);
					let bbwrite = builder.create_block();
					let bbexit = builder.create_block();
					let bb = builder.create_block();
					let a80 = builder.ins().icmp_imm(IntCC::UnsignedLessThan, a, 80);
					let b25 = builder.ins().icmp_imm(IntCC::UnsignedLessThan, b, 25);
					let ab8025 = builder.ins().band(a80, b25);
					builder.ins().brz(ab8025, bb, &[]);
					builder.ins().jump(bbwrite, &[]);
					builder.switch_to_block(bbwrite);
					let a5 = builder.ins().ishl_imm(a, 5);
					let ab = builder.ins().bor(a5, b);
					let ab = builder.ins().uextend(I64, ab);
					let ab4 = builder.ins().imul_imm(ab, 4);
					let vcode = builder.ins().iconst(tptr, code.as_ptr() as i64);
					let vcodeab = builder.ins().iadd(vcode, ab4);
					builder.ins().store(aligned, c, vcodeab, 0);
					let vprogbits = builder.ins().iconst(tptr, progbits.as_ptr() as i64);
					let ab3 = builder.ins().ushr_imm(ab, 3);
					let vprogbitsab3 = builder.ins().iadd(vprogbits, ab3);
					let progbitsread = builder.ins().load(I8, aligned, vprogbitsab3, 0);
					let ab7 = builder.ins().band_imm(ab, 7);
					let ab7 = builder.ins().ireduce(I8, ab7);
					let one = builder.ins().iconst(I8, 1);
					let bit = builder.ins().ishl(one, ab7);
					let bitcheck = builder.ins().band(progbitsread, bit);
					builder.ins().brz(bitcheck, bb, &[]);
					builder.ins().jump(bbexit, &[]);
					builder.switch_to_block(bbexit);
					let rstate = builder.ins().iconst(
						I64,
						((xy << 2)
							| match dir {
								Dir::E => 0,
								Dir::N => 1,
								Dir::W => 2,
								Dir::S => 3,
							}) as i64,
					);
					let stackidxconst = builder.ins().iconst(tptr, stackidx as *const isize as i64);
					let stidx = builder.use_var(vsidx);
					let stidx = builder.ins().sdiv_imm(stidx, 4);
					builder.ins().store(aligned, stidx, stackidxconst, 0);
					builder.ins().return_(&[rstate]);
					builder.switch_to_block(bb);
				}
				Op::Jr(r0, r1, r2) => {
					let inst = builder.ins().call(rand, &[]);
					let a = builder.inst_results(inst)[0];
					let zero = builder.ins().iconst(I8, 0);
					let j = builder
						.ins()
						.br_icmp(IntCC::Equal, a, zero, Block::from_u32(0), &[]);
					jumpmap.push((j, r0));
					compstack.push(r0);
					let bb = builder.create_block();
					builder.ins().jump(bb, &[]);
					builder.switch_to_block(bb);
					let one = builder.ins().iconst(I8, 1);
					let j = builder
						.ins()
						.br_icmp(IntCC::Equal, a, one, Block::from_u32(0), &[]);
					jumpmap.push((j, r1));
					compstack.push(r1);
					let bb = builder.create_block();
					builder.ins().jump(bb, &[]);
					builder.switch_to_block(bb);
					let two = builder.ins().iconst(I8, 2);
					let j = builder
						.ins()
						.br_icmp(IntCC::Equal, a, two, Block::from_u32(0), &[]);
					jumpmap.push((j, r2));
					compstack.push(r2);
					let j = builder.ins().jump(Block::from_u32(0), &[]);
					jumpmap.push((j, op.n));
				}
				Op::Jz(rz) => {
					let a = clpop(&mut builder);
					let j = builder.ins().brz(a, Block::from_u32(0), &[]);
					jumpmap.push((j, rz));
					compstack.push(rz);
					let j = builder.ins().jump(Block::from_u32(0), &[]);
					jumpmap.push((j, op.n));
				}
				Op::Ret => {
					let _one = builder.ins().iconst(I64, -1);
					builder.ins().return_(&[_one]);

					let newbb = builder.create_block();
					builder.switch_to_block(newbb);
					continue;
				}
				Op::Hcf => {
					let bb = builder.create_block();
					builder.switch_to_block(bb);
					builder.ins().jump(bb, &[]);
					continue;
				}
				Op::Nop => {}
			}
			compstack.push(op.n);
		}

		if !builder.is_filled() {
			let _one = builder.ins().iconst(I64, -1);
			builder.ins().return_(&[_one]);
		}

		for &(inst, loc) in jumpmap.iter() {
			builder.change_jump_destination(
				inst,
				*bbmap
					.get(&loc)
					.expect("invalid instruction location during jump patching"),
			);
		}

		// TODO we can seal_block eagerly
		builder.seal_all_blocks();
	}

	ctx.func.signature.returns.push(AbiParam::new(tptr));
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
		.define_function(
			id,
			&mut ctx,
			&mut binemit::NullTrapSink {},
			&mut binemit::NullStackMapSink {},
		)
		.map_err(|e| e.to_string())?;
	module.clear_context(&mut ctx);
	module.finalize_definitions();

	let func = module.get_finalized_function(id);
	let result = unsafe { std::mem::transmute::<_, fn() -> usize>(func) }();
	unsafe {
		module.free_memory();
	}
	Ok(if result == usize::max_value() {
		None
	} else {
		Some((
			result >> 2,
			match result & 3 {
				0 => Dir::E,
				1 => Dir::N,
				2 => Dir::W,
				_ => Dir::S,
			},
		))
	})
}
