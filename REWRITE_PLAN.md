# План переписывания ZmeyGorynich с Python на C++

## Общая информация

**Проект**: Интерпретатор эзотерического языка "Змей Горыныч" (кириллический синтаксис, Slavic-фольклорная тематика).

**Исходный код (Python)**: tree-walking interpreter: `lexer.py → parser.py → evaluator.py`

**Цель**: Переписать на C++17, используя:
- Классический полиморфный подход для AST (virtual + наследование)
- Самописный Decimal (без Boost)
- Catch2 для тестов
- Zero external dependencies (кроме Catch2)
- Улучшение архитектуры относительно Python-версии

---

## 1. Архитектурные решения

### 1.1 AST — классический полиморфизм

```cpp
enum class NodeType {
    Number, String, Bool, Identifier, BinaryOp, RootOp,
    Block, If, ElifBranch, While, FixedLoop,
    Assignment, ArrayAssignment,
    FunctionDef, FunctionCall, Return,
    Print, Input, Import,
    ArrayLiteral, ArrayAccess, ArrayCreate,
    ExpressionStatement
};

class ASTNode {
public:
    virtual ~ASTNode() = default;
    virtual NodeType getType() const = 0;
    int line = 0;
    int col = 0;
};
```

Каждая конкретная нода — класс-наследник. Используем `std::unique_ptr<ASTNode>` для владения в дереве.

### 1.2 Значения (Value)

```cpp
struct ArrayValue {
    std::vector<Value> elements;
};

class Value {
    enum class Type { Null, Int, Float, Decimal, String, Bool, Array };
    Type m_type;
    int64_t m_int;
    double m_float;
    Decimal m_decimal;
    std::string m_string;
    bool m_bool;
    ArrayValue m_array;
public:
    // конструкторы, геттеры, сеттеры
    Type getType() const;
    int64_t getInt() const;
    // ...
};
```

Можно через `std::variant`, но user выбрал классику → свой дискриминированный юнион.

### 1.3 Decimal — самописный

Фиксированная точность 100 знаков. Внутреннее хранение:
- `boost::multiprecision` не используем.
- Реализация: `int128_t` для малых точностей (30), или массив `uint64_t` для 50/100.
- Операции: +, -, *, /, sqrt, сравнение, строковый парсинг.
- Можно использовать библиотеку `libdecnumber` (из ICU) если хотим, но лучше самописный простой fixed-point с основанием 10^18.

**Упрощение**: Fixed-point decimal с precision 100, основание 10^18, массив из 6 uint64_t (100/18 ≈ 6 слов). Каждое слово хранит 18 десятичных разрядов.

### 1.4 Управление памятью

- `std::unique_ptr<ASTNode>` — всё дерево
- `std::shared_ptr` НЕ используем (кроме случая, если понадобится)
- `Context` владеет `std::unordered_map<std::string, Value>` для переменных
- Функции хранятся как struct с полями `args`, `body` (unique_ptr), `return_type`

### 1.5 Обработка ошибок

- Исключения: `SyntaxError`, `NameError`, `TypeError`, `ValueError`, `RuntimeError`
- Все наследуются от `ZmeyError : public std::runtime_error`
- В каждой ошибке — line, col, контекст (строка кода с указателем)

---

## 2. Структура проекта

```
/home/proudrykar/Develop/Projects/ZmeyGorynich/
├── CMakeLists.txt                    # Корневой CMake
├── src/
│   ├── CMakeLists.txt
│   ├── main.cpp                      # CLI entry point
│   └── zmey/
│       ├── CMakeLists.txt            # Библиотека libzmey
│       ├── color.h                   # ANSI цвета
│       ├── error.h / .cpp            # Исключения + контекст ошибок
│       ├── utf8.h / .cpp             # UTF-8 utilities
│       ├── decimal.h / .cpp          # High-precision Decimal (самописный)
│       ├── token.h                   # enum TokenType + struct Token
│       ├── lexer.h / .cpp            # Лексер
│       ├── ast.h / .cpp              # AST node classes
│       ├── parser.h / .cpp           # Recursive descent parser
│       ├── value.h / .cpp            # Value type (дискриминированный юнион)
│       ├── context.h / .cpp          # Symbol table / Environment
│       ├── builtins.h / .cpp         # Встроенные функции
│       └── evaluator.h / .cpp        # Tree-walking interpreter
├── tests/
│   ├── CMakeLists.txt
│   ├── test_main.cpp                 # Catch2 main
│   ├── test_decimal.cpp
│   ├── test_lexer.cpp
│   ├── test_parser.cpp
│   └── test_evaluator.cpp
├── examples/                         # .zg файлы (без изменений)
│   ├── test.zg
│   ├── test_debug.zg
│   ├── import_test_input.zg
│   └── ZmeyGorynichDocs.md
├── scripts/
│   └── clean.sh
└── .gitignore
```

