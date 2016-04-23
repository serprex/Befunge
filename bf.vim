%y
new
blast
setlocal cmdheight=4
0put
v/\_s*\S/d
normal! 26gg
if line('.') == 26
	normal! dG
endif
while line('.') < 25
	normal! o
endw
%s/^.*$/\= (submatch(0) . repeat(' ', 80-len(submatch(0))))[:79]
noh
res 25
vertical res 80
normal! gg0
let b:stack = []
let b:data = {}
fu! s:e()
	let b:x = b:x == 79 ? 0 : b:x + 1
endfu
fu! s:n()
	let b:y = b:y == 0 ? 24 : b:y - 1
	let b:curline = getline(b:y+1)
endfu
fu! s:w()
	let b:x = b:x == 0 ? 79 : b:x - 1
endfu
fu! s:s()
	let b:y = b:y == 24 ? 0 : b:y + 1
	let b:curline = getline(b:y+1)
endfu
let b:dir = 's:e'
let b:x = 0
let b:y = 0
fu! s:pop()
	if ! empty(b:stack)
		return remove(b:stack, -1)
	endif
endfu
fu! s:l0()
	call add(b:stack, 0)
endfu
fu! s:l1()
	call add(b:stack, 1)
endfu
fu! s:l2()
	call add(b:stack, 2)
endfu
fu! s:l3()
	call add(b:stack, 3)
endfu
fu! s:l4()
	call add(b:stack, 4)
endfu
fu! s:l5()
	call add(b:stack, 5)
endfu
fu! s:l6()
	call add(b:stack, 6)
endfu
fu! s:l7()
	call add(b:stack, 7)
endfu
fu! s:l8()
	call add(b:stack, 8)
endfu
fu! s:l9()
	call add(b:stack, 9)
endfu
fu! s:east()
	let b:dir='s:e'
endfu
fu! s:north()
	let b:dir='s:n'
endfu
fu! s:west()
	let b:dir='s:w'
endfu
fu! s:south()
	let b:dir='s:s'
endfu
fu! s:hop()
	call call(b:dir,[])
endfu
fu! s:dup()
	if ! empty(b:stack)
		call add(b:stack, b:stack[-1])
	endif
endfu
fu! s:opop()
	call s:pop()
endfu
fu! s:wmem()
	let l:a = s:pop()
	let l:b = s:pop()
	let l:c = s:pop()
	let b:data[l:a+l:b*25] = l:c
	call cursor(l:a+1, l:b+1)
	exec 'normal! r' . (l:c<31 || l:c>127 ? ' ' : nr2char(l:c))
endfu
fu! s:rmem()
	let l:a = s:pop()
	let l:b = s:pop()
	let l:c = l:a+l:b*25
	call add(b:stack, has_key(b:data, l:c) ? b:data[l:c] : char2nr(getline(l:a+1)[l:b]))
endfu
fu! s:add()
	call add(b:stack, s:pop()+s:pop())
endfu
fu! s:sub()
	let l:a = s:pop()
	let l:b = s:pop()
	call add(b:stack, b-a)
endfu
fu! s:mul()
	call add(b:stack, s:pop()*s:pop())
endfu
fu! s:div()
	let l:a = s:pop()
	let l:b = s:pop()
	call add(b:stack, b/a)
endfu
fu! s:rem()
	let l:a = s:pop()
	let l:b = s:pop()
	call add(b:stack, b%a)
endfu
fu! s:cmp()
	let l:a = s:pop()
	let l:b = s:pop()
	call add(b:stack, b>a)
endfu
fu! s:not()
	call add(b:stack, !s:pop())
endfu
fu! s:str()
	call call(b:dir,[])
	while b:curline[b:x] != '"'
		call add(b:stack, char2nr(b:curline[b:x]))
		call call(b:dir,[])
	endw
endfu
fu! s:vif()
	let b:dir = s:pop() ? 's:n' : 's:s'
endfu
fu! s:hif()
	let b:dir = s:pop() ? 's:w' : 's:e'
endfu
fu! s:swap()
	let l:a = s:pop()
	let l:b = s:pop()
	call add(b:stack, l:a)
	call add(b:stack, l:b)
endfu
fu! s:rng()
	let b:dir = ['s:n', 's:s', 's:w', 's:e'][reltime()[1]%4]
endfu
fu! s:prnm()
	echon s:pop() . ' '
endfu
fu! s:prch()
	echon nr2char(s:pop())
endfu
fu! s:getnm()
	call add(b:stack, input('')+0)
endfu
fu! s:getch()
	call add(b:stack, char2nr(getchar()))
endfu
fu! s:done()
	return 1
endfu
fu! s:befprequel()
	let b:x = col('.')-1
	let b:y = line('.')-1
	let b:curline = getline(b:y+1)
endfu
fu! BefungeStep()
	call s:befprequel()
	while !has_key(s:ops, b:curline[b:x])
		call call(b:dir,[])
	endw
	if !call(s:ops[b:curline[b:x]],[])
		call call(b:dir,[])
	endif
	call cursor(b:y+1, b:x+1)
	return b:curline[b:x]
endfu
fu! BefungeJog()
	while BefungeStep() != '@'
		redr
	endw
endfu
fu! BefungeRun()
	call s:befprequel()
	while !(has_key(s:ops, b:curline[b:x]) && call(s:ops[b:curline[b:x]],[]))
		call call(b:dir,[])
	endw
	return cursor(b:y+1, b:x+1)
endfu
let s:ops = {0:'s:l0',1:'s:l1',2:'s:l2',3:'s:l3',4:'s:l4',5:'s:l5',6:'s:l6',7:'s:l7',8:'s:l8',9:'s:l9',
	\'>':'s:east','^':'s:north','<':'s:west','v':'s:south','#':'s:hop',':':'s:dup','$':'s:opop','p':'s:wmem','g':'s:rmem',
	\'+':'s:add','-':'s:sub','*':'s:mul','/':'s:div','%':'s:rem','`':'s:cmp','!':'s:not','"':'s:str',
	\'|':'s:vif','_':'s:hif','\':'s:swap','?':'s:rng','.':'s:prnm',',':'s:prch','&':'s:getnm','~':'s:getch','@':'s:done'}
nnoremap <silent> <buffer> <F5> :call BefungeRun()<cr>
nnoremap <silent> <buffer> <F6> :call BefungeJog()<cr>
nnoremap <silent> <buffer> <F7> :echo b:stack<cr>
nnoremap <silent> <buffer> <F8> :echo b:data<cr>
nnoremap <silent> <buffer> <F10> :call BefungeStep()<cr>
setlocal colorcolumn=80
setlocal cursorcolumn
setlocal nu
syn match befungeNumber '\d'
syn match befungeOperator '[+\-*/%`!:$\\,.~&pg]'
syn match befungeMovement '[<v>^#]'
syn match befungeLogic '[_|@"?]'
syn match befungeOther '[^0-9+\-*/%`\\!:$,.~&pg>v<^#_|@"?]'
hi def link befungeNumber Number
hi def link befungeOperator Operator
hi def link befungeMovement Identifier
hi def link befungeLogic Keyword
hi def link befungeOther Comment
