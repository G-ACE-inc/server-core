# SERVER COMMAND EXECUTION CONTRACT

Version: 2026-10-03
Role: Server上で実行するCommand / Scriptのtechnical safety・partial state・evidence契約。

## 1. Purpose

このContractは、Server上で実行するOperationについて、exact target、shell/process safety、mutation classification、authorization boundary、concurrency、exit-status、bounded diagnostics、interruption recovery、evidence promotionを定義する。

Chat UI、会話形式、Notion運用、外部アプリ固有のinteraction ruleは扱わない。

## 2. Pre-command Requirement

Server operationを実行する前に、`docs/G_ACE_WORKSPACE.md` / `operations/pre-execution-schema.json` に従い、Taskに必要な範囲で少なくとも次を解決する。

```text
TARGET_PROJECT
TARGET_REPOSITORY
MUTATION_REPOSITORIES
READ_ONLY_REPOSITORIES
NEXT_ACTION
EXECUTION_ROUTE
EXECUTION_CAPABILITY
EXECUTION_AUTHORIZATION
MUTATION_CLASS
VERIFY_PATH
PRE_EXECUTION_COMPLETE
BLOCKER
```

Path、Branch、Runtime identity、Service identity、Provider target、mutation authorityが不明な場合は推測で補完しない。

## 3. Shell / Process Safety

既存interactive terminalで実行するCommandは、fail-fast制御の副作用でparent shellを終了・破損させない。

Technical requirements:
- `set -e`, `set -u`, `pipefail` 等のfail-fast stateは、parent shellを維持する必要がある場合はisolated child shell/process内で使用する。
- workflow control用の `exit` はparent interactive shellではなくisolated child processを終了させる。
- `cd` 失敗後に別Directoryで処理を続行しない。
- unbounded wait / `tail -f` 等にはtimeout / cancellation boundaryを持たせる。
- pipeline failureが重要な場合はfinal processだけでなく必要なreturn codeを保持する。
- primary operationのreturn codeを、後続diagnostic出力で上書きしない。

Isolationは `bash -lc '...'` 等でよいが、要件はparent-shell preservationと正しいfailure propagationである。

## 4. Mutation Classification

最終状態を戻しただけでworkflowを `READ_ONLY` と呼ばない。

```text
READ_ONLY_INSPECTION
REVERSIBLE_LOCAL_MUTATION
REPOSITORY_MUTATION
WORKSPACE_CLIENT_MUTATION
RUNTIME_MUTATION
PROVIDER_MUTATION
CREDENTIAL_MUTATION
PRODUCTION_MUTATION
```

例:
- `git fetch`, temporary checkout/detach, branch switchは `REVERSIBLE_LOCAL_MUTATION`。
- config/file writeは後で戻してもmutation。
- health/readback callは、そのOperation自体にside effectが無い場合だけread-only。

## 5. Authorization Scope

Mutation permissionはCurrent Task / change unit / target operationへscopeする。過去Taskや隣接Taskのpermissionをcarry-forwardしない。

Server operationを実行できることと、実行してよいことは別状態である。

## 6. Multi-task / Multi-worker Safety

複数Project、Agent、change unitが同時進行し得る前提で扱う。

- write/commit/runtime operation前にexact change unitを識別する。
- unrelated uncommitted diffをstage / overwriteしない。
- intended diffを分離できない場合はauto-commitしない。
- 同じGit index / client config / shared runtime stateを変更するwriterはserializeするかfail closedする。
- shared checkoutを別Taskへ影響する形でswitch/reset/rebaseしない。
- readbackだけならworking tree mutationよりGit object/API inspectionを優先する。

## 7. Exit Status / Partial Apply

outer commandの成功表示でprimary operation failureを隠さない。

- primary operationのreal return codeを保持する。
- 複数required operationがある場合はmaterial resultを個別に保持する。
- 前段Mutation成功後に後段required stepが失敗した場合、rollback/recoveryを実測確認できない限り `PARTIAL` とする。
- transaction/rollback semanticsが無いmulti-step workflowをatomicと呼ばない。
- recovery instructionはrecovery evidenceではない。

## 8. Output / Diagnostic Budget

Server command / helperはunbounded outputをdefaultで出さない。

- inventory/logはcount、failing identifier、bounded excerptを優先する。
- 大量diagnosticは必要時だけtemporary fileへ退避する。
- acceptance判定に必要なEvidenceだけを返す。
- output短縮のためにfailure evidenceを隠さない。
- Secret / Token / credential値をdiagnosticへ出さない。

## 9. Interruption / Pending-State Recovery

Command process interruption、tool response interruption、network failure、async operationの `queued / in_progress` は、それだけでunderlying operationの成功・失敗・未実行を証明しない。

- Current acceptanceに必要なCI / async checkがquery可能なら、bounded pollingでterminal stateまで確認する。
- indefinite waitは禁止し、上限到達時はrun/job/request IDとpending stateを保持する。
- interruption後はexact repository/PR HEAD、commit、run/job/request ID、Runtime/Provider readback等のdurable stateから再開点を復元する。
- previous mutationが `NOT_APPLIED / APPLIED / PARTIAL / UNKNOWN` のどれかを確認する前に同じmutationをblind retryしない。
- stable run/job/request IDがある場合はduplicate operationより既存IDの追跡を優先する。

## 10. Completion Boundary

`PRE_EXECUTION_COMPLETE=YES` は、外部Operationを安全に実行できるところまでtarget/action/authorization/verify pathが確定したことを意味する。実行済みではない。

実行後はreturned evidenceからのみstateを昇格する。Command発行だけでServer/Provider/Runtime/Production PASSへ進めない。

Evidence不足やdiagnostic contradictionがある場合は `UNKNOWN / NOT_VERIFIED / PARTIAL` を維持する。

## 11. Invariants

- parent interactive shellを維持する。
- reversible local Git mutationをpure read-onlyと表現しない。
- 別Taskのdiffをautomated commitへ混ぜない。
- same-target writerはserializeするかfail closedする。
- credential値をoutputへ出さない。
- partial mutationをfinal success printで隠さない。
- execution / verification / PASSをreturned evidence無しで主張しない。
- interruption後はdurable target stateをreadbackしてからmutation retryする。
- server-core mutation permissionとServer operation permissionを別境界として扱う。
