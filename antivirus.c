#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <dirent.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <unistd.h>

#define MAX_SIGNATURES 3
#define MAX_FILENAME 1024  // Increased buffer size to handle long paths and filenames

// Example malware signatures (just simple patterns)
unsigned char *signatures[MAX_SIGNATURES] = {
    (unsigned char *)"\x4D\x5A\x90\x00", // Example signature 1: MZ header (Windows executable)
    (unsigned char *)"\x7F\x45\x4C\x46", // Example signature 2: ELF header (Linux executable)
    (unsigned char *)"\x50\x4B\x03\x04", // Example signature 3: ZIP header
};

// Function to scan a file for malicious signatures
int scan_file(FILE *file) {
    unsigned char buffer[1024];
    size_t bytesRead;
    int found = 0;

    while ((bytesRead = fread(buffer, 1, sizeof(buffer), file)) > 0) {
        for (int i = 0; i < MAX_SIGNATURES; i++) {
            if (memcmp(buffer, signatures[i], strlen((char *)signatures[i])) == 0) {
                found = 1;
                break;
            }
        }
        if (found) break;
    }

    return found;
}

// Function to scan a directory for files
void scan_directory(const char *dirPath) {
    DIR *dir = opendir(dirPath);
    if (dir == NULL) {
        perror("Failed to open directory");
        return;
    }

    struct dirent *entry;
    while ((entry = readdir(dir)) != NULL) {
        if (entry->d_type == DT_REG) {  // If it's a regular file
            char filePath[MAX_FILENAME];  // Increased buffer size to handle longer file paths

            // Check the combined length of dirPath and entry->d_name
            if (strlen(dirPath) + strlen(entry->d_name) + 1 < sizeof(filePath)) {
                snprintf(filePath, sizeof(filePath), "%s/%s", dirPath, entry->d_name);
            } else {
                fprintf(stderr, "Warning: File path is too long, skipping file: %s/%s\n", dirPath, entry->d_name);
                continue;  // Skip file if path is too long
            }

            FILE *file = fopen(filePath, "rb");
            if (file == NULL) {
                perror("Failed to open file");
                continue;
            }

            if (scan_file(file)) {
                printf("Malware found: %s\n", filePath);
            }

            fclose(file);
        } else if (entry->d_type == DT_DIR && strcmp(entry->d_name, ".") != 0 && strcmp(entry->d_name, "..") != 0) {
            char subDirPath[MAX_FILENAME];  // Increased buffer size for subdirectory paths

            // Check the combined length of dirPath and entry->d_name
            if (strlen(dirPath) + strlen(entry->d_name) + 1 < sizeof(subDirPath)) {
                snprintf(subDirPath, sizeof(subDirPath), "%s/%s", dirPath, entry->d_name);
                scan_directory(subDirPath);  // Recursively scan subdirectories
            } else {
                fprintf(stderr, "Warning: Subdirectory path is too long, skipping: %s/%s\n", dirPath, entry->d_name);
            }
        }
    }

    closedir(dir);
}

int main() {
    const char *dirToScan = ".";  // Current directory

    printf("Starting antivirus scan...\n");
    scan_directory(dirToScan);
    printf("Scan completed.\n");

    return 0;
}
