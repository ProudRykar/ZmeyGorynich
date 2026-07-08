#pragma once

#include <cstdint>
#include <string>

namespace utf8 {

// Decode single UTF-8 codepoint from byte string.
// Returns number of bytes consumed (1-4), or 0 on error.
// Sets cp to the decoded codepoint.
size_t decode(const char* s, uint32_t& cp);

// Encode a codepoint into UTF-8 byte sequence.
// Returns number of bytes written (1-4).
// buf must have space for at least 4 bytes.
size_t encode(uint32_t cp, char* buf);

// Get next codepoint from string, advance position.
// Returns the codepoint, or 0 on error.
uint32_t next_cp(const std::string& s, size_t& pos);

// Count number of codepoints in the first byte_len bytes of s.
size_t count_codepoints(const std::string& s, size_t byte_len);

// Character category checks
bool is_cyrillic(uint32_t cp);
bool is_runic(uint32_t cp);
bool is_id_start(uint32_t cp);
bool is_id_continue(uint32_t cp);

} // namespace utf8
