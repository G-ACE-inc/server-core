## 変更目的
- TBD

## 対象責務と再利用
- 対象Moduleまたは対象責務:
- 再利用候補:
- 入力・出力への影響:
- 直接依存と制約への影響:

## Mutation Boundary
- TARGET_REPOSITORY:
- MUTATION_REPOSITORIES:
- READ_ONLY_REPOSITORIES:
- server-core mutation authorization: YES / NO / N/A
- Runtime / Provider / Secret / Production mutation: NONE / Master承認済みscopeを記載

このTemplateへの記入やPR作成自体をmutation authorizationとして扱わない。server-core変更はserver-core自体へのMasterの明示許可が成立している場合だけ行う。

## 変更内容
- TBD

## 検証結果
- 入力・実行条件:
- 期待出力:
- 変更された状態:
- 維持した状態:
- 既存機能で維持した結果:
- 異常入力または主要失敗条件の結果:

## 実行確認
- [ ] `git diff` で変更範囲を確認した
- [ ] 変更対象と対象外が一致している
- [ ] current Repositoryとmutation targetを照合した
- [ ] 秘密情報をGit管理外で扱っている
- [ ] 新規Code生成前に同じ責務を持つ既存資産を確認した
- [ ] 既存資産を利用しない場合の具体的理由を確認した
- [ ] 物理構造をProjectの規模、再利用範囲、依存、検証、運用上の実益で決定した
- [ ] 新規Moduleが再利用または修正コストを下げることを確認した
- [ ] Moduleの公開契約、依存方向、所有者を確認した
- [ ] 設計情報を1つの正本へ集約した
- [ ] 期待出力、状態変化、主要失敗条件、回帰結果を確認した
- [ ] Commit / Push / Merge / Deploy / Runtime / Production状態を分離して記録した
- [ ] main/PR merge、Production deploy/起動/公開/切替、Provider/Secret mutation、稼働Serviceのstop/restart/recreateを伴う場合はMasterの明示指示を確認した

## 補足
- TBD
