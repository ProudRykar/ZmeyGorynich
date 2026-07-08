#include "error.h"
#include "color.h"
#include <sstream>

std::string format_error(const ZmeyError& e) {
    const auto& ctx = e.context();
    std::ostringstream oss;

    oss << color::RED << "Ошибка: " << color::RESET << e.what() << "\n";

    if (ctx.line > 0 && !ctx.fullCode.empty()) {
        std::vector<std::string> lines;
        std::string line;
        std::istringstream stream(ctx.fullCode);
        while (std::getline(stream, line)) {
            lines.push_back(line);
        }

        int start = std::max(0, ctx.line - 2);
        int end = std::min(static_cast<int>(lines.size()), ctx.line);

        for (int i = start; i < end; ++i) {
            oss << color::CYAN << " " << (i + 1) << " | " << color::RESET
                << lines[i] << "\n";
        }

        if (ctx.line > 0 && ctx.line <= static_cast<int>(lines.size())) {
            oss << color::RED << "     | ";
            for (int c = 0; c < ctx.col - 1; ++c) {
                oss << " ";
            }
            oss << "^\n" << color::RESET;
        }
    }

    return oss.str();
}
