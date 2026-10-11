# GITHUB FREE MAX

## 目的
GitHub無料枠で、AI開発の効率と安全性を最大化する。

## リポジトリ内で有効化済み
- `.github/workflows/server-core-guard.yml`: 軽量CI
- `.github/dependabot.yml`: GitHub Actions用Dependabot
- `.github/pull_request_template.md`: PR標準化
- `.github/ISSUE_TEMPLATE/ai-task.yml`: AI作業Issueテンプレート
- `scripts/ai-auto-commit.sh`: AI作業後の自動commit / push

## GitHub画面で推奨する設定
GitHub CLIが未導入の環境では、次をGitHub画面から設定する。

### Actions
- Actionsを有効化する。
- Workflow permissionsは原則 `Read repository contents permission` にする。
- GitHub ActionsによるPR作成を使う場合だけ、`Allow GitHub Actions to create and approve pull requests` を有効化する。

### Branch / Rules
public repositoryでrulesetsが使える場合:

- `main` を対象にrulesetを作成する。
- `server-core-guard` の成功を必須にする。
- force pushを禁止する。
- deletionを禁止する。
- 実装変更はPR経由を優先する。

private repositoryで無料枠の制約がある場合:

- 軽量CIと自動commitを優先する。
- main直pushは、管理者が許可した正本更新または小規模文書更新に限定する。

### Private repository — verified platform limit (2026-10-11)

GitHub API readback on `G-ACE-inc/server-core` (private, org plan `free`):

- `GET /repos/G-ACE-inc/server-core/branches/main/protection` → **403** — "Upgrade to GitHub Pro or make this repository public to enable this feature."
- `POST /repos/G-ACE-inc/server-core/rulesets` → **403** (same message).
- GraphQL `branchProtectionRules` and `rulesets` on `main` → **empty**.

Therefore native `protected=true` branch protection and required-status-check merge gates are **not available** on the current plan while the repository stays private. Work Routine CU #40 PR guards (`server-core-guard` pull_request steps) do not run on a direct `main` push; only the generic push job runs unless the scoped main-push admission step is present.

Mitigations within existing tooling (no new Workflow file):

1. Prefer PR merge for CU #40 gate Source paths; keep `scripts/ai-auto-commit.sh` on feature branches when practical.
2. Existing `server-core-guard` **push** admission fails CI when CU #40 gate paths land on `main` without an associated merged PR (post-push signal; does not revert Git).
3. Hard block before push requires GitHub Pro/Team (private rulesets/protection) or making the repository public under the documented ruleset path above.


### Security
- Dependency graphを有効化する。
- Dependabot alertsを有効化する。
- Dependabot security updatesを有効化する。
- 利用可能な場合はsecret scanningを有効化する。

## 無料枠を浪費しない方針
- CIは軽量な文書・secret・表記チェックに限定する。
- cron実行は最小化し、Dependabotは週1回にする。
- self-hosted runnerが使える場合は、重い検証をそちらへ寄せる。
- public repositoryでは標準GitHub-hosted runnerのActionsを活用する。
- private repositoryではActions分数を消費するため、重い処理を避ける。

## 公式参照
- GitHub Actions billing and usage: https://docs.github.com/en/actions/concepts/billing-and-usage
- GITHUB_TOKEN authentication: https://docs.github.com/en/actions/tutorials/authenticate-with-github_token
- GitHub Actions repository settings: https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/enabling-features-for-your-repository/managing-github-actions-settings-for-a-repository
- Dependabot version updates: https://docs.github.com/en/code-security/how-tos/secure-your-supply-chain/secure-your-dependencies/configure-version-updates
- Repository rulesets: https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/creating-rulesets-for-a-repository
- Secure use of GitHub Actions: https://docs.github.com/en/actions/reference/security/secure-use
