# Store the first 12 Fibonacci numbers at 0x400.
addi x1, x0, 0
addi x2, x0, 1
addi x3, x0, 12
addi x20, x0, 1024
loop:
sw x1, 0(x20)
add x4, x1, x2
addi x1, x2, 0
addi x2, x4, 0
addi x20, x20, 4
addi x3, x3, -1
bne x3, x0, loop
ebreak
.org 1024
.word 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0
