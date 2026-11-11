/* Zero-dependency cross-platform launcher and first-run BMPT v1 delta patcher
 * for Brutal Mario Native PC Public Beta (Linux x86_64 & Windows x64).
 *
 * Links only standard C runtime (+ kernel32/user32/shell32 on Windows) and
 * sha256.c. Anchors cwd to the package root using UTF-16 Win32 APIs on Windows
 * so relative paths ("data/rom.sfc", "data/packs/...", "saves/save.srm") work
 * even when extracted into directories containing non-ASCII characters.
 */
#ifndef _WIN32
#  define _POSIX_C_SOURCE 200809L
#endif
#include "sha256.h"

#include <errno.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#ifdef _WIN32
#  define WIN32_LEAN_AND_MEAN
#  include <windows.h>
#  include <shellapi.h>
#  include <direct.h>
#  include <process.h>
#  include <sys/stat.h>
#else
#  include <dirent.h>
#  include <sys/stat.h>
#  include <sys/types.h>
#  include <unistd.h>
#endif

#define MAX_MANIFEST_ENTRIES 128
#define PATCH_REL_PATH "patch/brutalmario.bmpatch"
#define MANIFEST_REL_PATH "config/packs.manifest"

typedef struct {
    char var[64];
    char rel_path[256];
    uint32_t size;
    uint8_t sha256[32];
} ManifestEntry;

static uint16_t read_u16_le(const uint8_t *p) {
    return (uint16_t)p[0] | ((uint16_t)p[1] << 8);
}

static uint32_t read_u32_le(const uint8_t *p) {
    return (uint32_t)p[0] | ((uint32_t)p[1] << 8) |
           ((uint32_t)p[2] << 16) | ((uint32_t)p[3] << 24);
}

static int hex_val(char c) {
    if (c >= '0' && c <= '9') return c - '0';
    if (c >= 'a' && c <= 'f') return c - 'a' + 10;
    if (c >= 'A' && c <= 'F') return c - 'A' + 10;
    return -1;
}

static int parse_hex32(const char *s, uint8_t out[32]) {
    for (int i = 0; i < 32; ++i) {
        int hi = hex_val(s[i * 2]);
        int lo = hex_val(s[i * 2 + 1]);
        if (hi < 0 || lo < 0) return 0;
        out[i] = (uint8_t)((hi << 4) | lo);
    }
    return 1;
}

static void format_hex32(const uint8_t in[32], char out[65]) {
    static const char hex[] = "0123456789abcdef";
    for (int i = 0; i < 32; ++i) {
        out[i * 2] = hex[in[i] >> 4];
        out[i * 2 + 1] = hex[in[i] & 0x0f];
    }
    out[64] = '\0';
}

static void make_dir(const char *rel) {
#ifdef _WIN32
    _mkdir(rel);
#else
    mkdir(rel, 0755);
#endif
}

static void show_error_dialog(const char *utf8_msg) {
    fprintf(stderr, "\n%s\n", utf8_msg);
#ifdef _WIN32
    const char *no_box = getenv("BM_NO_MSGBOX");
    if (no_box && no_box[0] && strcmp(no_box, "0") != 0) return;
    wchar_t wmsg[2048];
    if (MultiByteToWideChar(CP_UTF8, 0, utf8_msg, -1, wmsg, 2048) > 0) {
        MessageBoxW(NULL, wmsg, L"Brutal Mario Native PC - 初始化提示 / Setup", MB_OK | MB_ICONINFORMATION);
    }
#endif
}