---

## 3. Детальное описание каждого модуля

### 3.1 CMakeLists.txt

```cmake
cmake_minimum_required(VERSION 3.16)
project(zmeygorynych VERSION 1.0.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# Опции
option(ZMEY_BUILD_TESTS "Build tests" ON)

add_subdirectory(src)

if(ZMEY_BUILD_TESTS)
    enable_testing()
    find_package(Catch2 QUIET)
    if(NOT Catch2_FOUND)
        include(FetchContent)
        FetchContent_Declare(
            Catch2
            GIT_REPOSITORY https://github.com/catchorg/Catch2.git
            GIT_TAG v3.7.0
        )
        FetchContent_MakeAvailable(Catch2)
    endif()
    add_subdirectory(tests)
endif()
```

### 3.2 color.h — ANSI цвета

Простые `constexpr` или `const` строки с escape-кодами. Без enum class (как в Python — простые константы).

```cpp
namespace color {
    constexpr const char* BLUE = "\033[94m";
    constexpr const char* GREEN = "\033[92m";
    constexpr const char* RED = "\033[91m";
    constexpr const char* RESET = "\033[0m";
    constexpr const char* YELLOW = "\033[93m";
    constexpr const char* CYAN = "\033[96m";
    constexpr const char* MAGENTA = "\033[95m";
}
```

### 3.3 error.h — Система ошибок

```cpp
struct ErrorContext {
    int line;
    int col;
    std::string line_content;   // содержимое строки с ошибкой
    std::string filename;
};

class ZmeyError : public std::runtime_error {
    ErrorContext m_ctx;
public:
    ZmeyError(const std::string& msg, const ErrorContext& ctx);
    const ErrorContext& context() const;
};

class SyntaxError : public ZmeyError { /* ... */ };
class NameError : public ZmeyError { /* ... */ };
class TypeError : public ZmeyError { /* ... */ };
class ValueError : public ZmeyError { /* ... */ };
class RuntimeError : public ZmeyError { /* ... */ };

// Формирование контекста:
//   строка 1 | code line
//   строка 2 |   ^  (указатель на колонку)
ErrorContext make_error_context(const std::string& code, int line, int col);
```

Функция `format_error_message(msg, ctx)` должна выводить:
```
Ошибка: сообщение
   3 |  x = 42 гойда
     |      ^
```

### 3.4 utf8.h — UTF-8 utilities

Нужны для:
- Определения категории символа: кириллица, руны, латиница, цифра
- Итерации по UTF-8
- Декодирования кодовой точки

```cpp
namespace utf8 {
    // Проверки категорий символов
    bool is_cyrillic(uint32_t cp);
    bool is_runic(uint32_t cp);     // U+16A0-U+16FF
    bool is_letter(uint32_t cp);    // общая проверка для идентификаторов
    bool is_digit(uint32_t cp);
    bool is_id_start(uint32_t cp);  // буква или _
    bool is_id_continue(uint32_t cp); // буква, цифра, _

    // UTF-8 декодирование
    size_t decode(const char* s, uint32_t& cp);
    size_t encode(uint32_t cp, char* buf);

    // Получение следующей кодовой точки из std::string
    uint32_t next_cp(const std::string& s, size_t& pos);

    // Количество кодовых точек в строке (для column)
    size_t count_codepoints(const std::string& s, size_t byte_len);
}
```

### 3.5 decimal.h — High-precision Decimal (самописный)

