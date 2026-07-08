#include "utf8.h"

namespace utf8 {

size_t decode(const char* s, uint32_t& cp) {
    if (!s || !(*s)) {
        cp = 0;
        return 0;
    }

    unsigned char c0 = static_cast<unsigned char>(s[0]);

    if (c0 < 0x80) {
        cp = c0;
        return 1;
    }

    if ((c0 & 0xE0) == 0xC0) {
        if (!(s[1] && (static_cast<unsigned char>(s[1]) & 0xC0) == 0x80)) {
            cp = 0;
            return 0;
        }
        cp = ((c0 & 0x1F) << 6) | (static_cast<unsigned char>(s[1]) & 0x3F);
        return 2;
    }

    if ((c0 & 0xF0) == 0xE0) {
        if (!(s[1] && (static_cast<unsigned char>(s[1]) & 0xC0) == 0x80 &&
              s[2] && (static_cast<unsigned char>(s[2]) & 0xC0) == 0x80)) {
            cp = 0;
            return 0;
        }
        cp = ((c0 & 0x0F) << 12) |
             ((static_cast<unsigned char>(s[1]) & 0x3F) << 6) |
             (static_cast<unsigned char>(s[2]) & 0x3F);
        return 3;
    }

    if ((c0 & 0xF8) == 0xF0) {
        if (!(s[1] && (static_cast<unsigned char>(s[1]) & 0xC0) == 0x80 &&
              s[2] && (static_cast<unsigned char>(s[2]) & 0xC0) == 0x80 &&
              s[3] && (static_cast<unsigned char>(s[3]) & 0xC0) == 0x80)) {
            cp = 0;
            return 0;
        }
        cp = ((c0 & 0x07) << 18) |
             ((static_cast<unsigned char>(s[1]) & 0x3F) << 12) |
             ((static_cast<unsigned char>(s[2]) & 0x3F) << 6) |
             (static_cast<unsigned char>(s[3]) & 0x3F);
        return 4;
    }

    cp = 0;
    return 0;
}

size_t encode(uint32_t cp, char* buf) {
    if (cp < 0x80) {
        buf[0] = static_cast<char>(cp);
        return 1;
    }
    if (cp < 0x800) {
        buf[0] = static_cast<char>(0xC0 | (cp >> 6));
        buf[1] = static_cast<char>(0x80 | (cp & 0x3F));
        return 2;
    }
    if (cp < 0x10000) {
        buf[0] = static_cast<char>(0xE0 | (cp >> 12));
        buf[1] = static_cast<char>(0x80 | ((cp >> 6) & 0x3F));
        buf[2] = static_cast<char>(0x80 | (cp & 0x3F));
        return 3;
    }
    if (cp <= 0x10FFFF) {
        buf[0] = static_cast<char>(0xF0 | (cp >> 18));
        buf[1] = static_cast<char>(0x80 | ((cp >> 12) & 0x3F));
        buf[2] = static_cast<char>(0x80 | ((cp >> 6) & 0x3F));
        buf[3] = static_cast<char>(0x80 | (cp & 0x3F));
        return 4;
    }
    return 0;
}

uint32_t next_cp(const std::string& s, size_t& pos) {
    if (pos >= s.size()) {
        return 0;
    }
    uint32_t cp;
    size_t n = decode(s.c_str() + pos, cp);
    if (n == 0) {
        cp = 0;
        n = 1;
    }
    pos += n;
    return cp;
}

size_t count_codepoints(const std::string& s, size_t byte_len) {
    size_t count = 0;
    size_t pos = 0;
    while (pos < byte_len) {
        uint32_t cp;
        size_t n = decode(s.c_str() + pos, cp);
        if (n == 0) {
            n = 1;
        }
        pos += n;
        ++count;
    }
    return count;
}

bool is_cyrillic(uint32_t cp) {
    return (cp >= 0x0400 && cp <= 0x04FF) ||
           (cp >= 0x0500 && cp <= 0x052F) ||
           (cp >= 0x2DE0 && cp <= 0x2DFF) ||
           (cp >= 0xA640 && cp <= 0xA69F);
}

bool is_runic(uint32_t cp) {
    return cp >= 0x16A0 && cp <= 0x16FF;
}

bool is_id_start(uint32_t cp) {
    if (cp == '_') return true;
    if (cp >= 'a' && cp <= 'z') return true;
    if (cp >= 'A' && cp <= 'Z') return true;
    if (is_cyrillic(cp)) return true;
    if (is_runic(cp)) return true;
    if (cp >= 0x0400 && cp <= 0x04FF) return true;
    if (cp >= 0x0500 && cp <= 0x052F) return true;
    return false;
}

bool is_id_continue(uint32_t cp) {
    if (cp >= '0' && cp <= '9') return true;
    return is_id_start(cp);
}

} // namespace utf8