static int anchor_to_package_root(void) {
#ifdef _WIN32
    wchar_t wexe[4096];
    DWORD n = GetModuleFileNameW(NULL, wexe, 4096);
    if (n == 0 || n >= 4096) return 0;
    wchar_t *slash = NULL;
    for (wchar_t *p = wexe; *p; ++p) {
        if (*p == L'\\' || *p == L'/') slash = p;
    }
    if (!slash) return 0;
    *slash = L'\0';
    size_t len = wcslen(wexe);
    if (len >= 4) {
        wchar_t *tail = wexe + len - 4;
        if ((tail[0] == L'\\' || tail[0] == L'/') &&
            (tail[1] == L'b' || tail[1] == L'B') &&
            (tail[2] == L'i' || tail[2] == L'I') &&
            (tail[3] == L'n' || tail[3] == L'N')) {
            *tail = L'\0';
        }
    }
    return SetCurrentDirectoryW(wexe) ? 1 : 0;
#else
    char exe[4096];
    ssize_t n = readlink("/proc/self/exe", exe, sizeof(exe) - 1);
    if (n <= 0) return 0;
    exe[n] = '\0';
    char *slash = strrchr(exe, '/');
    if (!slash) return 0;
    *slash = '\0';
    size_t len = strlen(exe);
    if (len >= 4 && strcmp(exe + len - 4, "/bin") == 0) {
        exe[len - 4] = '\0';
    }
    return chdir(exe) == 0 ? 1 : 0;
#endif
}

static int read_entire_file(const char *path, uint8_t **out_buf, size_t *out_size) {
    FILE *f = fopen(path, "rb");
    if (!f) return 0;
    if (fseek(f, 0, SEEK_END) != 0) { fclose(f); return 0; }
    long sz = ftell(f);
    if (sz < 0) { fclose(f); return 0; }
    if (fseek(f, 0, SEEK_SET) != 0) { fclose(f); return 0; }
    uint8_t *buf = (uint8_t *)malloc((size_t)sz + 1);
    if (!buf) { fclose(f); return 0; }
    size_t got = sz > 0 ? fread(buf, 1, (size_t)sz, f) : 0;
    fclose(f);
    if (got != (size_t)sz) { free(buf); return 0; }
    *out_buf = buf;
    *out_size = (size_t)sz;
    return 1;
}

static int load_manifest(ManifestEntry *entries, int max_entries) {
    FILE *f = fopen(MANIFEST_REL_PATH, "rb");
    if (!f) return -1;
    char line[512];
    int count = 0;
    while (fgets(line, sizeof(line), f)) {
        size_t l = strlen(line);
        while (l > 0 && (line[l - 1] == '\n' || line[l - 1] == '\r')) line[--l] = '\0';
        if (l == 0 || line[0] == '#') continue;
        if (count >= max_entries) { fclose(f); return -1; }
        char *tab1 = strchr(line, '\t');
        if (!tab1) { fclose(f); return -1; }
        *tab1 = '\0';
        char *tab2 = strchr(tab1 + 1, '\t');
        if (!tab2) { fclose(f); return -1; }
        *tab2 = '\0';
        char *tab3 = strchr(tab2 + 1, '\t');
        if (!tab3) { fclose(f); return -1; }
        *tab3 = '\0';

        ManifestEntry *e = &entries[count];
        snprintf(e->var, sizeof(e->var), "%s", line);
        snprintf(e->rel_path, sizeof(e->rel_path), "%s", tab1 + 1);
        e->size = (uint32_t)strtoul(tab2 + 1, NULL, 10);
        if (strlen(tab3 + 1) != 64 || !parse_hex32(tab3 + 1, e->sha256)) {
            fclose(f);
            return -1;
        }
        ++count;
    }
    fclose(f);
    return count;
}

static int verify_manifest_files(const ManifestEntry *entries, int count, int check_sha) {
    for (int i = 0; i < count; ++i) {
        FILE *f = fopen(entries[i].rel_path, "rb");
        if (!f) return 0;
        if (fseek(f, 0, SEEK_END) != 0) { fclose(f); return 0; }
        long sz = ftell(f);
        fclose(f);
        if (sz < 0 || (uint32_t)sz != entries[i].size) return 0;
        if (check_sha) {
            uint8_t *buf = NULL;
            size_t bsz = 0;
            if (!read_entire_file(entries[i].rel_path, &buf, &bsz)) return 0;
            uint8_t actual[32];
            sha256_compute(buf, bsz, actual);
            free(buf);
            if (memcmp(actual, entries[i].sha256, 32) != 0) return 0;
        }
    }
    return 1;
}

