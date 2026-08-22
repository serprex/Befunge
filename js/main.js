#!/bin/node
import * as funge from './funge.js';
import fs from 'node:fs';
const buf = Buffer.alloc(1);
let peeked = -1;
// one byte, -1 at end of input
function readchar() {
	if (peeked !== -1) {
		const c = peeked;
		peeked = -1;
		return c;
	}
	for (;;) {
		try {
			return fs.readSync(process.stdin.fd, buf, 0, 1) ? buf[0] : -1;
		} catch (ex) {
			if (ex.code === 'EOF') return -1;
			if (ex.code !== 'EAGAIN' && ex.code !== 'EINTR') {
				throw ex;
			}
		}
	}
}
// like scanf %d: skip space, read digits, leave the terminator for next time
function readnum() {
	let c = readchar();
	while (c === 32 || (c >= 9 && c <= 13)) c = readchar();
	let neg = false;
	if (c === 43 || c === 45) {
		neg = c === 45;
		c = readchar();
	}
	let n = 0;
	while (c >= 48 && c <= 57) {
		n = n * 10 + (c - 48);
		c = readchar();
	}
	peeked = c;
	return neg ? -n : n;
}
const opts = {};
let path = null,
	noopt = false;
for (const argv of process.argv) {
	if (argv === '--') noopt = true;
	else if (!noopt && argv.startsWith('--')) opts[argv.slice(2)] = true;
	else path = argv;
}
fs.readFile(path, 'utf8', (err, board) => {
	if (err) return;
	const mem = new WebAssembly.Memory({ initial: 1 });
	funge.runSource(
		board,
		{
			'': {
				p: x => {
					process.stdout.write(x + ' ');
				},
				q: x => process.stdout.write(String.fromCharCode(x)),
				i: readnum,
				c: readchar,
				r: funge.r4,
				t: x =>
					console.log(x, `[${new Int32Array(mem.buffer).slice(0, x >> 2)}]`),
				m: mem,
			},
		},
		opts,
	);
});
