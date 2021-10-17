use rand;
use std::io;
use std::mem::transmute;

pub fn rand_nibble() -> u8 {
	rand::random::<u8>() & 3
}

pub fn read_char() -> i32 {
	let mut line = String::new();
	io::stdin()
		.read_line(&mut line)
		.expect("Error reading character");
	line.chars()
		.next()
		.map(|c| unsafe { transmute(c) })
		.unwrap_or(0i32)
}

pub fn read_int() -> i32 {
	let mut line = String::new();
	io::stdin()
		.read_line(&mut line)
		.expect("Error reading number");
	line.trim().parse().unwrap_or(0)
}

pub fn putnum(n: i32) {
	print!("{} ", n);
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