static int check_base_candidate_bytes(const uint8_t *raw, size_t sz,
                                      uint32_t expected_size, const uint8_t expected_sha[32],
                                      uint8_t **out_base) {
    const uint8_t *body = raw;
    if (sz == (size_t)expected_size + 512) {
        body = raw + 512;
        sz = expected_size;
    }
    if (sz != expected_size) return 0;
    uint8_t digest[32];
    sha256_compute(body, sz, digest);
    if (memcmp(digest, expected_sha, 32) != 0) return 0;
    uint8_t *copy = (uint8_t *)malloc(expected_size);
    if (!copy) return 0;
    memcpy(copy, body, expected_size);
    *out_base = copy;
    return 1;
}

static int has_rom_extension(const char *name) {
    size_t len = strlen(name);
    if (len < 4) return 0;
    const char *ext = name + len - 4;
    if (ext[0] != '.') return 0;
    char e1 = ext[1] >= 'A' && ext[1] <= 'Z' ? (char)(ext[1] + 32) : ext[1];
    char e2 = ext[2] >= 'A' && ext[2] <= 'Z' ? (char)(ext[2] + 32) : ext[2];
    char e3 = ext[3] >= 'A' && ext[3] <= 'Z' ? (char)(ext[3] + 32) : ext[3];
    return (e1 == 's' && (e2 == 'f' || e2 == 'm') && e3 == 'c');
}

