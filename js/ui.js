(function(){"use strict";
const funge = require("js/funge");
const taBoard = document.getElementById("taBoard");
const prOut = document.getElementById("prOut");
document.getElementById("btnGo").addEventListener("click", (s, e) => {
	const imp = {
		"": {
			p: x => prOut.textContent += x + " ",
			q: x => prOut.textContent += String.fromCharCode(x),
			i: () => prompt("Number", "")|0,
			c: () => prompt("Character", "").charCodeAt(0)|0,
			r: funge.r4,
			m: new WebAssembly.Memory({ initial: 1 }),
		}
	};
	prOut.textContent = "";
	funge.runSource(taBoard.value, imp);
});
})();
