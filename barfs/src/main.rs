extern crate cranelift;
extern crate cranelift_module;
extern crate cranelift_simplejit;

mod cfg;
mod evalcfg;
mod jit;
mod util;

/*
use std::fmt::Write;
use std::io::{self, Read};
use std::fs::File;
use std::env::args;
*/
use std::mem;

fn main() {
	let mut code = vec![0u8; 10240];
	let mut stack = vec![0u8; 4096];
	let mut stackidx: usize = 0;
	code[0] = b'1';
	code[32] = b'1';
	code[64] = b'+';
	code[96] = b'.';
	code[128] = b'@';
	let (cfg, progbits) = cfg::create_cfg(&code, 0, cfg::Dir::E);
	print!("{:?}", cfg);
	evalcfg::eval(&cfg, &progbits, &mut code, &mut stack, &mut stackidx);

	/*
	let mut jit = jit::Jit::new();
	match jit.compile(code, stack, 0, cfg::Dir::E) {
		Ok(func) => {
			let f = unsafe { mem::transmute::<_, fn() -> u32>(func) };
			print!("{}", f());
		}
		Err(err) => print!("{}", err),
	}
	*/
}
