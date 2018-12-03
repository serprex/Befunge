This is my collection of Befunge VMs. I'll explain their evolution chronologically

### marsh
March 2010 I created marsh

It included such microoptimizations as postprocessing the assembly of GCC since GCC was generating 'set `rax` to `L1`, jump to `L2`, which indirectly jumps to `rax`'.  Also included a spawn script which would replace the 2000 spaces in the binary with befunge sourcecode, allowing self hosting befunge executables

A month later I optimized indexing by having one dimension be a power of 2. The choices are 128x25 vs 80x32. The latter is much smaller, but somewhat unintuitive as it the memory layout puts vertical text side by side. I also observed that if I duplicated the VM 4 times I could reduce the instruction dispatch to not have to check direction. Changing direction works by changing VMs.

#### Intermission
During this time I moved out, read _Fountainhead_ & _Atlas Shrugged_, & began college

### bejit
Come December I made a first jab at bejit. It was a sea of malloc without any peepholing, & it outraced marsh with ease. Soon after I started on an optimizer which would iterate the entire 10240 loop cache cells when replacing a node. There were so many bugs. By February I gave up, rewrote it to use bytecode without optimizations, found performance comparable to marsh. Optimizations fixed that, & I moved on

#### Years go by, until September 2015
During this time I've dropped out of college, moved back to my hometown, got into elementsthegame, made openEtG, was laid off shortly after buying a home, had recently transitioned from flooring back into programming. I began working offline on a Befunge to Python bytecode JIT while the summer was spent stripping & staining the house (don't paint cedar). I really have to thank the help I received with the house. Also I started using vim

### funge.py
I don't remember what made me want to get back into mucking with Python bytecode, but I'd been itching to do something like this but CLR & JVM are both snobs about non static stack depth. I soon learnt that it was pretty important to handle underflow, & that meant tracking stack depth

I realized that g's bound checking could be optimized to only check 0<=x<2560, so this was backported to marsh & bejit too

In February it took 3 attempts to reduce the verbosity of the opcode definitions, the idea behind templating would be that the opcode blocks are then mostly constant & I can skip many LOAD/ADD/STORE instructions. The only variable portion would be the jump offsets. I was in a rut trying to optimize the compiler in ways that would make beer6 faster. Beer6 being a special benchmark since it triggers a couple hundred recompiles. A fork was made to experiment with peepholing

I also got thinking in February how the Python bytecode could be optimized. I found abarnert had a repo experimenting with it, so I joined in to make a strategic effort in optimizing funge.py

I was trying to work out how to remove stack guards. I also decided that funge.py would use unbounded space. Being able to remove bounds checking made it come without perf loss. Templating had to be gutted in order for instructions to be able to handle partial const propagation. Instructions were moved into classes to start grouping the data that was getting too scattered. Found that perf was better in using classes to resolve differences rather than lookups on op. Mutating __class__ was a little lower but it was a net win

Having been working with Befunge now for half a year, I started thinking how to make a Befunge IDE in vim. bef.vim could use a lot of work, I was really let down by just how slow vimscript is

In May I let wfunge.py be the only funge.py. There were some fun microoptimizations with the new bytecode, such as it being better to load a 0 than duplicate the non-zero stack depth & unary not it

### bejit-elvm
In November 2016 I found out that \ was broken in all my implementations for stacks of depth 1. I also worked out how marsh/bejit could have tighter code by leaving a stack empty rather than pushing a 0 on it. I also found ELVM, a neat project, so I made bejit-elvm because their interpreter was like most interpreters. Also spent some time improving their constant constructions to include factoring alongside base 9 encoding

### funge.js
I set things down until March, when this readme is being written, when WASM became available in Firefox & Chrome. Over the course of a couple weeks an optimizing wasm jit was made. Instead of tracking partial application it tracks which stack an operator should get its values from
