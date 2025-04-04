#!/bin/bash
#./scripts/clean.sh

RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

TO_CLEAN=(
    "__pycache__"
    "build"
    "*.pyc"
    "*.pyo"
    "*.pyd"
    "*.spec"
)

echo "Очистка временных файлов и папок во всех директориях..."

found_any=false

for item in "${TO_CLEAN[@]}"; do
    found_items=$(find . -name "$item")
    if [ -n "$found_items" ]; then
        echo "$found_items" | while IFS= read -r line; do
            rm -rf "$line"
            echo -e "${GREEN}Удалено: $line${NC}"
        done
        found_any=true
    fi
done

if [ "$found_any" = false ]; then
    echo -e "${RED}Временные файлы и папки не найдены.${NC}"
fi

if [ "$found_any" = true ]; then
    echo -e "${GREEN}Очистка завершена!${NC}"
fi