static int find_vanilla_smw_rom(int argc, char **argv,
                                uint32_t expected_size, const uint8_t expected_sha[32],
                                uint8_t **out_base, char *rejected_hint, size_t hint_cap) {
    rejected_hint[0] = '\0';
#ifdef _WIN32
    /* 1. Check wide CLI arguments (supports drag-and-drop with Unicode paths) */
    int wargc = 0;
    LPWSTR *wargv = CommandLineToArgvW(GetCommandLineW(), &wargc);
    if (wargv) {
        for (int i = 1; i < wargc; ++i) {
            if (wargv[i][0] == L'-') continue;
            FILE *wf = _wfopen(wargv[i], L"rb");
            if (!wf) continue;
            fseek(wf, 0, SEEK_END);
            long sz = ftell(wf);
            fseek(wf, 0, SEEK_SET);
            if (sz == (long)expected_size || sz == (long)expected_size + 512) {
                uint8_t *buf = (uint8_t *)malloc((size_t)sz);
                if (buf && fread(buf, 1, (size_t)sz, wf) == (size_t)sz) {
                    if (check_base_candidate_bytes(buf, (size_t)sz, expected_size, expected_sha, out_base)) {
                        free(buf);
                        fclose(wf);
                        LocalFree(wargv);
                        return 1;
                    }
                }
                free(buf);
            }
            char utf8_name[512];
            WideCharToMultiByte(CP_UTF8, 0, wargv[i], -1, utf8_name, sizeof(utf8_name), NULL, NULL);
            snprintf(rejected_hint, hint_cap, "%s (%ld bytes)", utf8_name, sz);
            fclose(wf);
        }
        LocalFree(wargv);
    }

    /* 2. Scan package root and optional rom/ subfolder */
    const wchar_t *patterns[] = { L"*", L"rom\\*", L"roms\\*" };
    const wchar_t *prefixes[] = { L"", L"rom\\", L"roms\\" };
    for (int d = 0; d < 3; ++d) {
        WIN32_FIND_DATAW ffd;
        HANDLE h = FindFirstFileW(patterns[d], &ffd);
        if (h == INVALID_HANDLE_VALUE) continue;
        do {
            if (ffd.dwFileAttributes & FILE_ATTRIBUTE_DIRECTORY) continue;
            ULONGLONG fsz = ((ULONGLONG)ffd.nFileSizeHigh << 32) | ffd.nFileSizeLow;
            char utf8_name[512];
            WideCharToMultiByte(CP_UTF8, 0, ffd.cFileName, -1, utf8_name, sizeof(utf8_name), NULL, NULL);
            if (fsz == expected_size || fsz == (ULONGLONG)expected_size + 512) {
                wchar_t wfull[1024];
                _snwprintf(wfull, 1024, L"%ls%ls", prefixes[d], ffd.cFileName);
                FILE *wf = _wfopen(wfull, L"rb");
                if (wf) {
                    uint8_t *buf = (uint8_t *)malloc((size_t)fsz);
                    if (buf && fread(buf, 1, (size_t)fsz, wf) == (size_t)fsz) {
                        if (check_base_candidate_bytes(buf, (size_t)fsz, expected_size, expected_sha, out_base)) {
                            free(buf);
                            fclose(wf);
                            FindClose(h);
                            return 1;
                        }
                    }
                    free(buf);
                    fclose(wf);
                }
                if (!rejected_hint[0]) {
                    snprintf(rejected_hint, hint_cap, "%s (%llu bytes, SHA-256 mismatch)",
                             utf8_name, (unsigned long long)fsz);
                }
            } else if (has_rom_extension(utf8_name) && !rejected_hint[0]) {
                snprintf(rejected_hint, hint_cap, "%s (%llu bytes)",
                         utf8_name, (unsigned long long)fsz);
            }
        } while (FindNextFileW(h, &ffd));
        FindClose(h);
    }
    (void)argc;
    (void)argv;
#else
    for (int i = 1; i < argc; ++i) {
        if (argv[i][0] == '-') continue;
        uint8_t *buf = NULL;
        size_t sz = 0;
        if (read_entire_file(argv[i], &buf, &sz)) {
            if (check_base_candidate_bytes(buf, sz, expected_size, expected_sha, out_base)) {
                free(buf);
                return 1;
            }
            snprintf(rejected_hint, hint_cap, "%.240s (%zu bytes)", argv[i], sz);
            free(buf);
        }
    }
    const char *dirs[] = { ".", "rom", "roms" };
    for (int d = 0; d < 3; ++d) {
        DIR *dp = opendir(dirs[d]);
        if (!dp) continue;
        struct dirent *de;
        while ((de = readdir(dp)) != NULL) {
            if (de->d_name[0] == '.') continue;
            char full[1024];
            if (strcmp(dirs[d], ".") == 0)
                snprintf(full, sizeof(full), "%s", de->d_name);
            else
                snprintf(full, sizeof(full), "%s/%s", dirs[d], de->d_name);
            struct stat st;
            if (stat(full, &st) != 0 || !S_ISREG(st.st_mode)) continue;
            if ((size_t)st.st_size == expected_size || (size_t)st.st_size == (size_t)expected_size + 512) {
                uint8_t *buf = NULL;
                size_t sz = 0;
                if (read_entire_file(full, &buf, &sz)) {
                    if (check_base_candidate_bytes(buf, sz, expected_size, expected_sha, out_base)) {
                        free(buf);
                        closedir(dp);
                        return 1;
                    }
                    free(buf);
                }
                if (!rejected_hint[0]) {
                    snprintf(rejected_hint, hint_cap, "%.240s (%lld bytes, SHA-256 mismatch)",
                             full, (long long)st.st_size);
                }
            } else if (has_rom_extension(de->d_name) && !rejected_hint[0]) {
                snprintf(rejected_hint, hint_cap, "%.240s (%lld bytes)", full, (long long)st.st_size);
            }
        }
        closedir(dp);
    }
#endif
    return 0;
}

