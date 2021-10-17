#!/bin/node
const funge = require('./funge');
const fs = require('fs');
function readline() {
	let ret = '';
	const buf = new Buffer.alloc(1);
	while (true) {
		try {
			const bytesRead = fs.readSync(process.stdin.fd, buf, 0, 1);
			if (!bytesRead || buf[0] == 10) return ret;
			ret += String.fromCharCode(buf[0]);
		} catch (ex) {
			if (ex.code != 'EAGAIN' && ex.code != 'EINTR') {
				throw ex;
			}
		}
	}
}
fs.readFile(process.argv[process.argv.length - 1], 'utf8', (err, board) => {
	funge.runSource(board, {
		'': {
			p: x => process.stdout.write(x + ' '),
			q: x => process.stdout.write(String.fromCharCode(x)),
			i: () => readline() | 0,
			c: () => readline().charCodeAt(0) | 0,
			r: funge.r4,
			m: new WebAssembly.Memory({ initial: 1 }),
		},
	});
});
