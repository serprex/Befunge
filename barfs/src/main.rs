mod cfg;
mod evalcfg;
mod jit;
mod util;

use std::env;
use std::fs::File;
use std::io::{BufRead, BufReader};

fn main() {
	let mut code = [0i32; 2560];
	let mut stack = [0i32; 4096];
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
					code[x << 5 | y] = ch as u32 as i32;
				}
			}
		}
	}

	let mut xy = 0;
	let mut dir = cfg::Dir::E;
	loop {
		let (cfg, progbits) = cfg::create_cfg(&code, xy, dir);
		if false {
			for (idx, node) in cfg.iter().enumerate() {
				println!("{} {:?}", idx, node);
			}
		}
		if let Some((newxy, newdir)) = if false {
			evalcfg::eval(&cfg, &progbits, &mut code, &mut stack, &mut stackidx)
		} else {
			match jit::execute(&cfg, &progbits, &mut code, &mut stack, &mut stackidx) {
				Ok(res) => {
					if false {
						println!("{:?} {}", res, stackidx);
					}
					res
				}
				Err(err) => {
					println!("{}", err);
					break;
				}
			}
		} { 
			xy = newxy;
			dir = newdir;
		} else {
			break;
		}
	}
}
