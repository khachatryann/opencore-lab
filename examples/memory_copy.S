# Copy 16 bytes from 0x400 to 0x440, including high-bit byte values.
addi x20, x0, 1024
addi x21, x0, 1088
addi x1, x0, 16
loop:
lbu x2, 0(x20)
sb x2, 0(x21)
addi x20, x20, 1
addi x21, x21, 1
addi x1, x1, -1
bne x1, x0, loop
ebreak
.org 1024
.byte 0, 1, 127, 128, 255, 42, 65, 66, 67, 200, 3, 4, 5, 6, 7, 8
