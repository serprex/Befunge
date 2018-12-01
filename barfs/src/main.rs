extern crate cranelift;
extern crate cranelift_module;
extern crate cranelift_simplejit;
extern crate fnv;
extern crate rand;

mod cfg;
mod evalcfg;
mod jit;
mod util;

use std::env;
use std::fs::File;
use std::io::{BufRead, BufReader, Read};
use std::mem;

fn main() {
	let mut code = [0u8; 10240];
	let mut stack = [0u8; 4096];
	let mut stackidx: usize = 0;
	{
		let fin = File::open(env::args().nth(1).expect("Missing argument for input file"))
			.expect("Failed to open file");
		let reader = BufReader::new(fin);
		for x in 0..79usize {
			for y in 0..24usize {
				code[(x << 5 | y) * 4] = 32;
			}
		}
		for (y, line) in reader.lines().take(25).enumerate() {
			if let Ok(line) = line {
				for (x, ch) in line.chars().take(80).take_while(|&c| c != '\n').enumerate() {
					util::writeu32(&mut code, x << 5 | y, ch as u32);
				}
			}
		}
	}

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
