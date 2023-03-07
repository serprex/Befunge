use rand;
use std::io::{self, Read, Write};
use crate::CellInt;

pub fn rand_nibble() -> u8 {
	rand::random::<u8>() & 3
}

pub fn read_char() -> CellInt {
	let mut byte = [0u8];
	let iostdin = io::stdin();
	let mut stdin = iostdin.lock();
	if stdin.read_exact(&mut byte).is_ok() {
		byte[0] as CellInt
	} else {
		-1
	}
}

pub fn read_int() -> CellInt {
	let mut line = String::new();
	io::stdin()
		.read_line(&mut line)
		.expect("Error reading number");
	line.trim().parse().unwrap_or(0)
}

pub fn putch(n: CellInt) {
	let mut buf = [0u8; 4];
	let ch = std::char::from_u32(n as u32).unwrap_or(std::char::REPLACEMENT_CHARACTER);
	let s = ch.encode_utf8(&mut buf);
	let _ = io::stdout().write_all(s.as_bytes());
}

pub fn putnum(n: CellInt) {
	let _ = io::stdout().write_all(format!("{} ", n).as_bytes());
}

pub fn pop(data: &mut [CellInt], stackidx: &mut isize) -> CellInt {
	if *stackidx < 0 {
		0
	} else {
		let v = data[*stackidx as usize];
		*stackidx = stackidx.wrapping_sub(1);
		v
	}
}

pub fn push(data: &mut [CellInt], stackidx: &mut isize, v: CellInt) -> () {
	*stackidx = stackidx.wrapping_add(1);
	data[*stackidx as usize] = v;
}

pub fn print_stack(stack: *const CellInt, stackidx: isize) -> () {
	print!("{}", stackidx);
	let mut idx = 0;
	while idx <= stackidx {
		print!(" {}", unsafe { *stack.offset(idx) });
		idx += 1;
	}
	println!();
}