static int run_first_time_setup(int argc, char **argv) {
    uint8_t *patch = NULL;
    size_t patch_sz = 0;
    if (!read_entire_file(PATCH_REL_PATH, &patch, &patch_sz) || patch_sz < 80) {
        free(patch);
        show_error_dialog("错误：未找到补丁文件 " PATCH_REL_PATH "，请确保已完整解压整个压缩包！\n"
                          "Error: Missing or truncated " PATCH_REL_PATH ". Extract the entire archive first.");
        return 0;
    }
    uint8_t body_sha[32];
    sha256_compute(patch, patch_sz - 32, body_sha);
    if (memcmp(body_sha, patch + patch_sz - 32, 32) != 0 ||
        memcmp(patch, "BMPT\x01\x00\x00\x00", 8) != 0) {
        free(patch);
        show_error_dialog("错误：补丁文件校验失败（文件可能损坏），请重新解压压缩包。\n"
                          "Error: Patch file integrity check failed.");
        return 0;
    }

    uint32_t expected_base_size = read_u32_le(patch + 8);
    const uint8_t *expected_base_sha = patch + 12;
    uint32_t file_count = read_u32_le(patch + 44);
    size_t cursor = 48;
    size_t body_end = patch_sz - 32;

    uint8_t *base = NULL;
    char rejected_hint[600];
    if (!find_vanilla_smw_rom(argc, argv, expected_base_size, expected_base_sha,
                              &base, rejected_hint, sizeof(rejected_hint))) {
        char sha_hex[65];
        format_hex32(expected_base_sha, sha_hex);
        char msg[1800];
        snprintf(msg, sizeof(msg),
            "【首次运行初始化 / First-Time Setup】\n\n"
            "本发布包不包含任天堂原版 ROM。请将一份美版原版《Super Mario World (U) [!]》ROM 放入当前游戏根目录，然后重新启动即可自动合成全部游戏资源（仅首次需要，耗时不到 1 秒）：\n\n"
            "  • 支持文件名：任意名称（.sfc 或 .smc 均可）\n"
            "  • 支持大小：524,288 字节（无头）或 524,800 字节（带 512 字节头）\n"
            "  • 无头 SHA-256：%s\n"
            "%s%s\n"
            "Place an unmodified US 'Super Mario World (U) [!]' ROM (.sfc or .smc, 512 KB) into this folder and launch again.",
            sha_hex,
            rejected_hint[0] ? "\n  [已跳过不匹配文件 / Skipped non-matching file]: " : "",
            rejected_hint);
        free(patch);
        show_error_dialog(msg);
        return 0;
    }

    printf("[Setup] Found valid Super Mario World (U) [!]. Synthesizing %u game files...\n", file_count);
    make_dir("data");
    make_dir("data/packs");
    make_dir("saves");

    for (uint32_t f = 0; f < file_count; ++f) {
        if (cursor + 2 > body_end) { free(base); free(patch); return 0; }
        uint16_t path_len = read_u16_le(patch + cursor);
        cursor += 2;
        if (path_len == 0 || path_len >= 250 || cursor + path_len + 40 > body_end) {
            free(base); free(patch); return 0;
        }
        char rel_path[256];
        memcpy(rel_path, patch + cursor, path_len);
        rel_path[path_len] = '\0';
        cursor += path_len;
        /* Disallow path traversal */
        if (strstr(rel_path, "..") != NULL || rel_path[0] == '/' || rel_path[0] == '\\') {
            free(base); free(patch); return 0;
        }
        uint32_t out_size = read_u32_le(patch + cursor);
        cursor += 4;
        const uint8_t *expected_out_sha = patch + cursor;
        cursor += 32;
        uint32_t op_count = read_u32_le(patch + cursor);
        cursor += 4;

        uint8_t *out_buf = (uint8_t *)malloc(out_size ? out_size : 1);
        if (!out_buf) { free(base); free(patch); return 0; }
        size_t pos = 0;

        for (uint32_t op = 0; op < op_count; ++op) {
            if (cursor >= body_end) { free(out_buf); free(base); free(patch); return 0; }
            uint8_t kind = patch[cursor++];
            if (kind == 1) { /* OP_COPY */
                if (cursor + 8 > body_end) { free(out_buf); free(base); free(patch); return 0; }
                uint32_t src_off = read_u32_le(patch + cursor);
                uint32_t len = read_u32_le(patch + cursor + 4);
                cursor += 8;
                if (src_off + len > expected_base_size || pos + len > out_size) {
                    free(out_buf); free(base); free(patch); return 0;
                }
                memcpy(out_buf + pos, base + src_off, len);
                pos += len;
            } else if (kind == 2) { /* OP_ZERO */
                if (cursor + 4 > body_end) { free(out_buf); free(base); free(patch); return 0; }
                uint32_t len = read_u32_le(patch + cursor);
                cursor += 4;
                if (pos + len > out_size) { free(out_buf); free(base); free(patch); return 0; }
                memset(out_buf + pos, 0, len);
                pos += len;
            } else if (kind == 3) { /* OP_LITERAL */
                if (cursor + 4 > body_end) { free(out_buf); free(base); free(patch); return 0; }
                uint32_t len = read_u32_le(patch + cursor);
                cursor += 4;
                if (cursor + len > body_end || pos + len > out_size) {
                    free(out_buf); free(base); free(patch); return 0;
                }
                memcpy(out_buf + pos, patch + cursor, len);
                cursor += len;
                pos += len;
            } else {
                free(out_buf); free(base); free(patch); return 0;
            }
        }

        if (pos != out_size) { free(out_buf); free(base); free(patch); return 0; }
        uint8_t actual_sha[32];
        sha256_compute(out_buf, out_size, actual_sha);
        if (memcmp(actual_sha, expected_out_sha, 32) != 0) {
            free(out_buf); free(base); free(patch);
            show_error_dialog("错误：合成文件哈希校验不匹配！\nError: Synthesized file SHA-256 mismatch!");
            return 0;
        }

        FILE *outf = fopen(rel_path, "wb");
        if (!outf || (out_size > 0 && fwrite(out_buf, 1, out_size, outf) != out_size)) {
            if (outf) fclose(outf);
            free(out_buf); free(base); free(patch);
            show_error_dialog("错误：无法写入合成文件，请检查目录写入权限。\nError: Failed to write synthesized game asset.");
            return 0;
        }
        fclose(outf);
        free(out_buf);
    }

    free(base);
    free(patch);
    printf("[Setup] Successfully synthesized and verified all %u files!\n", file_count);
    return 1;
}