**Внутреннее представление**: fixed-point с основанием 10^18, массив uint64_t слов.

```
precision = 100 знаков после запятой
scale = 10^18 в каждом слове
mantissa = uint64_t[6]  (6 * 18 = 108 > 100)
sign = bool
```

```cpp
class Decimal {
    static constexpr int WORDS = 6;
    static constexpr int DIGITS_PER_WORD = 18;
    static constexpr uint64_t BASE = 1000000000000000000ULL; // 10^18

    uint64_t m_words[WORDS] = {};
    bool m_negative = false;
    int m_exponent = 0; // смещение для позиции десятичной точки

public:
    Decimal();                          // = 0
    Decimal(int64_t v);
    Decimal(const std::string& str);    // парсинг

    // Арифметика
    Decimal operator+(const Decimal& other) const;
    Decimal operator-(const Decimal& other) const;
    Decimal operator*(const Decimal& other) const;
    Decimal operator/(const Decimal& other) const;
    Decimal sqrt() const;

    // Сравнения
    int compare(const Decimal& other) const; // -1, 0, 1
    bool operator==(const Decimal& other) const;
    bool operator<(const Decimal& other) const;
    bool operator>(const Decimal& other) const;
    bool operator<=(const Decimal& other) const;
    bool operator>=(const Decimal& other) const;

    // Преобразования
    std::string toString() const;
    double toDouble() const;
    int64_t toInt64() const;

    // Precision management
    void setPrecision(int prec); // округление до prec знаков
    int getPrecision() const;
};
```

**Важно**: Реализация может быть упрощена — используем `uint128_t` (компиляторный intrinsic) или `__int128` для промежуточных вычислений.

### 3.6 token.h — Токены

```cpp
enum class TokenType {
    NUMBER, ROOT, GOYDA, BLOCK_OPEN, BLOCK_CLOSE,
    TYPE_ANNOTATION, DEF, RETURN_TYPE, RETURN,
    IMPORT, AS, DOT, OP, ID, ASSIGN,
    STRING, NEWLINE, COMMA, BRACKET_OPEN, BRACKET_CLOSE,
    PAREN_OPEN, PAREN_CLOSE, EOF_TOKEN, INVALID
};

struct Token {
    TokenType type;
    std::string value;
    int line;
    int col;

    Token(TokenType t, std::string v, int l, int c);
};

// Для отладки/вывода
const char* tokenTypeName(TokenType t);
```

### 3.7 lexer.h / .cpp — Лексер

```cpp
class Lexer {
    std::string_view m_code;
    size_t m_pos = 0;
    int m_line = 1;
    int m_line_start = 0; // byte offset of line start

public:
    explicit Lexer(std::string_view code);

    std::vector<Token> tokenize();

private:
    // Trie для многословных операторов
    struct OpTrieNode {
        std::map<char32_t, std::unique_ptr<OpTrieNode>> children;
        std::string full_op; // заполнено, если это конец оператора
    };
    std::unique_ptr<OpTrieNode> m_op_trie;

    void buildOpTrie();
    std::string tryMatchOp(); // возвращает сматченный оператор или ""

    char32_t peek();          // текущая кодовая точка
    char32_t advance();       // прочитать и сдвинуться
    void skipWhitespace();
    void skipLineComment();
    void skipMultilineComment();

    Token readNumber();
    Token readString();
    Token readIdentifier();   // ID или keyword
    Token readOperator();     // через Trie
    Token readNext();         // один токен
};
```

**Ключевые особенности:**
- Ручной FSM, без `<regex>` (C++ regex медленный и проблемный с Unicode)
- Многословные операторы через Trie (префиксное дерево), построенное на этапе конструирования лексера
- Список операторов тот же, что в Python `SLAVIC_OP`
- Кириллица/руны в идентификаторах — проверка через `utf8::is_id_start/continue`
- Комментарии: `# ...` и `Голос предков шепчет: ... Голос предков внезапно стих...`
- Позиция: line + column (в кодовых точках)

**Trie для операторов:**
```
корень → в → ... → "возвысить в"
              → ... → "возвысить"
прибави
отними
умножи → ... → на → "умножи на"
ровно → ... → либо → превосходит → "ровно либо превосходит"
                → уступает → "ровно либо уступает"
       ... → "ровно"
```

