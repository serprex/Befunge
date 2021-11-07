(function () {
	'use strict';
	const taBoard = document.getElementById('taBoard');
	const prOut = document.getElementById('prOut');
	function handle(s, e) {
		const mem = new WebAssembly.Memory({ initial: 1 });
		const imp = {
			'': {
				p: x => (prOut.textContent += x + ' '),
				q: x => (prOut.textContent += String.fromCharCode(x)),
				i: () => prompt('Number', '') | 0,
				c: () => prompt('Character', '').charCodeAt(0) | 0,
				r: funge.r4,
				t: x =>
					console.log(x, `[${new Int32Array(mem.buffer).slice(0, x >> 2)}]`),
				m: mem,
			},
		};
		prOut.textContent = '';
		funge.runSource(taBoard.value, imp, {
			interpret: document.getElementById('chkInterpret').checked,
			time: document.getElementById('chkTime').checked,
			trace: document.getElementById('chkTrace').checked,
		});
	}
	document.getElementById('btnRun').addEventListener('click', handle);
})();
