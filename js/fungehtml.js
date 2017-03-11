(function(){"use strict";
var funge = require("js/funge");
var taBoard = document.getElementById("taBoard");
var prOut = document.getElementById("prOut");
document.getElementById("btnGo").addEventListener("click", (s, e) => {
	var imp = {
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