### 3.8 ast.h — AST Nodes (классический полиморфизм)

```cpp
enum class NodeType {
    Number, String, Bool, Identifier, BinaryOp, RootOp,
    Block, If, ElifBranch, While, FixedLoop,
    Assignment, ArrayAssignment,
    FunctionDef, Return,
    Print, Input, Import,
    ArrayLiteral, ArrayAccess, ArrayCreate,
    ExpressionStatement, Args, Arg, ElifBlocks
};

class ASTNode {
public:
    virtual ~ASTNode() = default;
    virtual NodeType getType() const = 0;
    int line = 0;
    int col = 0;
};

// --- Литералы ---
class NumberNode : public ASTNode {
public:
    NodeType getType() const override { return NodeType::Number; }
    std::string value;  // raw string from source, parsed later
};

class StringNode : public ASTNode {
public:
    NodeType getType() const override { return NodeType::String; }
    std::string value; // без кавычек
};

class BoolNode : public ASTNode {
public:
    NodeType getType() const override { return NodeType::Bool; }
    bool value;
};

// --- Идентификаторы ---
class IdentifierNode : public ASTNode {
public:
    NodeType getType() const override { return NodeType::Identifier; }
    std::string name;  // может быть "module.var"
};

// --- Выражения ---
class BinaryOpNode : public ASTNode {
public:
    NodeType getType() const override { return NodeType::BinaryOp; }
    std::unique_ptr<ASTNode> left;
    std::unique_ptr<ASTNode> right;
    std::string op; // оригинальный строковый оператор
};

class RootOpNode : public ASTNode {
public:
    NodeType getType() const override { return NodeType::RootOp; }
    std::unique_ptr<ASTNode> expr;
};

// --- Массивы ---
class ArrayLiteralNode : public ASTNode {
public:
    NodeType getType() const override { return NodeType::ArrayLiteral; }
    std::vector<std::unique_ptr<ASTNode>> elements;
};

class ArrayAccessNode : public ASTNode {
public:
    NodeType getType() const override { return NodeType::ArrayAccess; }
    std::unique_ptr<ASTNode> array;
    std::unique_ptr<ASTNode> index;
};

class ArrayCreateNode : public ASTNode {
public:
    NodeType getType() const override { return NodeType::ArrayCreate; }
    std::unique_ptr<ASTNode> size;
    std::unique_ptr<ASTNode> value;
};

// --- Операторы ---
class ExpressionStatementNode : public ASTNode {
public:
    NodeType getType() const override { return NodeType::ExpressionStatement; }
    std::unique_ptr<ASTNode> expr;
};

class BlockNode : public ASTNode {
public:
    NodeType getType() const override { return NodeType::Block; }
    std::vector<std::unique_ptr<ASTNode>> statements;
};

class AssignmentNode : public ASTNode {
public:
    NodeType getType() const override { return NodeType::Assignment; }
    std::string variable;
    std::unique_ptr<ASTNode> expr;
    std::string type_hint; // может быть пустой
};

class ArrayAssignmentNode : public ASTNode {
public:
    NodeType getType() const override { return NodeType::ArrayAssignment; }
    std::string variable;
    std::unique_ptr<ASTNode> index;
    std::unique_ptr<ASTNode> expr;
    std::string type_hint;
};

class PrintNode : public ASTNode {
public:
    NodeType getType() const override { return NodeType::Print; }
    std::vector<std::unique_ptr<ASTNode>> args;
    bool silent = false; // "и эхом затихнуть"
};

class InputNode : public ASTNode {
public:
    NodeType getType() const override { return NodeType::Input; }
    std::unique_ptr<ASTNode> prompt; // может быть nullptr
    std::string variable;
};

class WhileNode : public ASTNode {
public:
    NodeType getType() const override { return NodeType::While; }
    std::unique_ptr<ASTNode> condition;
    std::unique_ptr<BlockNode> body;
};

class FixedLoopNode : public ASTNode {
public:
    NodeType getType() const override { return NodeType::FixedLoop; }
    int iterations;
    std::unique_ptr<BlockNode> body;
};

// --- Conditionals ---
class IfNode : public ASTNode {
public:
    NodeType getType() const override { return NodeType::If; }
    std::unique_ptr<ASTNode> condition;
    std::unique_ptr<BlockNode> then_body;
    std::vector<std::unique_ptr<IfNode>> elif_branches; // каждый elif: {condition, body}
    std::unique_ptr<BlockNode> else_body; // может быть nullptr
};

// --- Functions ---
class ArgNode : public ASTNode {
public:
    NodeType getType() const override { return NodeType::Arg; }
    std::string name;
    std::string type_hint;
};

class ArgsNode : public ASTNode {
public:
    NodeType getType() const override { return NodeType::Args; }
    std::vector<std::unique_ptr<ArgNode>> args;
};

class FunctionDefNode : public ASTNode {
public:
    NodeType getType() const override { return NodeType::FunctionDef; }
    std::string name;
    std::unique_ptr<ArgsNode> args;
    std::unique_ptr<BlockNode> body;
    std::string return_type;
};

class ReturnNode : public ASTNode {
public:
    NodeType getType() const override { return NodeType::Return; }
    std::unique_ptr<ASTNode> expr;
};

class CallNode : public ASTNode {
public:
    NodeType getType() const override { return NodeType::FunctionCall; }
    std::string name;
    std::vector<std::unique_ptr<ASTNode>> args;
};

class ImportNode : public ASTNode {
public:
    NodeType getType() const override { return NodeType::Import; }
    std::string filename;
    std::string alias; // может быть пустой
};
```

