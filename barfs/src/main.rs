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
use std::mem::transmute;

fn main() {
	let mut code = [0i32; 2560];
	let mut stack = [0i32; 4096];
	let mut stackidx: usize = 0;
	{
		let fin = File::open(env::args().nth(1).expect("Missing argument for input file"))
			.expect("Failed to open file");
		let reader = BufReader::new(fin);
		for x in 0..79usize {
			for y in 0..24usize {
				code[x << 5 | y] = 32;
			}
		}
		for (y, line) in reader.lines().take(25).enumerate() {
			if let Ok(line) = line {
				for (x, ch) in line.chars().take(80).take_while(|&c| c != '\n').enumerate() {
					code[x << 5 | y] = unsafe { transmute(ch as u32) };
				}
			}
		}
	}

	let mut xy = 0;
	let mut dir = cfg::Dir::E;
	loop {
		let (cfg, progbits) = cfg::create_cfg(&code, xy, dir);
		for (idx, node) in cfg.iter().enumerate() {
			println!("{} {:?}", idx, node);
		}
		let ret = if true {
			evalcfg::eval(&cfg, &progbits, &mut code, &mut stack, &mut stackidx)
		} else {
			let mut jit = jit::Jit::new();
			match jit.compile(&cfg, &progbits, &mut code, &mut stack, &mut stackidx) {
				Ok(res) => {
					println!("{:?} {}", res, stackidx);
					res
				}
				Err(err) => {
					print!("{}", err);
					break;
				}
			}
		};
		if ret.0 == usize::max_value() {
			break;
		}
		xy = ret.0;
		dir = ret.1;
	}
}
