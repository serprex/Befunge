use cranelift::prelude::*;
use cranelift_codegen::settings::{self, Configurable};
use cranelift_codegen::binemit;
use cranelift_module::{Linkage, Module, default_libcall_names};
use cranelift_jit::{JITBuilder, JITModule};
use fxhash::{FxHashMap};

use crate::cfg::{BinOp, Dir, Instr, Op};

use crate::util::{putnum, rand_nibble, read_int};

pub fn execute(
	cfg: &[Instr],
	progbits: &[u8],
	code: &mut [i32],
	stack: &mut [i32],
	stackidx: &mut isize,
) -> Result<(usize, Dir), String> {
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

	let mut module = JITModule::new(jit_builder);
	let mut ctx = module.make_context();
	let ti32 = types::I32;
	let ti64 = types::I64;
	let tptr = module.target_config().pointer_type();

	{
		let mut builder = FunctionBuilder::new(&mut ctx.func, &mut func_ctx);

		let mut aligned = MemFlags::new();
		aligned.set_aligned();

		let mut putcharsig = module.make_signature();
		putcharsig.params.push(AbiParam::new(ti32));
		putcharsig.returns.push(AbiParam::new(ti32));
		let putcharfn = module.declare_function("putchar", Linkage::Import, &putcharsig).unwrap();
		let putchar = module.declare_func_in_func(putcharfn, &mut builder.func);

		let mut getcharsig = module.make_signature();
		getcharsig.returns.push(AbiParam::new(ti32));
		let getcharfn = module.declare_function("getchar", Linkage::Import, &getcharsig).unwrap();
		let getchar = module.declare_func_in_func(getcharfn, &mut builder.func);

		let mut putnumsig = module.make_signature();
		putnumsig.params.push(AbiParam::new(ti32));
		let putnumfn = module.declare_function("pn", Linkage::Import, &putnumsig).unwrap();
		let putnum = module.declare_func_in_func(putnumfn, &mut builder.func);

		let mut getnumsig = module.make_signature();
		getnumsig.returns.push(AbiParam::new(ti32));
		let getnumfn = module.declare_function("gn", Linkage::Import, &getnumsig).unwrap();
		let getnum = module.declare_func_in_func(getnumfn, &mut builder.func);

		let mut randsig = module.make_signature();
		randsig.returns.push(AbiParam::new(ti32));
		let randfn = module.declare_function("r", Linkage::Import, &randsig).unwrap();
		let rand = module.declare_func_in_func(randfn, &mut builder.func);

		let entry_bb = builder.create_block();
		builder.append_block_params_for_function_params(entry_bb);
		builder.switch_to_block(entry_bb);

		let stackidxconst = builder.ins().iconst(tptr, (*stackidx * 4) as i64);
		let vsidx = Variable::new(0);
		builder.declare_var(vsidx, ti64);
		builder.def_var(vsidx, stackidxconst);

		let ta = Variable::new(1);
		builder.declare_var(ta, ti32);

		let tb = Variable::new(2);
		builder.declare_var(tb, ti32);

		let tc = Variable::new(3);
		builder.declare_var(tc, ti32);

		let clpush = |builder: &mut FunctionBuilder, val: Value| {
			let stidx = builder.use_var(vsidx);
			let four = builder.ins().iconst(ti64, 4);
			let newstidx = builder.ins().iadd(stidx, four);
			let vstack = builder.ins().iconst(tptr, stack.as_ptr() as i64);
			let slotptr = builder.ins().iadd(vstack, newstidx);
			builder.ins().store(aligned, val, slotptr, 0);
			builder.def_var(vsidx, newstidx);
		};

		let clpop = |builder: &mut FunctionBuilder, var: Variable| {
			let bbpop = builder.create_block();
			let zbb = builder.create_block();
			let bb = builder.create_block();
			builder.append_block_param(bb, ti32);

			let stidx = builder.use_var(vsidx);
			let zerocc = builder.ins().iconst(ti64, 0);
			builder.ins().br_icmp(IntCC::SignedLessThan, stidx, zerocc, zbb, &[]);
			builder.ins().fallthrough(bbpop, &[]);
			builder.switch_to_block(bbpop);
			let four = builder.ins().iconst(ti64, 4);
			let newstidx = builder.ins().isub(stidx, four);
			let vstack = builder.ins().iconst(tptr, stack.as_ptr() as i64);
			let slotptr = builder.ins().iadd(vstack, newstidx);
			builder.def_var(vsidx, newstidx);
			let loadres = builder.ins().load(ti32, aligned, slotptr, 4);
			builder.ins().jump(bb, &[loadres]);
			builder.switch_to_block(zbb);
			let zero = builder.ins().iconst(ti32, 0);
			builder.ins().fallthrough(bb, &[zero]);
			builder.switch_to_block(bb);
			builder.def_var(var, builder.block_params(bb)[0]);
		};

		let mut compstack = vec![0u32];
		let mut bbmap = FxHashMap::default();
		let mut jumpmap = Vec::new();
		while let Some(n) = compstack.pop() {
			let op = &cfg[n as usize];
			println!("compiling {} {:?}", n, op);

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
					builder.ins().fallthrough(newbb, &[]);
				}
				builder.switch_to_block(newbb);
				bbmap.insert(n, newbb);
			}

			match op.op {
				Op::Ld(val) => {
					let num = builder.ins().iconst(ti32, val as i64);
					clpush(&mut builder, num);
				}
				Op::Bin(bop) => {
					clpop(&mut builder, ta);
					clpop(&mut builder, tb);
					let a = builder.use_var(ta);
					let b = builder.use_var(tb);
					let num = match bop {
						BinOp::Add => builder.ins().iadd(a, b),
						BinOp::Sub => builder.ins().isub(a, b),
						BinOp::Mul => builder.ins().imul(a, b),
						BinOp::Div => builder.ins().sdiv(a, b),
						BinOp::Mod => builder.ins().srem(a, b),
						BinOp::Cmp => {
							let cmp = builder.ins().icmp(IntCC::SignedGreaterThan, a, b);
							builder.ins().bint(ti32, cmp)
						}
					};
					clpush(&mut builder, num);
				}
				Op::Not => {
					clpop(&mut builder, ta);
					let a = builder.use_var(ta);
					let eq = builder.ins().icmp_imm(IntCC::Equal, a, 0);
					clpush(&mut builder, eq);
				}
				Op::Pop => {
					clpop(&mut builder, ta);
				}
				Op::Dup => {
					clpop(&mut builder, ta);
					let a = builder.use_var(ta);
					clpush(&mut builder, a);
					let a = builder.use_var(ta);
					clpush(&mut builder, a);
				}
				Op::Swp => {
					clpop(&mut builder, ta);
					clpop(&mut builder, tb);
					let b = builder.use_var(tb);
					clpush(&mut builder, b);
					let a = builder.use_var(ta);
					clpush(&mut builder, a);
				}
				Op::Rch => {
					let inst = builder.ins().call(getchar, &[]);
					let a = builder.inst_results(inst)[0];
					clpush(&mut builder, a);
				}
				Op::Wch => {
					clpop(&mut builder, ta);
					let a = builder.use_var(ta);
					builder.ins().call(putchar, &[a]);
				}
				Op::Rum => {
					let inst = builder.ins().call(getnum, &[]);
					let a = builder.inst_results(inst)[0];
					clpush(&mut builder, a);
				}
				Op::Wum => {
					clpop(&mut builder, ta);
					let a = builder.use_var(ta);
					builder.ins().call(putnum, &[a]);
				}
				Op::Rem => {
					clpop(&mut builder, ta);
					clpop(&mut builder, tb);
					let a = builder.use_var(ta);
					let five = builder.ins().iconst(ti32, 5);
					let a5 = builder.ins().ishl(a, five);
					let b = builder.use_var(tb);
					let ab = builder.ins().bor(a5, b);
					let twofivesixzero = builder.ins().iconst(ti32, 2560);
					let idxbb = builder.create_block();
					let bb = builder.create_block();
					builder.append_block_param(bb, ti32);
					let zero = builder.ins().iconst(ti32, 0);
					builder.ins().br_icmp(IntCC::UnsignedLessThan, ab, twofivesixzero, bb, &[zero]);
					builder.ins().fallthrough(idxbb, &[]);
					builder.switch_to_block(idxbb);
					let ab = builder.ins().uextend(ti64, ab);
					let vcode = builder.ins().iconst(tptr, code.as_ptr() as i64);
					let vcodeab = builder.ins().iadd(vcode, ab);
					let result = builder.ins().load(ti32, aligned, vcodeab, 0);
					builder.ins().fallthrough(bb, &[result]);
					builder.switch_to_block(bb);
					let val = builder.block_params(bb)[0];
					clpush(&mut builder, val);
				}
				Op::Wem(xy, dir) => {
					clpop(&mut builder, tb);
					clpop(&mut builder, ta);
					clpop(&mut builder, tc);
					let bbwrite = builder.create_block();
					let bb = builder.create_block();
					let a = builder.use_var(ta);
					let b = builder.use_var(tb);
					let a80 = builder.ins().icmp_imm(IntCC::UnsignedLessThan, a, 80);
					let b25 = builder.ins().icmp_imm(IntCC::UnsignedLessThan, b, 25);
					let ab8025 = builder.ins().band(a80, b25);
					builder.ins().brz(ab8025, bb, &[]);
					builder.ins().fallthrough(bbwrite, &[]);
					builder.switch_to_block(bbwrite);
					let five = builder.ins().iconst(ti32, 5);
					let a5 = builder.ins().ishl(a, five);
					let ab = builder.ins().bor(a5, b);
					let ab = builder.ins().uextend(ti64, ab);
					let vcode = builder.ins().iconst(tptr, code.as_ptr() as i64);
					let vcodeab = builder.ins().iadd(vcode, ab);
					let c = builder.use_var(tc);
					builder.ins().store(aligned, c, vcodeab, 0);
					builder.ins().fallthrough(bb, &[]);
					builder.switch_to_block(bb);
				}
				Op::Jr(r0, r1, r2) => {
					compstack.push(r0);
					compstack.push(r1);
					compstack.push(r2);
				}
				Op::Jz(rz) => {
					clpop(&mut builder, ta);
					let a = builder.use_var(ta);
					let j = builder.ins().brz(a, Block::from_u32(0), &[]);
					jumpmap.push((j, rz));
					compstack.push(rz);
					let j = builder.ins().fallthrough(Block::from_u32(0), &[]);
					jumpmap.push((j, op.n));
				}
				Op::Ret => {
					let _one = builder.ins().iconst(ti64, -1);
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
			let _one = builder.ins().iconst(ti64, -1);
			builder.ins().return_(&[_one]);
		}

		for &(inst, loc) in jumpmap.iter() {
			builder.change_jump_destination(inst, *bbmap.get(&loc).expect("invalid instruction location during jump patching"));
		}

		// TODO we can seal_block eagerly
		builder.seal_all_blocks();
	}

	ctx.func.signature.returns.push(AbiParam::new(tptr));
	println!("{:?}", ctx.func);
	let isa_flags = settings::Flags::new(settings::builder());
	if let Err(errors) = cranelift_codegen::verifier::verify_function(&ctx.func, &isa_flags) {
		return Err(format!("{}", errors));
	}
	let id = module
		.declare_function("f", Linkage::Export, &ctx.func.signature)
		.map_err(|e| e.to_string())?;
	module
		.define_function(id, &mut ctx, &mut binemit::NullTrapSink {}, &mut binemit::NullStackMapSink {})
		.map_err(|e| e.to_string())?;
	module.clear_context(&mut ctx);
	module.finalize_definitions();

	let func = module.get_finalized_function(id);
	let result = unsafe { std::mem::transmute::<_, fn() -> usize>(func) }();
	unsafe { module.free_memory(); }
	Ok(if result == usize::max_value() {
		(result, Dir::E)
	} else {
		(
			result >> 2,
			match result & 3 {
				0 => Dir::E,
				1 => Dir::N,
				2 => Dir::W,
				_ => Dir::S,
			},
		)
	})
}