static void backup_save_before_cheat(void) {
    const char *cur = "saves/save.srm";
    const char *bak = "saves/save.srm.before-cheat";
    FILE *f = fopen(cur, "rb");
    if (!f) return;
    fclose(f);
    remove(bak);
    if (rename(cur, bak) == 0) {
        printf("[Cheat] Backed up existing save to %s\n", bak);
    }
}

static void set_env_kv(const char *k, const char *v, int overwrite) {
    if (!overwrite) {
        const char *existing = getenv(k);
        if (existing && existing[0]) return;
    }
#ifdef _WIN32
    _putenv_s(k, v);
#else
    setenv(k, v, overwrite);
#endif
}

#ifdef _WIN32
static char *win_quote_arg(const char *arg) {
    int need_quotes = (arg[0] == '\0' || strchr(arg, ' ') != NULL || strchr(arg, '\t') != NULL);
    size_t len = strlen(arg);
    char *out = (char *)malloc(len * 2 + 4);
    size_t pos = 0;
    if (need_quotes) out[pos++] = '"';
    for (size_t i = 0; i < len; ++i) {
        if (arg[i] == '"') out[pos++] = '\\';
        out[pos++] = arg[i];
    }
    if (need_quotes) out[pos++] = '"';
    out[pos] = '\0';
    return out;
}
#endif

