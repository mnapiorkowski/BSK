// Note: I am not the author of this code - it was provided as a part of the task.

// gcc -Wall -Wextra -Werror -std=c11 -static -o decompress_easier decompress.c
// gcc -Wall -Wextra -Werror -std=c11 -static-pie -o decompress decompress.c
#define _GNU_SOURCE
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

struct cmd {
    uint16_t length;
    uint16_t dist;
};

static void readn(unsigned char *buf, size_t len) {
    while (len) {
        ssize_t num_read;
        if ((num_read = read(STDIN_FILENO, buf, len)) <= 0) {
            fprintf(stderr, "Read error :c\n");
            exit(1);
        }

        buf += num_read;
        len -= num_read;
    }
}

int main() {
    setlinebuf(stdout);
    puts("Very Cool Decompressor v0.1");

    uint8_t buf[1024] = {0};
    uint8_t *bufpos = buf;

    struct cmd cmd;
    for (;;) {
        readn((unsigned char*)&cmd, sizeof(cmd));
        if (cmd.length == 0) break;
        if (cmd.dist) {
            uint8_t *src = bufpos - cmd.dist;
            for (size_t i = 0; i < cmd.length; i++) {
                *bufpos++ = *src++;
            }
        } else {
            readn(bufpos, cmd.length);
            bufpos += cmd.length;
        }
    }

    write(STDOUT_FILENO, buf, bufpos - buf);

    return 0;
}
