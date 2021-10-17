(function () {
	'use strict';
	const taBoard = document.getElementById('taBoard');
	const prOut = document.getElementById('prOut');
	function handle(interp) {
		return (s, e) => {
			const imp = {
				'': {
					p: x => (prOut.textContent += x + ' '),
					q: x => (prOut.textContent += String.fromCharCode(x)),
					i: () => prompt('Number', '') | 0,
					c: () => prompt('Character', '').charCodeAt(0) | 0,
					r: funge.r4,
					m: new WebAssembly.Memory({ initial: 1 }),
				},
			};
			prOut.textContent = '';
			funge.runSource(taBoard.value, imp, interp);
		};
	}
	document.getElementById('btnRun').addEventListener('click', handle(false));
	document.getElementById('btnWalk').addEventListener('click', handle(true));
})();