int main(int argc, char **argv) {
#ifdef _WIN32
    SetConsoleOutputCP(CP_UTF8);
#endif
    if (!anchor_to_package_root()) {
        show_error_dialog("Error: Could not resolve package root directory.");
        return 1;
    }

    int setup_only = 0;
    int verify_only = 0;
    int special_zone = 0;
    int complete_all = 0;
    const char *extra_args[128];
    int extra_count = 0;

    for (int i = 1; i < argc; ++i) {
        if (strcmp(argv[i], "--setup-only") == 0) {
            setup_only = 1;
        } else if (strcmp(argv[i], "--verify") == 0) {
            verify_only = 1;
        } else if (strcmp(argv[i], "--special-zone") == 0 || strcmp(argv[i], "-s") == 0) {
            special_zone = 1;
        } else if (strcmp(argv[i], "--complete-all") == 0 || strcmp(argv[i], "-c") == 0) {
            complete_all = 1;
        } else if (has_rom_extension(argv[i]) && argv[i][0] != '-') {
            /* Dragged-and-dropped ROM path handled by find_vanilla_smw_rom */
            continue;
        } else if (extra_count < 120) {
            extra_args[extra_count++] = argv[i];
        }
    }

    ManifestEntry entries[MAX_MANIFEST_ENTRIES];
    int entry_count = load_manifest(entries, MAX_MANIFEST_ENTRIES);
    if (entry_count <= 0) {
        show_error_dialog("Error: Missing or invalid " MANIFEST_REL_PATH ".");
        return 1;
    }

    if (verify_only) {
        if (!verify_manifest_files(entries, entry_count, 1)) {
            fprintf(stderr, "[Verify] FAILED: missing or corrupted game assets.\n");
            return 1;
        }
        printf("[Verify] OK: all %d manifest entries match size and SHA-256.\n", entry_count);
        return 0;
    }

    if (!verify_manifest_files(entries, entry_count, 0)) {
        if (!run_first_time_setup(argc, argv)) {
            return 2;
        }
        if (!verify_manifest_files(entries, entry_count, 1)) {
            show_error_dialog("Error: Post-setup verification failed.");
            return 1;
        }
    }

    if (setup_only) {
        if (!verify_manifest_files(entries, entry_count, 1)) {
            fprintf(stderr, "[Setup] Verification failed.\n");
            return 1;
        }
        printf("[Setup] Ready (%d verified entries).\n", entry_count);
        return 0;
    }

    make_dir("saves");
    const char *cheat_script = NULL;
    if (special_zone) {
        backup_save_before_cheat();
        cheat_script = "scripts/cheat-special-zone.script";
    } else if (complete_all) {
        backup_save_before_cheat();
        cheat_script = "scripts/cheat-complete-all.script";
    }

    int pack_count = 0;
    for (int i = 0; i < entry_count; ++i) {
        if (strcmp(entries[i].var, "ROM") == 0) continue;
        set_env_kv(entries[i].var, entries[i].rel_path, 1);
        ++pack_count;
    }
    set_env_kv("SNESRECOMP_APU_MASTER_CLOCK", "1", 0);
    set_env_kv("SNESRECOMP_REWIND", "0", 0);

#ifdef _WIN32
    const char *game_bin = "bin\\BrutalMario.exe";
#else
    const char *game_bin = "bin/BrutalMario";
#endif

    const char *raw_argv[140];
    int n = 0;
    raw_argv[n++] = game_bin;
    raw_argv[n++] = "--no-launcher";
    raw_argv[n++] = "--config";
    raw_argv[n++] = "config/config.ini";
    raw_argv[n++] = "--rom";
    raw_argv[n++] = "data/rom.sfc";
    if (cheat_script) {
        raw_argv[n++] = "--script";
        raw_argv[n++] = cheat_script;
    }
    for (int i = 0; i < extra_count; ++i) {
        raw_argv[n++] = extra_args[i];
    }
    raw_argv[n] = NULL;

    printf("[Launcher] Mounted %d native content packs. Starting game...\n", pack_count);
    fflush(stdout);

#ifdef _WIN32
    char *quoted_argv[140];
    for (int i = 0; i < n; ++i) quoted_argv[i] = win_quote_arg(raw_argv[i]);
    quoted_argv[n] = NULL;
    int rc = (int)_spawnv(_P_WAIT, game_bin, (const char *const *)quoted_argv);
    for (int i = 0; i < n; ++i) free(quoted_argv[i]);
    if (rc < 0) {
        show_error_dialog("Error: Failed to launch bin\\BrutalMario.exe.");
        return 1;
    }
    return rc;
#else
    execv(game_bin, (char *const *)raw_argv);
    perror("execv(bin/BrutalMario) failed");
    return 1;
#endif
}
