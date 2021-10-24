use rand;
use std::io::{self, Read, Write};

pub fn rand_nibble() -> u8 {
	rand::random::<u8>() & 3
}

pub fn read_char() -> i32 {
	let mut byte = [0u8];
	let iostdin = io::stdin();
	let mut stdin = iostdin.lock();
	if stdin.read_exact(&mut byte).is_ok() {
		byte[0] as i32
	} else {
		-1
	}
}

pub fn read_int() -> i32 {
	let mut line = String::new();
	io::stdin()
		.read_line(&mut line)
		.expect("Error reading number");
	line.trim().parse().unwrap_or(0)
}

pub fn putch(n: i32) {
	let mut buf = [0u8; 4];
	let ch = std::char::from_u32(n as u32).unwrap_or(std::char::REPLACEMENT_CHARACTER);
	let s = ch.encode_utf8(&mut buf);
	let _ = io::stdout().write_all(s.as_bytes());
}

pub fn putnum(n: i32) {
	let _ = io::stdout().write_all(format!("{} ", n).as_bytes());
}

pub fn pop(data: &mut [i32], stackidx: &mut isize) -> i32 {
	if *stackidx < 0 {
		0
	} else {
		let v = data[*stackidx as usize];
		*stackidx = stackidx.wrapping_sub(1);
		v
	}
}

pub fn push(data: &mut [i32], stackidx: &mut isize, v: i32) -> () {
	*stackidx = stackidx.wrapping_add(1);
	data[*stackidx as usize] = v;
}

pub fn print_stack(stack: *const i32, stackidx: isize) -> () {
	print!("{}", stackidx);
	let mut idx = 0;
	while idx <= stackidx {
		print!(" {}", unsafe { *stack.offset(idx) });
		idx += 1;
	}
	println!();
}
