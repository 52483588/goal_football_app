# XML 快照备份（方案 A：单提交快照，仓库不膨胀）

GitHub Action 每小时从 macauslot.com 下载 8 个足球赔率 XML，归档进
`HisData/<时间戳>/`，然后 **把整段历史折叠成「单个根提交」+ force-push** 到仓库。
无论之前攒了多少小时的历史提交，每次都收敛为 1 个提交，blob 按内容去重只存一次
→ **不随小时数膨胀**（旧的 `add-and-commit` 长历史会被一次性压掉）。

## 为什么这样设计
- 你最关注**取回速度**和**不膨胀**。单提交快照 = 用 Git 协议传输（最快），
  且历史不增长。本地 `git fetch` 只传缺失 blob，速度恒定、不随时间退化。
- 你本地电脑时开时关（离线通常 ≤24h）：Action 在 GitHub 上 7×24 跑，
  数据全量常驻快照，上线只补差额，永不丢。

## 本地取回
```bash
./pull.sh            # 默认分支 main
./pull.sh master     # 指定分支
```
脚本等价于 `git fetch origin && git reset --hard origin/<分支>`。

## ⚠️ 关键约定
1. 本地**不要用普通 `git pull`**，必须用 `pull.sh`（force-push 会重写历史，普通 pull 会冲突）。
2. **切换方案后请做一次全新 `git clone`**：旧仓库已攒了一堆历史提交，
   force-push 不会自动瘦身本地，需重新克隆才能真正变小。
3. 任何其他 clone 也要 `git reset --hard origin/<分支>`，不能 pull。

## 瘦身（日后若仓库过大）
直接删除旧的 `HisData/<时间戳>/` 文件夹后再次让 Action 跑一次（或手动
`git commit --amend` + `git push --force-with-lease`），快照即变小。
因为历史只有 1 个提交，没有"历史里的旧大文件"需要 gc 清理。

## 文件说明
- `.github/workflows/xml-snapshot.yml`：每小时下载 + 归档 + 单提交 force-push。
- `pull.sh`：本地取回脚本。
