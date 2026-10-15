# MASTER TERMINAL COMMAND CONTRACT

Version: 2026-10-05-r12
Role: G-ACE WorkspaceでAIがMasterへ提示するTerminal Commandの形式・安全・検証・返却契約。

## 1. Scope

**適用対象の限定（重要）:** この文書の行数・総文字数・ワンライナー・`GACE_RESULT`などの表示形式は、Master本人へCopy & Paste用Commandを**提示する場合だけ**の契約である。server-coreの新しい共通 `host.command` ターミナルでAI自身が作成・送信・実行するコマンド、標準入力、標準出力、標準エラー、成果物には適用しない。新ターミナルへの入出力を66行/6,072文字/4,000文字へ切り詰めたり、長文コマンドを禁止したり、固定コマンド方式へ誘導する根拠にしてはならない。新ターミナルは実際の通信・実行資源・認証・機密保護の境界に従い、必要な大きさのコマンドとデータを処理する。大容量は必要に応じて分割・永続化・ページングし、欠落や省略を明示して再取得可能にする。Masterへの承認・確認を新設しない。

本Contractは、Workspace AI / Server AI / Cursor / Codex等がMasterへCopy & Paste用Commandを提示する場合に必ず適用する。

Notion最上位大原則のMaster Terminal Command Contractを弱めてはならない。server-core側では、Workspace / Server AIがNotion本文を直接読まなくても同じ安全境界を守れるよう、実行時に必要なCommand契約を保持する。

## 2. Master Interface

Masterの通常操作は次だけとする。

1. AIが提示した完成Code BlockをそのままCopy & Pasteする。
2. 実行結果を加工せず返す。

MasterへCommand書換え、Placeholder置換、Path推測、Log選別、複数Commandからの選択を要求しない。

## 3. Mandatory Pre-Send Gate

Commandを提示する直前に、完成Command本文そのものについて最低限次を確認する。

```text
ONE_CODE_BLOCK=YES
ONE_EXEC_COMMAND=YES
ONE_LINE=YES_OR_EXPLICIT_SAFE_EXCEPTION
MAX_LINES<=66
TOTAL_COMMAND_CHARS<=6072
COPY_PASTE_READY=YES
MASTER_EDIT_REQUIRED=NO
PLACEHOLDER=0
PROJECT_IDENTITY=VALID
CONFIRMED_DIRECTORY=YES
WORKDIR_SET_FIRST=YES
APPROVAL_BOUNDARY_OK=YES
TASK_NECESSITY_ONLY=YES
EVIDENCE_NEEDED_ONLY=YES
PRIMARY_EXIT_CAPTURE=VALID
GACE_RESULT_ENVELOPE=VALID
RESULT_MARKERS_EXACT_ONE_PAIR=YES
PROJECT_END_PRESENT=YES
INTERACTIVE_SHELL_SURVIVES=YES
NAKED_EXIT=0
UNBOUNDED_WAIT=0
SECRET_EXPOSURE=0
EXACT_COMMAND_SYNTAX_VALIDATION=PASS
POST_VALIDATION_COMMAND_MUTATION=0
FINAL_COMMAND_REVIEW=PASS
```

1項目でも満たせないCommandはMasterへ提示しない。不要確認の削減、Command単純化、既存検証済みHelper / Script、別Executorへ再Routingする。

## 4. Exact Command Syntax Validation Hard Gate

目視ReviewだけでSyntax PASSにしてはならない。

Masterへ表示する**完成Code Blockの実体そのもの**を、対象ShellのParserまたはSyntax-only validatorへ通す。

### Bash系

実行せず完成本文を`bash -n`相当でParseし、Exit 0を確認する。Bash以外を対象にする場合は対象ShellのSyntax-only検査を優先する。

### PowerShell

`System.Management.Automation.Language.Parser`等のParse-only検査でParse Error 0件を確認する。

Parserを利用できない場合、複数制御構文、複雑なQuote / Escape、Script相当のCommandをMasterへ発行しない。検証済みHelper / Script、より単純なCommand、別Executorへ再Routingする。

### Exact Body Invariant

Validatorへ渡した本文とMasterへ表示する本文は同一でなければならない。

検証後に空白以外を修正、追記、圧縮、1行化した場合、そのPASSは失効する。最終本文で再検査する。

次の場合は送信禁止。

- Parser FAIL
- validator未実施
- 対象Shell不明
- 検証本文と表示本文が不一致
- 検証後にCommand本文を変更したが再検査していない

Syntax PASSは意味的安全性の代替ではない。Directory / Project / Approval / Exit Code / Secret / Mutation / GACE_RESULT等の既存Gateも同時にPASSさせる。

## 5. Format / Size

