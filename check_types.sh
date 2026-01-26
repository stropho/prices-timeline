#!/usr/bin/env bash
# Type checking script

echo "Running mypy type checker..."
echo "=============================="

mypy . --pretty

exit_code=$?

if [ $exit_code -eq 0 ]; then
    echo ""
    echo "✅ Type checking passed!"
else
    echo ""
    echo "❌ Type checking failed. Please fix the errors above."
fi

exit $exit_code