### 3.9 parser.h / .cpp — Парсер

```cpp
class Parser {
    const std::vector<Token>& m_tokens;
    std::string_view m_code;
    size_t m_pos = 0;

public:
    Parser(const std::vector<Token>& tokens, std::string_view code);
    std::vector<std::unique_ptr<ASTNode>> parse();

private:
    const Token& cur() const;    // текущий токен
    const Token& peek(size_t offset = 0) const;
    void advance();
    bool accept(TokenType type);
    bool accept(TokenType type, const std::string& value);
    std::string expect(TokenType type, const std::string& msg = "");
    std::string expect(TokenType type, const std::string& value, const std::string& msg = "");

    ErrorContext errorCtx() const;
    [[noreturn]] void error(const std::string& msg) const;

    // --- Парсинг выражений ---
    std::unique_ptr<ASTNode> parsePrimary();
    std::unique_ptr<ASTNode> parsePower();
    std::unique_ptr<ASTNode> parseMultiplicative();
    std::unique_ptr<ASTNode> parseAdditive();
    std::unique_ptr<ASTNode> parseComparison();
    std::unique_ptr<ASTNode> parseExpression();

    // --- Парсинг операторов ---
    std::unique_ptr<ASTNode> parseStatement();
    std::unique_ptr<ASTNode> parseAssignment();
    std::unique_ptr<ASTNode> parsePrint();
    std::unique_ptr<ASTNode> parseInput();
    std::unique_ptr<ASTNode> parseWhile();
    std::unique_ptr<ASTNode> parseIf();
    std::unique_ptr<ASTNode> parseFunctionDef();
    std::unique_ptr<ASTNode> parseReturn();
    std::unique_ptr<ASTNode> parseCall();
    std::unique_ptr<ASTNode> parseFixedLoop();
    std::unique_ptr<ASTNode> parseArrayCreate();
    std::unique_ptr<ASTNode> parseImport();
    std::unique_ptr<ASTNode> parseExpressionStatement();

    // Вспомогательные
    std::string parseTypeAnnotation(); // парсит "быти цело" → "число:int"
    std::vector<std::unique_ptr<ASTNode>> parseCommaSeparated(
        TokenType close_type, const std::string& close_value,
        std::function<std::unique_ptr<ASTNode>()> element_parser);
};
```

**Улучшения относительно Python:**
- Нет замыканий — методы класса
- Чёткие типы нод вместо строковых `node.type == 'Assignment'`
- `TYPE_MAP` — `std::unordered_map<std::string, std::string>`
- Циклы с фиксированным числом итераций — `std::unordered_map<std::string, int>`

