# AI自由コマンド作成・簡易ゲート

通常の開発実行は、CHAT自身がShellコマンドを作成して既存の `host.command` から実行する。対象Repo・作業ディレクトリ・実行先・現在のSHAを確認し、既存のGitHub Actions → Gateway → Receiver → Hostを使用する。Masterに技術判断やコマンド選択を求めない。

実行直前にAI自身が一度だけ確認する。
1. **破損**：意図しない削除・上書き・他者の作業への影響がないか。
2. **誤り**：対象、構文、引数、実行先が正しいか。
3. **見直し**：完成したコマンド本文を読み直したか。

問題なければ即実行。問題があればAI自身で修正して続行する。実行結果を確認して開発を続ける。この簡易ゲートはMasterの承認、独立したテスト工程、逐次報告、入力・出力の恣意的な容量制限を増やさない。権限・認証・機密保護・不可逆操作の既存境界は守る。隔離開発が必要な場合だけ `dev.job` を使用する。

Masterへコマンドを渡す例外的な場合だけ `docs/MASTER_TERMINAL_COMMAND.md` を適用する。

生成時はShell文字列の多重連結を避け、Python本文を`.py`、Shell本文を`.sh`へ書き、既存の要求draftと`python3 scripts/chat_host_command_prepare.py --command-file <file> --language python --request-draft <draft.json> --output-directory .github/chat-host-requests`で組み立てられる。Pythonは実行せずcompileし、本文を展開しないquoted heredocへ変換する。要求ファイル名は`req_<24桁hex>.json`を自動生成し、JSONの改行・引用符はserializerへ任せる。draftのCurrent/SHA/START根拠は実際に確認したものを渡し、ツールは承認receiptや権限を作らない。draftなしならコマンドの構文確認だけを行い、要求は作成しない。

既存Selectorも最終本文を`bash -n`と、認識可能なquoted Python heredocのcompileで検査する。未閉鎖heredocの警告も拒否する。動的生成、inline `-c`、任意の複雑なShell内Pythonは全面解析せず、診断の`python_coverage`とparser versionを確認する。構文成功は実行先・SHAの鮮度・必要ファイル・コマンドの安全性・Runtime成功を証明しない。Source依存操作は既存`source_context`を使用し、失敗時は元の要求/Runと固定診断コードから修正する。SERVER_AI自身の通常VS実行へHost経路を強制しない。

2026-10-17の調査では、保存済み100要求の構文が正常でも、稼働Gatewayの秘匿置換・4000文字sliceを適用すると18本文が変わり11件が構文不正になった。生成と伝送を分けて検証し、エンコード等で秘匿処理を回避しない。登録済み内部配送先の正確なdata配送はGateway incident #28の設定・Source・実機証拠で別途確認する。ログの秘匿処理は維持し、credential値をコマンドへ埋め込まない。
