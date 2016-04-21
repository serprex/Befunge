:%y
new
blast
:0put
:v/\_s*\S/d
normal! G
while line('.') > 25
	normal! dd
endwhile
while line('.') < 25
	normal! o
endwhile
:%s/^.*$/\= (submatch(0) . repeat(' ', 80-len(submatch(0))))[:79]
noh
res 25
vertical res 80
call cursor(1, 1)
let b:stack = []
let b:data = {}
let b:dir = 0
let b:stop = 0
let b:x = 0
let b:y = 0
fu! s:pop()
	if ! empty(b:stack)
		return remove(b:stack, -1)
	endif
endfu
fu! BefungeExec(ch)
	if a:ch ==# ' '
	elseif a:ch =~# '\d'
		call add(b:stack, a:ch+0)
	elseif a:ch ==# '>'
		let b:dir = 0
	elseif a:ch ==# '^'
		let b:dir = 1
	elseif a:ch ==# '<'
		let b:dir = 2
	elseif a:ch ==# 'v'
		let b:dir = 3
	elseif a:ch ==# '#'
		call BefungeMove()
	elseif a:ch ==# ':'
		if ! empty(b:stack)
			call add(b:stack, b:stack[-1])
		endif
	elseif a:ch ==# '$'
		call s:pop()
	elseif a:ch ==# 'p'
		let l:a = s:pop()
		let l:b = s:pop()
		let l:c = s:pop()
		let b:data[l:a+l:b*25] = l:c
		if l:c<31 || l:c>127
			let l:c = 32
		endif
		call cursor(l:a+1, l:b+1)
		execute 'normal! cl' . nr2char(l:c)
	elseif a:ch ==# 'g'
		let l:a = s:pop()
		let l:b = s:pop()
		let l:c = l:a + l:b*25
		if has_key(b:data, l:c)
			call add(b:stack, b:data[l:c])
		else
			call add(b:stack, char2nr(getline(l:a+1)[l:b]))
		endif
	elseif a:ch ==# '+'
		let l:a = s:pop()
		let l:b = s:pop()
		call add(b:stack, b+a)
	elseif a:ch ==# '-'
		let l:a = s:pop()
		let l:b = s:pop()
		call add(b:stack, b-a)
	elseif a:ch ==# '*'
		let l:a = s:pop()
		let l:b = s:pop()
		call add(b:stack, b*a)
	elseif a:ch ==# '/'
		let l:a = s:pop()
		let l:b = s:pop()
		call add(b:stack, b/a)
	elseif a:ch ==# '%'
		let l:a = s:pop()
		let l:b = s:pop()
		call add(b:stack, b%a)
	elseif a:ch ==# '`'
		let l:a = s:pop()
		let l:b = s:pop()
		call add(b:stack, b>a)
	elseif a:ch ==# '!'
		call add(b:stack, !s:pop())
	elseif a:ch ==# '"'
		call BefungeMove()
		let l:ch = getline(b:y+1)[b:x]
		while l:ch != '"'
			call add(b:stack, char2nr(l:ch))
			call BefungeMove()
			let l:ch = getline(b:y+1)[b:x]
		endwhile
	elseif a:ch ==# '|'
		let b:dir = s:pop() ? 1 : 3
	elseif a:ch ==# '_'
		let b:dir = s:pop() ? 2 : 0
	elseif a:ch ==# '\'
		let l:a = s:pop()
		let l:b = s:pop()
		call add(b:stack, l:b)
		call add(b:stack, l:a)
	elseif a:ch ==# '?'
		let b:dir = reltime()[1]%4
	elseif a:ch ==# '.'
		echon s:pop() . ' '
	elseif a:ch ==# ','
		echon nr2char(s:pop())
	elseif a:ch ==# '&'
		call add(b:stack, input('')+0)
	elseif a:ch ==# '~'
		call add(b:stack, char2nr(getchar()))
	else
		return a:ch ==# '@'
	endif
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
endfu
fu! BefungeStep()
	let b:x = col('.')-1
	let b:y = line('.')-1
	if ! BefungeExec(getline(b:y+1)[b:x])
		call BefungeMove()
		call cursor(b:y+1, b:x+1)
	endif
endfu
fu! BefungeJog()
	let b:x = col('.')-1
	let b:y = line('.')-1
	let b:stop = 0
	while ! BefungeExec(getline(b:y+1)[b:x])
		call BefungeMove()
		call cursor(b:y+1, b:x+1)
		redr
	endwhile
endfu
fu! BefungeRun()
	let b:x = col('.')-1
	let b:y = line('.')-1
	let b:stop = 0
	while ! BefungeExec(getline(b:y+1)[b:x])
		call BefungeMove()
	endwhile
	call cursor(b:y+1, b:x+1)
endfu
nnoremap <silent> <buffer> <F5> :call BefungeRun()<cr>
nnoremap <silent> <buffer> <F6> :call BefungeJog()<cr>
nnoremap <silent> <buffer> <F7> :echo b:stack<cr>
nnoremap <silent> <buffer> <F8> :echo b:data<cr>
nnoremap <silent> <buffer> <F10> :call BefungeStep()<cr>
setlocal colorcolumn=80
setlocal cursorcolumn
setlocal nu