### 3.10 value.h / .cpp — Тип значения

```cpp
class Value {
public:
    enum class Type { Null, Int, Float, Decimal, String, Bool, Array };

    // Конструкторы
    Value() : m_type(Type::Null), m_int(0), m_float(0.0), m_bool(false) {}
    Value(int64_t v);
    Value(double v);
    Value(const Decimal& v);
    Value(const std::string& v);
    Value(bool v);
    Value(const ArrayValue& v);

    // Геттеры
    Type getType() const { return m_type; }
    bool isNull() const;
    int64_t getInt() const;
    double getFloat() const;
    const Decimal& getDecimal() const;
    const std::string& getString() const;
    bool getBool() const;
    const ArrayValue& getArray() const;
    ArrayValue& getArray();

    // Утилиты
    std::string toString() const;  // для вывода (bool → Истина/Ложь)
    std::string typeName() const;  // "цело", "плывун", и т.д.
    bool isNumeric() const;        // Int, Float, или Decimal

private:
    Type m_type;
    int64_t m_int;
    double m_float;
    Decimal m_decimal;
    std::string m_string;
    bool m_bool;
    ArrayValue m_array;
};

// Вспомогательные функции
Value stringifyValue(const Value& v);
```

### 3.11 context.h / .cpp — Контекст (symbol table)

```cpp
struct FunctionDef {
    std::vector<std::string> args;
    std::vector<std::string> args_type_hints;
    std::unique_ptr<BlockNode> body;
    std::string return_type;
    std::string name;
};

struct CallFrame {
    std::string func_name;
    std::vector<std::unique_ptr<ASTNode>> args_nodes;
    std::vector<Value> args_values;
};

class Context {
    std::unordered_map<std::string, Value> m_variables;
    std::unordered_map<std::string, std::string> m_type_hints;
    std::unordered_map<std::string, FunctionDef> m_functions;
    Context* m_parent = nullptr;
    std::vector<CallFrame> m_call_stack;

public:
    Context(Context* parent = nullptr);

    // Variables
    Value get(const std::string& key) const; // ищет в parent
    void set(const std::string& key, const Value& value, const std::string& type_hint = "");
    bool hasVariable(const std::string& key) const;

    // Type hints
    std::string getTypeHint(const std::string& key) const;

    // Functions
    void setFunction(const std::string& name, FunctionDef func);
    const FunctionDef* getFunction(const std::string& name) const; // ищет в parent + builtins

    // Call stack (для глас)
    void pushCall(const std::string& name,
                  const std::vector<std::unique_ptr<ASTNode>>& args_nodes,
                  const std::vector<Value>& args_values);
    void popCall();
    std::string getCallArgName(int index = 0) const;
    const CallFrame& currentCallFrame() const;

    // Массивы builtins
    static const std::unordered_map<std::string, FunctionDef>& builtins();
};
```

### 3.12 builtins.h / .cpp — Встроенные функции

```cpp
namespace builtins {
    Value молвить(const std::vector<Value>& args, Context* ctx);
    Value глас(const std::vector<Value>& args, Context* ctx);
    Value созвать_дружину(const std::vector<Value>& args, Context* ctx);
    Value имя_аргумента(const std::vector<Value>& args, Context* ctx);
    Value тип_значения(const std::vector<Value>& args, Context* ctx);
    Value строчить_значение(const std::vector<Value>& args, Context* ctx);

    // Регистрация в контексте
    void registerBuiltins(Context& ctx);
}
```

**Улучшение**: `глас` переписывается чисто, без λ-макарон. Разбивается на логические шаги:
1. Определить имя (переменная или вызов функции)
2. Получить тип
3. Сформировать строку с ANSI-цветами и рунами
4. Вывести

### 3.13 evaluator.h / .cpp — Вычислитель

