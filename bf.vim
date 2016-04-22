:%y
new
blast
setlocal cmdheight=4
:0put
:v/\_s*\S/d
normal! 26gg
if line('.') == 26
	normal! dG
endif
while line('.') < 25
	normal! o
endwhile
:%s/^.*$/\= (submatch(0) . repeat(' ', 80-len(submatch(0))))[:79]
noh
res 25
vertical res 80
normal! gg0
let b:stack = []
let b:data = {}
let b:dir = 0
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
	let b:dir=0
endfu
fu! s:north()
	let b:dir=1
endfu
fu! s:west()
	let b:dir=2
endfu
fu! s:south()
	let b:dir=3
endfu
fu! s:hop()
	call BefungeMove()
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
	if l:c<31 || l:c>127
		exec 'normal! cl '
	else
		exec 'normal! cl' . nr2char(l:c)
	endif
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
	let l:ch = BefungeMove()
	while l:ch != '"'
		call add(b:stack, char2nr(l:ch))
		let l:ch = BefungeMove()
	endwhile
endfu
fu! s:vif()
	let b:dir = s:pop() ? 1 : 3
endfu
fu! s:hif()
	let b:dir = s:pop() ? 2 : 0
endfu
fu! s:swap()
	let l:a = s:pop()
	let l:b = s:pop()
	call add(b:stack, l:a)
	call add(b:stack, l:b)
endfu
fu! s:rng()
	let b:dir = reltime()[1]%4
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
fu! BefungeMove()
	if b:dir == 0
		let b:x = b:x == 79 ? 0 : b:x + 1
	elseif b:dir == 1
		let b:y = b:y == 0 ? 24 : b:y - 1
	elseif b:dir == 2
		let b:x = b:x == 0 ? 79 : b:x - 1
	else
		let b:y = b:y == 24 ? 0 : b:y + 1
	endif
	return getline(b:y+1)[b:x]
endfu
fu! s:befprequel()
	let b:x = col('.')-1
	let b:y = line('.')-1
	return getline(b:y+1)[b:x]
endfu
fu! BefungeStep()
	let l:ch = s:befprequel()
	if !(has_key(s:ops, l:ch) && call(s:ops[l:ch],[]))
		let l:ch = BefungeMove()
		call cursor(b:y+1, b:x+1)
	endif
endfu
fu! BefungeJog()
	let l:ch = s:befprequel()
	while !(has_key(s:ops, l:ch) && call(s:ops[l:ch],[]))
		let l:ch = BefungeMove()
		call cursor(b:y+1, b:x+1)
		redr
	endwhile
endfu
fu! BefungeRun()
	let l:ch = s:befprequel()
	while !(has_key(s:ops, l:ch) && call(s:ops[l:ch],[]))
		let l:ch = BefungeMove()
	endwhile
	return cursor(b:y+1, b:x+1)
endfu
let s:ops = {0:'s:l0',1:'s:l1',2:'s:l2',3:'s:l3',4:'s:l4',5:'s:l5',6:'s:l6',7:'s:l7',8:'s:l8',9:'s:l9',
	\'>':'s:east','^':'s:north','<':'s:west','v':'s:south','#':'s:hop',':':'s:dup','$':'s:opop','p':'s:wmem','g':'s:rmem',
	\'+':'s:add','-':'s:sub','*':'s:mul','/':'s:div','%':'s:rem','`':'s:cmp','!':'s:not','"':'s:str',
	\"|":'s:vif',"_":'s:hif','\':'s:swap','?':'s:rng','.':'s:prnm',',':'s:prch','&':'s:getnm','~':'s:getch','@':'s:done'}
nnoremap <silent> <buffer> <F5> :call BefungeRun()<cr>
nnoremap <silent> <buffer> <F6> :call BefungeJog()<cr>
nnoremap <silent> <buffer> <F7> :echo b:stack<cr>
nnoremap <silent> <buffer> <F8> :echo b:data<cr>
nnoremap <silent> <buffer> <F10> :call BefungeStep()<cr>
setlocal colorcolumn=80
setlocal cursorcolumn
setlocal nu

