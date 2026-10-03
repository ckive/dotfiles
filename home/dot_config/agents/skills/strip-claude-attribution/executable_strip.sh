#!/usr/bin/env bash
# strip.sh [--apply] [repo] -- remove Claude attribution lines from commit messages.
# Dry run by default. --apply rewrites every local branch and tag, after writing a backup bundle.
set -euo pipefail

apply=0 repo=.
for a in "$@"; do
  case $a in
    --apply) apply=1 ;;
    -h | --help) sed -n 2,3p "$0"; exit 0 ;;
    *) repo=$a ;;
  esac
done
cd "$repo"
top=$(git rev-parse --show-toplevel)
name=$(basename "$top")

# Keep the three copies of the pattern in step: git --grep (detect), perl (rewrite), verify.
grep_re='^(co-authored-by:.*(claude|anthropic)|.*generated with \[?claude code)'
perl_filter='s/^co-authored-by:.*(?:claude|anthropic).*\n?//gim; s/^.*generated with \[?claude code.*\n?//gim; s/\s+\z/\n/'

hits=$(git log --branches --tags -i -E --grep="$grep_re" --format='%h %ad %s' --date=short)
count=$(printf '%s' "$hits" | grep -c . || true)
echo "$name: $count commit(s) carry Claude attribution"
[ "$count" -eq 0 ] && exit 0
printf '%s\n' "$hits"

pushed=$(git log --branches --tags -i -E --grep="$grep_re" --format=%H |
  while read -r c; do git branch -r --contains "$c" | grep -q . && echo "$c"; done | grep -c . || true)
first=$(git log --branches --tags -i -E --grep="$grep_re" --format=%H | tail -1)
rewritten=$(git rev-list --count "$first"^..HEAD 2>/dev/null || git rev-list --count HEAD)
echo
echo "Rewriting changes the hash of ~$rewritten commit(s) on HEAD's line (everything since $(git rev-parse --short "$first"))."
[ "$pushed" -gt 0 ] && echo "WARNING: $pushed of them are already on a remote: needs push --force-with-lease; protected branches will refuse."
git log --branches --tags --format=%G? | grep -qv N && echo "WARNING: rewritten commits that were signed lose their signatures."

if [ "$apply" -eq 0 ]; then
  echo; echo "Dry run. Re-run with --apply to rewrite."
  exit 0
fi

[ -n "$(git status --porcelain --untracked-files=no)" ] && { echo "Refusing: tracked changes in the working tree. Commit or stash first." >&2; exit 1; }
[ "$(git worktree list | wc -l)" -gt 1 ] && { echo "Refusing: other worktrees exist; land or remove them first." >&2; exit 1; }

backup_dir="$HOME/.cache/strip-claude-attribution"
mkdir -p "$backup_dir"
bundle="$backup_dir/$name-$(date -u +%Y%m%dT%H%M%SZ).bundle"
git bundle create "$bundle" --branches --tags
echo "Backup: $bundle  (restore: git clone $bundle)"

FILTER_BRANCH_SQUELCH_WARNING=1 git filter-branch -f \
  --msg-filter "perl -0777 -pe '$perl_filter'" \
  --tag-name-filter cat -- --branches --tags 2>&1 | tr '\r' '\n' | grep -v '^Rewrite ' | grep . || true

git for-each-ref --format='%(refname)' refs/original | xargs -n1 git update-ref -d
left=$(git log --branches --tags -i -E --grep="$grep_re" --format=%h | grep -c . || true)
echo "Done. Commits still carrying attribution: $left"