```cpp
class Evaluator {
    Context* m_context;
    std::string m_current_file;
    int m_decimal_precision = 100;  // getcontext().prec

public:
    Evaluator(Context* ctx, const std::string& current_file = "");

    // Главный цикл
    Value evaluateProgram(const std::vector<std::unique_ptr<ASTNode>>& ast);
    Value evaluate(const ASTNode& node);

private:
    // Expression evaluation
    Value evaluateExpression(const ASTNode& node);
    Value evaluateBinaryOp(const BinaryOpNode& node);
    Value evaluateCall(const CallNode& node);

    // Utility
    Value normalizeOperator(const std::string& op) const; // славянский → символ
    void checkType(const Value& value, const std::string& type_hint, const ASTNode& node);

    // Import
    void evaluateImport(const std::vector<std::unique_ptr<ASTNode>>& ast,
                        Context& module_ctx, const std::string& filepath);

    // Function call
    Value callFunction(const FunctionDef& func,
                       const std::vector<Value>& args,
                       const std::vector<std::unique_ptr<ASTNode>>& args_nodes,
                       Context& parent_ctx);
};
```

**Улучшение**: `evaluate_condition` полностью удаляется. Вместо этого:
- `While` и `If` используют `evaluateExpression` для условия
- BinaryOp с операторами сравнения возвращает `Value(true/false)`
- Если `while(true)` — работает бесконечно (как задумано)
- Исправлен баг Python-версии, где `evaluate_condition` игнорировала `BinaryOp` с компараторами

**Улучшение**: В Python `evaluate_condition` проверяет `node.type == 'Condition'`, но парсер НИКОГДА не создаёт такие ноды — он создаёт `BinaryOp`. Это баг, из-за которого While и If не работали бы. Исправляем в C++.

**Улучшение**: `call_function` не ищет тип аргумента в `func['body'].children[0].children` (как в Python). Вместо этого типы аргументов хранятся в `FunctionDef.args_type_hints`.

### 3.14 main.cpp — CLI

```cpp
int main(int argc, char* argv[]) {
    if (argc < 2) {
        std::cerr << "Usage: zmeygorynych <file.zg>\n";
        return 1;
    }

    std::string filename = argv[1];
    if (filename.size() < 3 || filename.substr(filename.size() - 3) != ".zg") {
        std::cerr << "Error: " << filename << " is not a valid ZmeyGorynych file!\n";
        return 1;
    }

    try {
        std::ifstream file(filename);
        if (!file) {
            throw std::runtime_error("Cannot open file: " + filename);
        }
        std::string code((std::istreambuf_iterator<char>(file)),
                          std::istreambuf_iterator<char>());

        Lexer lexer(code);
        auto tokens = lexer.tokenize();

        if (/* DEBUG */ false) {
            std::cerr << "Tokens:\n";
            for (const auto& t : tokens) {
                std::cerr << "  " << tokenTypeName(t.type)
                          << " '" << t.value << "'"
                          << " " << t.line << ":" << t.col << "\n";
            }
        }

        Parser parser(tokens, code);
        auto ast = parser.parse();

        if (/* DEBUG */ false) {
            std::cerr << "AST:\n";
            // printAST(ast);
        }

        Context ctx;
        builtins::registerBuiltins(ctx);

        Evaluator evaluator(&ctx, filename);
        evaluator.evaluateProgram(ast);

    } catch (const ZmeyError& e) {
        std::cerr << "Ошибка: " << e.what() << "\n";
        return 1;
    } catch (const std::exception& e) {
        std::cerr << "Ошибка: " << e.what() << "\n";
        return 1;
    }

    return 0;
}
```

---

## 4. Тесты (Catch2)

### test_main.cpp
```cpp
#define CATCH_CONFIG_MAIN
#include <catch2/catch_all.hpp>
```

### test_lexer.cpp
Прямой перенос Python-тестов:
- `test_tokenize_basic` — `x = 42 гойда`
- `test_tokenize_string` — `"привет" гойда`
- `test_tokenize_boolean` — `x = истина гойда` (истина/ложь — пока ID, не ключевые слова)
- `test_tokenize_function_call` — `молвить(x) гойда`
- `test_tokenize_comments` — `# ...`
- `test_tokenize_multi_line_comment` — `Голос предков шепчет: ...`

