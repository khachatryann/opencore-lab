# Linear search for 19. x10 receives its index (4), or -1 if absent.
addi x20, x0, 1024
addi x1, x0, 6
addi x2, x0, 19
addi x3, x0, 0
addi x10, x0, -1
loop:
beq x3, x1, done
lw x4, 0(x20)
beq x4, x2, found
addi x20, x20, 4
addi x3, x3, 1
jal x0, loop
found:
addi x10, x3, 0
done:
ebreak
.org 1024
.word 7, -3, 12, 0, 19, 2
