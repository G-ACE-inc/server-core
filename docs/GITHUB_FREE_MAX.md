# GITHUB FREE MAX

## Purpose

GitHubの利用Costを無駄に増やさず、G-ACEのAI開発に必要な安全性・追跡性・検証品質を維持する。

このDocumentは固定の料金表やPlan上限値の正本ではない。GitHubのPlan、billing、Actions quota、Security/Ruleset availability等の可変条件がTask判断に必要な場合は、その時点のGitHub公式情報またはRepository設定をreadbackする。

## Repository-side Efficiency Policy

server-coreでCurrent利用するGitHub側の主要仕組み:
- `.github/workflows/server-core-guard.yml` — Authority / Contract / safety regressionを軽量に検出する。
- `.github/workflows/server-core-behavior.yml` — Source変更で壊れ得るhelper / wiring / bounded behaviorを実行検証する。
- `.github/dependabot.yml` — GitHub Actions dependency更新を週1回・bounded PR数・grouped updateで確認する。
- `.github/pull_request_template.md` — Scope / verification / approval boundaryをPRへ残す。
- `.github/ISSUE_TEMPLATE/ai-task.yml` — AI TaskのScope / mutation boundaryを固定する。

CIやAutomationは「多いほど安全」と扱わない。Acceptanceと回帰防止に必要な検証だけを持ち、同じEvidenceを複数Workflowで理由なく重複計算しない。

## Cost / Resource Rule

- GitHub connector等、既に利用可能なAPI/Toolで完了できるreadbackやmetadata確認を優先し、同じ確認のためだけにServer/Workspace AIや重いCIを起動しない。
- CIはSource/Contract変更で壊れ得る重要InvariantとBehaviorへ集中させる。
- Scheduled jobは必要最小限にする。Current DependabotはGitHub Actions dependencyを週1回確認する。
- Dependabot PRはgroup化し、同時open数をbounded化する。
- 重いE2E / Runtime / Provider検証はAcceptanceに必要な場合だけ行い、文書変更だけを理由に無関係なRuntime検証を増やさない。
- Current CI Evidenceを再利用できる場合、同じSHA・同じ条件のWorkflowを理由なく再実行しない。
- 外部Wait / queued jobのPollingだけでAI TurnやGitHub Resourceを浪費しない。
- Cost削減のために必要なVerificationを削除・skipしない。

## GitHub Settings Boundary

Repository/Organization側のGitHub設定変更は、Source File変更とは別のProvider/Repository Settings mutationとして扱う。

次の設定を変更する必要がある場合は、Current Repository設定とGitHub公式仕様を確認し、Masterの承認Boundaryに従う。
- Actions permissions / workflow permissions
- Branch protection / rulesets
- Security feature settings
- Dependabot feature settings
- Secret scanning等のSecurity設定

Documentに推奨事項があること自体を、GitHub側設定変更の承認として扱わない。

## Dependabot Contract

Current Repository contract:

```text
ECOSYSTEM=github-actions
INTERVAL=weekly
DAY=monday
TIME=05:00
TIMEZONE=Asia/Tokyo
OPEN_PULL_REQUESTS_LIMIT=3
GROUP=github-actions
```

この設定はdependency updateの発見とPR作成をbounded化するためのRepository Source Contractであり、PRのMerge承認ではない。DependabotがPRを作成しても、通常のPR / CI / Merge boundaryを適用する。

## Verification

GitHub運用変更では必要範囲で次を分離して確認する。

```text
SOURCE_CONFIG
REMOTE_REPOSITORY_READBACK
PR
CI
REPOSITORY_SETTING
BILLING_OR_PLAN_CONDITION
```

Sourceに設定FileがあることだけでGitHub側featureが有効・利用可能・課金条件内と断定しない。

## Official references

可変仕様を判断するときはGitHub公式DocumentationをCurrent sourceとして確認する。
- GitHub Actions billing and usage
- GitHub Actions repository settings
- Dependabot version updates / options reference
- Repository rulesets
- Secure use of GitHub Actions

## Invariants

- GitHub利用Costの削減を理由に必要Testを消さない。
- 同じEvidenceを理由なく複数経路で再取得しない。
- Scheduled automationを無目的に増やさない。
- Plan固有の上限値やfeature availabilityを恒久値として固定しない。
- Repository Source変更とGitHub Provider/Settings mutationを混同しない。
- Dependabot PR作成をMerge承認と扱わない。
