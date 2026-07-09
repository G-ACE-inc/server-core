#!/usr/bin/env bash

echo "DISABLED: PROJECT_STATUS.mdの自動追記は禁止されています。" >&2
echo "作業履歴はGitHub commit / PRを正本にしてください。" >&2
echo "PROJECT_STATUS.mdは管理者の明示指示がある場合だけ更新してください。" >&2
exit 1