- 原則: 1 Code Block / 1実行Command / 1行の完成Command。
- 既存の1行原則は維持する。
- ただしScript相当の複数制御構文や深いNestを1行へ圧縮するとSyntax事故Riskが増える場合は、安全性のための明示例外として複数行を許可する。
- 明示例外でも1 Code Block全体が1回Copy & Pasteする1実行単位でなければならない。
- 最大66行。
- Command本文合計6072文字以内。
- 1行の文字数上限は設けない。
- `...`、`<PROJECT>`、`<PATH>`、`<ID>`、未確定値、未確認Path等のPlaceholderを残さない。
- 1行原則のためだけに`if / elif / else / fi`、loop、subshell、複数段Quote等を無理に圧縮しない。

## 6. Complexity Gate

1 Commandの中へ、Read-only診断、Source整列、Build / Runtime Mutation、Test、長大Readbackを目的なく詰め込まない。

同一Change Unitとして一体である必要が無ければ分離する。Master操作回数だけを減らす目的でScript相当処理を巨大Commandへしない。

過剰なNest、Subshell、Quote、Escape、Here Document、一時変数、Pipelineを不必要に増やさない。ただし安全性・判定精度に必要な処理は削らない。

## 7. Project / Environment / Directory

必要範囲で次を確定してからCommandを生成する。

- Project
- Environment / Host
- OS / Shell
- Directory
- Repository
- Branch / HEAD when relevant
- Working Tree when relevant
- Runtime target when relevant
- Approval Boundary

未確認Pathや値を推測してMutation Commandへ入れない。

対象Project識別が必要なCommandは、Project固有処理より先に確認済みProject Directoryを指定して親Interactive Shellで`cd` / `Set-Location`する。`cd`失敗時は誤Directoryで続行しない。

## 8. Shell Survival

MasterのInteractive ShellをCommand失敗と一緒に終了させない。

- 裸の`exit`を使わない。
- 不要な`exec`を使わない。
- 不要な`set -e` / `set -euo pipefail`で親Interactive Shellを巻き込まない。
- 無制御の`tail -f`等を使わない。
- 長時間処理はtimeout等で上限を設ける。

## 9. Mutation Class / Fail Closed

Commandは内部的に次へ分類する。

```text
READ_ONLY
SAFE_MUTATION
RUNTIME_MUTATION
DESTRUCTIVE
```

期待Preconditionと違えば変更せずfail-closedする。

診断Commandへpull / reset / branch変更 / restart / recreate / deploy / rm / prune / overwrite / DB変更 / Production変更等を勝手に混在させない。

Master Approval Boundaryを越えるMutationを暗黙に追加しない。

## 10. Exit Code / Pipeline

Primary処理の成否は直後に保存する。後続`printf`等で`$?`を上書きして成功扱いしない。

Pipelineを使う場合はShellに応じた方法でPipeline全体を正しく評価する。

## 11. GACE_RESULT Envelope

結果返却が必要なCommandは次の最小Envelopeへ統一する。

```text
========== GACE_RESULT_BEGIN ==========
PROJECT=...
PWD=...
ACTION=...
VERIFY=...
EXIT_CODE=...
ERROR=...
PROJECT_END=...
========== GACE_RESULT_END ==========
```

- 1 Envelope = 1 Project / 1 Environment。
- `PROJECT_END`はBEGIN直後の`PROJECT`と同じ値。
- 成功・失敗どちらでも可能な限りENDまで出す。
- BEGINがありENDが無い場合は`NOT_VERIFIED`。
- Taskに不要なField取得のためだけに追加確認しない。
- 必要時だけ`HOST / ENVIRONMENT / BRANCH / BEFORE_HEAD / REMOTE_HEAD / AFTER_HEAD / RUN_ID`等を追加する。

## 12. Log / Secret

大量LogはBound / Filter / File保存等で制御する。

既にLog / Artifact / CI / TGserver Evidenceから確定できる事実をMaster Terminalで重複取得しない。

Secret / Token / Credential実値をChat返却へ出さない。`env`、`docker inspect`、`.env`等を無差別表示しない。

## 13. Result Handling

Masterから結果が返ったら説明やPASS/FAIL判定だけで止まらない。

```text
結果判定
 -> 原因確定
 -> AI側で可能な修正 / 調査
 -> Test
 -> 再検証
 -> 次の未完了項目
```

再度Master Terminal操作が必要な場合だけ次の完成Commandを出す。

## 14. Absolute Enforcement

- Ruleを読んだという自己申告だけでCompliance扱いにしない。
- Syntax validationを実施していないCommandを`FINAL_COMMAND_REVIEW=PASS`にしない。
- 既存Constraintを短縮・省略・独自解釈で弱めない。
- Masterが毎回「大原則を守れ」と再指示しなくても本Contractを自動適用する。
