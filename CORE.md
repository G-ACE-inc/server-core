# LibralCore Core Philosophy
Version: 1.1

## LibralCore
LibralCoreはシステムではない。開発思想である。

## 目的
再利用 / 分離 / 着脱 / 蓄積 / 継承

## 第一原則：再利用可能でなければならない。
## 第二原則：すべてをModule化する（1 Module = 1責務）。
## 第三原則：Moduleは着脱可能であること。
## 第四原則：依存関係を最小化し疎結合を維持する。
## 第五原則：知識を捨てず、学習結果はKBへ蓄積する。
## 第六原則：構成図を絶対とする（STRUCTURE.mdに従う）。
## 第七原則：削除ではなく退避する（不要ファイルは必ず archive/ へ）。

## 第八原則：5層アーキテクチャを必須とする。

本原則は第一原則〜第七原則を置き換えない。再利用可能性と1責務を満たすため、Layer 1の部品は単独の業務責務を持つならLayer 2のModuleとして扱う。

### 5層定義
- Layer 1：部品。小さな共通処理。例: Hash生成、時刻正規化、秘密情報除去。
- Layer 2：Module。単独で意味のある最小機能。例: 重複判定、Source検証、正本保存。
- Layer 3：機能束。複数Moduleを順序統合する単位。例: KB登録Pipeline、検索Pipeline。
- Layer 4：System。astera-kbサービス全体。
- Layer 5：Application。管理UI、利用画面、外部向け製品。

### 必須制約
- 5層の名称、順序、責務を省略、改名、統合、飛び越ししてはならない。
- 依存方向は高層から低層への一方向のみとし、低層は高層をimportしない。
- Layer 1はLayer 2以上をimportしない。
- Layer 2はLayer 3以上をimportしない。
- Layer 3はLayer 4以上をimportしない。
- Layer 4はLayer 5以上をimportしない。
- 循環依存、層の逆転、構成図にない越境実装は禁止する。
- この原則に違反する実装、文書、構成図は正規仕様ではない。

## AI運用思想
AIは「忘れる」「推測する」「暴走する」前提で運用する。

## 開発フロー
目的 ➔ 設計 ➔ 構造（構成図） ➔ 実装 ➔ 検証 ➔ 運用
順番を飛ばさない。

## Project定義
Projectは完成品ではなく、Module集合体である。
対象: KAGURA, KAGRRA, TGAXIS, AEGIS, EntryBot, KB 等

## 最重要
思想を守れない実装は禁止。速度より構造を優先する。
