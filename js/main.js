#!/bin/node
const funge = require('./funge');
const fs = require('fs');
function readline() {
	let ret = '';
	const buf = new Buffer.alloc(1);
	for (;;) {
		try {
			const bytesRead = fs.readSync(process.stdin.fd, buf, 0, 1);
			if (!bytesRead || buf[0] === 10) return ret;
			ret += String.fromCharCode(buf[0]);
		} catch (ex) {
			if (ex.code !== 'EAGAIN' && ex.code !== 'EINTR') {
				throw ex;
			}
		}
	}
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
				i: () => readline() | 0,
				c: () => readline().charCodeAt(0) | 0,
				r: funge.r4,
				t: x =>
					console.log(x, `[${new Int32Array(mem.buffer).slice(0, x >> 2)}]`),
				m: mem,
			},
		},
		opts,
	);
});
