# Overflow wraps; compare signed and unsigned, shift, combine bits.
lui x1, 0x80000
addi x2, x0, -1
add x3, x1, x1
sub x4, x0, x2
slt x5, x1, x2
sltu x6, x1, x2
slli x7, x4, 7
srai x8, x1, 31
xor x9, x7, x2
andi x10, x9, 255
addi x20, x0, 1024
sw x10, 0(x20)
fence
ebreak
.org 1024
.word 0
