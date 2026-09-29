#!/bin/sh
# Build the public history of the Playoff Jimmy episode from the private working repository.
#
#   studio/tools/public_repo.sh <empty or disposable directory>
#
# Clones main, then rewrites every commit to keep only the episode, the renderer, the tools and
# their tests, and to drop third-party material in every commit: the saved Basketball-Reference
# pages, the team media guides and anything extracted or rendered from them, the probe downloads,
# and the download scripts (Sports Reference does not permit scripted access or redistribution;
# the numbers themselves are facts, published with a citation). Commits left empty are dropped.
# The rewrite is deterministic, so rerunning it later reproduces the same hashes for the same
# commits and a push of the result is a fast-forward.
set -eu
SRC=$(git -C "$(dirname "$0")" rev-parse --show-toplevel)
WORK=$1
rm -rf "$WORK"
git clone --quiet --no-local --single-branch --branch main "$SRC" "$WORK"
cd "$WORK"
git remote remove origin

KEEP='^(README\.md|LICENSE|\.gitignore|studio/episodes/playoff-jimmy/|studio/render/|studio/tools/|tests/test_(analysis|analysis_v2|story_check|render|assembly)\.py$)'
DROP='^studio/episodes/playoff-jimmy/(data/(raw|extracted|qa|probes)/|analysis/(fetch_bbref|probe_sources)\.py$)'
export KEEP DROP
# Commits carry the GitHub no-reply address, not a personal email.
NOREPLY=160076610+bilguutei2k@users.noreply.github.com
export NOREPLY
FILTER_BRANCH_SQUELCH_WARNING=1 git filter-branch --prune-empty --tag-name-filter cat \
  --env-filter 'GIT_AUTHOR_EMAIL=$NOREPLY; GIT_COMMITTER_EMAIL=$NOREPLY; export GIT_AUTHOR_EMAIL GIT_COMMITTER_EMAIL' \
  --index-filter '
  list=$(mktemp)
  git ls-files | { grep -vE "$KEEP" || true; } > "$list"
  git ls-files | { grep -E "$DROP" || true; } >> "$list"
  if [ -s "$list" ]; then git rm -q --cached --ignore-unmatch --pathspec-from-file="$list"; fi
  rm -f "$list"
' -- --all > /dev/null
rm -rf .git/refs/original
git reflog expire --expire=now --all
git gc --quiet --prune=now
echo "Public history in $WORK: $(git rev-list --count main) commits"
