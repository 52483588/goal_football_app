#!/usr/bin/env bash
# 本地取回脚本（方案 A 配套）
# 只拉取"本地缺失的 blob"，速度快、可断点续拉、离线多久都只补差额。
#
# 用法：
#   ./pull.sh            # 默认分支 main
#   ./pull.sh master     # 指定分支
#
# ⚠️ 注意：远端是单提交 force-push 快照，本地【不要】用普通 git pull，
#          一律用本脚本（git fetch + git reset --hard）。
# ⚠️ 切换方案后请先做一次【全新 clone】，旧仓库的胖历史不会自动瘦身。

set -e

BRANCH="${1:-main}"

echo "▶ 拉取远端快照（分支：$BRANCH）..."
git fetch origin
git reset --hard "origin/$BRANCH"

echo "✅ 已同步到最新快照。"
echo "   归档目录：HisData/<时间戳>/   （每个文件夹即一小时的全量 XML）"

# ---------- 可选：清理本地过旧的 HisData 文件夹 ----------
# ⚠️ 本地是你的【永久归档】。默认 CLEANUP_DAYS=0（不清理），以免误删历史。
#    真正防止 GitHub 仓库膨胀的是工作流里的「远程清理」（默认 3 天），本地清理只为了省磁盘。
#    若确实要腾本地空间，把下面改成 3（注意：超过 3 天的本地归档将被删除，不再可回溯）。
CLEANUP_DAYS=0
if [ "$CLEANUP_DAYS" -gt 0 ]; then
  echo "▶ 清理本地超过 ${CLEANUP_DAYS} 天的 HisData 文件夹..."
  CUTOFF=$(date -d "-${CLEANUP_DAYS} days" +%s)
  found=0
  for d in HisData/*/; do
    [ -d "$d" ] || continue
    ts=$(basename "$d")
    if [[ "$ts" =~ ^[0-9]{8}_[0-9]{6}$ ]]; then
      epoch=$(date -d "${ts:0:4}-${ts:4:2}-${ts:6:2} ${ts:9:2}:${ts:11:2}:${ts:13:2}" +%s 2>/dev/null || true)
      if [ -n "$epoch" ] && [ "$epoch" -lt "$CUTOFF" ]; then
        echo "  🗑 删除 $d"
        rm -rf "$d"
        found=1
      fi
    fi
  done
  [ "$found" -eq 0 ] && echo "  ℹ️ 没有超过 ${CLEANUP_DAYS} 天的文件夹"
fi
