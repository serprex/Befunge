pub fn readu32(data: &[u8], idx: usize) -> u32 {
	(data[idx] as u32)
		| (data[idx + 1] as u32) << 8
		| (data[idx + 2] as u32) << 16
		| (data[idx + 3] as u32) << 24
}

pub fn writeu32(data: &mut [u8], idx: usize, v: u32) -> () {
	data[idx] = (v & 255) as u8;
	data[idx + 1] = ((v >> 8) & 255) as u8;
	data[idx + 2] = ((v >> 16) & 255) as u8;
	data[idx + 3] = ((v >> 24) & 255) as u8;
}

pub fn popu32(data: &mut [u8], stackidx: &mut usize) -> u32 {
	if *stackidx >= 4 {
		*stackidx -= 4;
		readu32(data, *stackidx)
	} else {
		0
	}
}

pub fn pushu32(data: &mut [u8], stackidx: &mut usize, v: u32) -> () {
	writeu32(data, *stackidx, v);
	*stackidx += 4;
}
