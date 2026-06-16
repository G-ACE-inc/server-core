#!/bin/bash
set -e

cd /home/admin1/server-core

echo ""
echo "=== PROJECT_STATUS.md 追記ツール ==="

read -p "作業内容: " WORK
read -p "変更ファイル: " FILES
read -p "結果: " RESULT
read -p "懸念事項: " ISSUE
read -p "次回作業: " NEXT

cat <<EOT >> PROJECT_STATUS.md

### $(date '+%Y-%m-%d %H:%M')

- **内容:** ${WORK}
- **変更ファイル:** ${FILES}
- **結果:** ${RESULT}
- **懸念事項:** ${ISSUE}
- **次回作業:** ${NEXT}

EOT

echo "PROJECT_STATUS.md 更新完了"
