# Sum six signed words. x10 = 37, also stored at 0x440.
addi x20, x0, 1024
addi x1, x0, 6
addi x10, x0, 0
loop:
lw x2, 0(x20)
add x10, x10, x2
addi x20, x20, 4
addi x1, x1, -1
bne x1, x0, loop
addi x21, x0, 1088
sw x10, 0(x21)
ebreak
.org 1024
.word 7, -3, 12, 0, 19, 2
