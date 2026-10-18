# Bubble sort six signed words in place. Expected: -3,0,2,7,12,19.
addi x1, x0, 5
outer:
addi x20, x0, 1024
addi x2, x1, 0
inner:
lw x3, 0(x20)
lw x4, 4(x20)
bge x4, x3, ordered
sw x4, 0(x20)
sw x3, 4(x20)
ordered:
addi x20, x20, 4
addi x2, x2, -1
bne x2, x0, inner
addi x1, x1, -1
bne x1, x0, outer
ebreak
.org 1024
.word 7, -3, 12, 0, 19, 2
