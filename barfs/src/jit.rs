use std::slice;

use cranelift::prelude::*;
use cranelift_module::{DataContext, Linkage, Module};
use cranelift_simplejit::{SimpleJITBackend, SimpleJITBuilder};

use cfg;

pub struct Jit {
	builder_ctx: FunctionBuilderContext,
	ctx: codegen::Context,
	data_ctx: DataContext,
	module: Module<SimpleJITBackend>,
}

impl Jit {
	pub fn new() -> Self {
		let builder = SimpleJITBuilder::new();
		let module = Module::new(builder);
		Self {
			builder_ctx: FunctionBuilderContext::new(),
			ctx: module.make_context(),
			data_ctx: DataContext::new(),
			module,
		}
	}

	pub fn compile(
		&mut self,
		code: Vec<u8>,
		stack: Vec<u8>,
		xy: usize,
		dir: cfg::Dir,
	) -> Result<*const u8, String> {
		let (cfg, progbits) = cfg::create_cfg(&code, xy, dir);

		let int32 = codegen::ir::types::Type::int(32).ok_or("ISA doesn't support 32-bit int")?;

		let stack: Result<_, String> = {
			self.data_ctx.define(stack.into_boxed_slice());
			let id = self
				.module
				.declare_data("s", Linkage::Export, true)
				.map_err(|e| e.to_string())?;
			self.module
				.define_data(id, &self.data_ctx)
				.map_err(|e| e.to_string())?;
			self.data_ctx.clear();
			self.module.finalize_definitions();
			let buffer = self.module.get_finalized_data(id);
			Ok(unsafe { slice::from_raw_parts(buffer.0, buffer.1) })
		};

		let codedata: Result<_, String> = {
			self.data_ctx.define(code.into_boxed_slice());
			let id = self
				.module
				.declare_data("c", Linkage::Export, true)
				.map_err(|e| e.to_string())?;
			self.module
				.define_data(id, &self.data_ctx)
				.map_err(|e| e.to_string())?;
			self.data_ctx.clear();
			self.module.finalize_definitions();
			let buffer = self.module.get_finalized_data(id);
			Ok(unsafe { slice::from_raw_parts(buffer.0, buffer.1) })
		};

		{
			let mut builder = FunctionBuilder::new(&mut self.ctx.func, &mut self.builder_ctx);
			let entry_ebb = builder.create_ebb();
			builder.append_ebb_params_for_function_params(entry_ebb);
			builder.switch_to_block(entry_ebb);
			builder.seal_block(entry_ebb);

			let zero = builder.ins().iconst(int32, 0);
			builder.ins().return_(&[zero]);
		}

		self.ctx.func.signature.returns.push(AbiParam::new(int32));
		let id = self
			.module
			.declare_function("f", Linkage::Export, &self.ctx.func.signature)
			.map_err(|e| e.to_string())?;
		self.module
			.define_function(id, &mut self.ctx)
			.map_err(|e| e.to_string())?;
		self.module.clear_context(&mut self.ctx);
		self.module.finalize_definitions();

		Ok(self.module.get_finalized_function(id))
	}
}