### test_parser.cpp
- `test_parse_assignment` — `x быти цело = 42 гойда`
- `test_parse_function_call` — `молвить(42) гойда`
- `test_parse_if_statement` — `аще x > 0 то ухожу я в пляс ...`
- `test_parse_while_loop` — `покуда x < 10 ...`
- `test_parse_function_definition` — `сотвори добавить(x быти цело, y быти цело) изречет цело ...`
- `test_parse_invalid_syntax` — missing `гойда`

### test_evaluator.py → test_evaluator.cpp
- `test_evaluate_assignment` — проверка переменной
- `test_evaluate_print` — проверка вывода
- `test_evaluate_if` — условие
- `test_evaluate_while` — цикл
- `test_evaluate_function_call` — функция
- `test_evaluate_type_error` — тип ошибки

---

## 5. Пофазовая реализация

### Фаза 1: Фундамент (3-4 файла)
1. `color.h` — 10 строк
2. `utf8.h/.cpp` — 100-150 строк
3. `error.h/.cpp` — 80-100 строк
4. `decimal.h/.cpp` — 300-400 строк
5. `CMakeLists.txt` корневой + в src/

**Проверка**: `decimal` тесты (сложение, вычитание, умножение, деление, sqrt, сравнение)

### Фаза 2: Лексер (3 файла)
1. `token.h` — 50 строк
2. `lexer.h/.cpp` — 250-350 строк

**Проверка**: лексер проходит тесты test_lexer

### Фаза 3: AST + Парсер (4 файла)
1. `ast.h` — 200-300 строк (все классы нод)
2. `parser.h/.cpp` — 500-700 строк

**Проверка**: парсер проходит 6 тестов из test_parser

### Фаза 4: Value + Context + Builtins (6 файлов)
1. `value.h/.cpp` — 150-200 строк
2. `context.h/.cpp` — 150-200 строк
3. `builtins.h/.cpp` — 100-150 строк

**Проверка**: компилируется, builtins регистрируются

### Фаза 5: Evaluator (2 файла)
1. `evaluator.h/.cpp` — 500-700 строк

### Фаза 6: CLI + Тесты
1. `main.cpp` — 60 строк
2. `tests/test_lexer.cpp` — 80 строк
3. `tests/test_parser.cpp` — 100 строк
4. `tests/test_evaluator.cpp` — 100 строк

**Проверка**: полный прогон тестов, запуск на example .zg файлах

---

## 6. Улучшения относительно Python-версии

1. **Исправлен баг `evaluate_condition`**: Удаляем отдельную функцию для условий. `While` и `If` используют `evaluateExpression`, которая корректно обрабатывает `BinaryOp` с компараторами.

2. **Типы аргументов функции**: Вместо поиска типа аргумента в `body.children[0].children` (хрупко), типы хранятся в `FunctionDef.args_type_hints`.

3. **`глас` без λ-макарон**: 65-строчная лямбда с walrus operator разбивается на чистые шаги.

4. **Чёткая типизация AST**: Вместо одного класса `Node` с полем `type` — иерархия классов с типизированными полями.

5. **Разделение на мелкие файлы**: Вместо `evaluator.py` (801 строка) — несколько модулей.

6. **Производительность**: C++ компилируется в нативный код. Нет оверхеда Python-интерпретатора.

7. **Trie для операторов**: Вместо regex — префиксное дерево, O(length_of_op) на поиск.

---

## 7. Известные баги Python-версии (чтобы не воспроизводить)

1. **`evaluate_condition` против `BinaryOp`**: Функция `evaluate_condition` проверяет `node.type == 'Condition'`, но парсер создаёт `BinaryOp` для сравнений. В результате `evaluate_condition` всегда возвращает `False` для реальных условий → циклы while и if с условиями НЕ РАБОТАЮТ.

2. **`:`, `ё` в нормализации**: `normalize_operator` убирает `:` с конца и заменяет `ё` на `е`. Нужно убедиться, что это корректно.

3. **`getcontext().prec`**: Глобальная переменная precision Decimal — проблемы с потоками и неявным состоянием. В C++ precision хранится в Evaluator.

---

## 8. Требования к среде

- C++17 компилятор (GCC 9+, Clang 10+, MSVC 2019+)
- CMake 3.16+
- Catch2 3.x (автоматически через FetchContent)
- Linux (текущая платформа), в перспективе кроссплатформенность
