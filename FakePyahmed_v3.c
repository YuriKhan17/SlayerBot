#include <stdio.h>
#include <stdlib.h>

__attribute__((constructor))
void init() {
    FILE *log = fopen("spyblade_log.txt", "a");
    if (log) {
        fprintf(log, "[!] Demon triggered Pyahmed.so trap!\n");
        fprintf(log, "Timestamp: %ld\n", time(NULL));
        fclose(log);
    }
}
