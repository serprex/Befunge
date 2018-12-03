use std::slice;

use cranelift::prelude::*;
use cranelift_module::{Linkage, Module};
use cranelift_simplejit::{SimpleJITBackend, SimpleJITBuilder};

use cfg::{BinOp, Dir, Instr, Op};

pub struct Jit {
	builder_ctx: FunctionBuilderContext,
	ctx: codegen::Context,
	module: Module<SimpleJITBackend>,
}

impl Jit {
	pub fn new() -> Self {
		let builder = SimpleJITBuilder::new();
		let module = Module::new(builder);
		Self {
			builder_ctx: FunctionBuilderContext::new(),
			ctx: module.make_context(),
			module,
		}
	}

	pub fn compile(
		&mut self,
		cfg: &[Instr],
		progbits: &[u8],
		code: &mut [i32],
		stack: &mut [i32],
		stackidx: &mut usize,
	) -> Result<(usize, Dir), String> {
		let ti32 = codegen::ir::types::I32;
		let tptr = self.module.target_config().pointer_type();

		{
			let mut builder = FunctionBuilder::new(&mut self.ctx.func, &mut self.builder_ctx);

			let mut aligned = MemFlags::new();
			aligned.set_aligned();

			let zero = builder.ins().iconst(ti32, 0);
			let one = builder.ins().iconst(ti32, 1);
			let four = builder.ins().iconst(ti32, 4);
			let _one = builder.ins().iconst(ti32, -1);
			let vstackidx = builder.ins().iconst(tptr, stackidx as *mut usize as i64);
			let vstack = builder.ins().iconst(tptr, stack.as_ptr() as i64);
			let vcode = builder.ins().iconst(tptr, code.as_ptr() as i64);

			let entry_ebb = builder.create_ebb();
			builder.append_ebb_params_for_function_params(entry_ebb);
			builder.switch_to_block(entry_ebb);
			builder.seal_block(entry_ebb);

			let mut compstack = vec![0u32];
			while let Some(n) = compstack.pop() {
				let op = &cfg[n as usize];
				match op.op {
					Op::Ld(val) => {
						let num = builder.ins().iconst(ti32, val as i64);
						let stidx = builder.ins().load(ti32, aligned, vstackidx, 0);
						let newstidx = builder.ins().iadd(stidx, one);
						let newstidx4 = builder.ins().imul(newstidx, four);
						let slotptr = builder.ins().iadd(vstack, newstidx4);
						builder.ins().store(aligned, num, slotptr, 0);
						builder.ins().store(aligned, newstidx, vstackidx, 0);
					}
					Op::Bin(bop) => {
						let a = zero;
						let b = zero;
						let num = match bop {
							BinOp::Add => builder.ins().iadd(a, b),
							BinOp::Sub => builder.ins().isub(a, b),
							BinOp::Mul => builder.ins().imul(a, b),
							BinOp::Div => builder.ins().sdiv(a, b),
							BinOp::Mod => builder.ins().srem(a, b),
							BinOp::Cmp => builder.ins().icmp(IntCC::SignedGreaterThan, a, b),
						};
						let stidx = builder.ins().load(ti32, aligned, vstackidx, 0);
						let newstidx = builder.ins().iadd(stidx, one);
						let newstidx4 = builder.ins().imul(newstidx, four);
						let slotptr = builder.ins().iadd(vstack, newstidx4);
						builder.ins().store(aligned, num, slotptr, 0);
						builder.ins().store(aligned, newstidx, vstackidx, 0);
					}
					Op::Not => {}
					Op::Pop => {}
					Op::Dup => {}
					Op::Swp => {}
					Op::Rch => {}
					Op::Wch => {}
					Op::Rch => {}
					Op::Rum => {}
					Op::Wum => {}
					Op::Rem => {}
					Op::Wem(xy, dir) => {}
					Op::Jr(r0, r1, r2) => {
						compstack.push(r0);
						compstack.push(r1);
						compstack.push(r2);
					}
					Op::Jz(rz) => {
						compstack.push(rz);
					}
					Op::Ret => {
						builder.ins().return_(&[_one]);
						continue;
					}
					Op::Hcf => {
						let ebb = builder.create_ebb();
						builder.switch_to_block(ebb);
						builder.ins().jump(ebb, &[]);
						continue;
					}
					Op::Nop => {}
				}
				compstack.push(op.n);
			}

			builder.ins().return_(&[_one]);
		}

		self.ctx.func.signature.returns.push(AbiParam::new(tptr));
		let id = self
			.module
			.declare_function("f", Linkage::Export, &self.ctx.func.signature)
			.map_err(|e| e.to_string())?;
		self.module
			.define_function(id, &mut self.ctx)
			.map_err(|e| e.to_string())?;
		self.module.clear_context(&mut self.ctx);
		self.module.finalize_definitions();

		let func = self.module.get_finalized_function(id);
		let result = unsafe { std::mem::transmute::<_, fn() -> usize>(func) }();
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
}
