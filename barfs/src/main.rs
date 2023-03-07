mod cfg;
mod evalcfg;
mod jit;
mod util;

use std::env;
use std::fs::File;
use std::io::{BufRead, BufReader};

pub type CellInt = i64;

fn main() {
	let mut code: [CellInt; 2560] = [0; 2560];
	let mut stack: [CellInt; 4096] = [0; 4096];
	let mut stackidx: isize = -1;
	{
		let fin = File::open(env::args().nth(1).expect("Missing argument for input file"))
			.expect("Failed to open file");
		let reader = BufReader::new(fin);
		for x in 0..80usize {
			for y in 0..25usize {
				code[x << 5 | y] = 32;
			}
		}
		for (y, line) in reader.lines().take(25).enumerate() {
			if let Ok(line) = line {
				for (x, ch) in line.chars().take(80).take_while(|&c| c != '\n').enumerate() {
					code[x << 5 | y] = ch as u32 as CellInt;
				}
			}
		}
	}

	let mut xy = 0;
	let mut dir = cfg::Dir::E;
	loop {
		let mut progbits = [0u8; 320];
		let cfg = cfg::create_cfg(&code, &mut progbits, xy, dir);
		if false {
			for (idx, node) in cfg.iter().enumerate() {
				println!("{} {:?}", idx, node);
			}
		}
		let newxydir = if false {
			evalcfg::eval(&cfg, &progbits, &mut code, &mut stack, &mut stackidx)
		} else {
			match jit::execute(&cfg, &progbits, &mut code, &mut stack, &mut stackidx) {
				Ok(res) => {
					if false {
						print!("{} ", res);
						util::print_stack(stack.as_ptr(), stackidx);
					}
					res
				}
				Err(err) => {
					println!("{}", err);
					break;
				}
			}
		};

		if newxydir == u32::max_value() {
			break;
		}
		xy = newxydir >> 2;
		dir = newxydir.into();
	}
}
