# Disk Usage Breakdown - RockchipLlama

## Total Working Directory: 12.7 GB

### Breakdown by Category

#### Working Files (NOT in git) - 8.5 GB
```
7.4 GB  - models/               ← Your actual model files (NOT TRACKED)
  ├── 5.0 GB - qwen3-4b/*.rkllm
  ├── 1.6 GB - gemma3-1b/*.rkllm  
  └── 909 MB - qwen3-0.6b/*.rkllm

118 MB  - venv/                  ← Python virtual env (NOT TRACKED)
33 MB   - cache/                 ← Binary cache files (NOT TRACKED)
  └── 33 MB - system.rkllm_cache
```

#### Git Repository - 4.6 GB
```
4.6 GB  - .git/                  ← Git history (WILL BE PUSHED)
  └── Contains deleted 5GB model in history from earlier today
```

#### Submodule - 625 MB
```
625 MB  - external/rknn-llm/     ← Git submodule (REFERENCE ONLY)
```

#### Source Code - ~2 MB
```
424 KB - docs/
380 KB - benchmarks/
292 KB - src/
120 KB - scripts/
32 KB  - config/
~20 KB - test files, configs, README
```

## What Gets Pushed to GitHub

**Size: 4.14 GB** (git pack size)

**Contents:**
- ✅ Source code (~2 MB)
- ✅ Documentation
- ✅ Submodule reference (not the files, just the commit hash)
- ❌ Models (excluded by .gitignore)
- ❌ Cache (excluded by .gitignore)
- ❌ venv (excluded by .gitignore)
- ⚠️  **LARGE FILE IN HISTORY**: 5GB qwen3-4b model that was committed and then deleted

## The Problem

**The same 5GB model exists in TWO places:**

1. **Git history** (commit 5db318a):
   ```
   models/Qwen3-4B-Instruct-2507-rk3588-w8a8-opt-0-hybrid-ratio-0.0-16k.rkllm
   Status: Committed, then deleted in commit 5e4da54
   Impact: 4.14 GB git pack size
   ```

2. **Working directory** (NOT tracked):
   ```
   models/qwen3-4b/Qwen3-4B-Instruct-2507-rk3588-w8a8-opt-0-hybrid-ratio-0.0-16k.rkllm
   Status: On disk, ignored by .gitignore
   Impact: 5 GB disk usage
   ```

**Total waste: ~5 GB in git history that shouldn't be there**

## Solution

Clean git history to remove the large file:

```bash
# Option 1: Install git-filter-repo (best tool)
pip3 install git-filter-repo

# Remove the large file from all history
git filter-repo --path models/Qwen3-4B-Instruct-2507-rk3588-w8a8-opt-0-hybrid-ratio-0.0-16k.rkllm --invert-paths

# Force push clean history
git push -f origin main
```

**Result after cleanup:**
- .git size: ~20 MB (instead of 4.6 GB)
- Push size: ~20 MB (instead of 4.14 GB)
- Working directory: Still 7.4 GB (your models), but NOT pushed

## Why This Happened

When the model was first committed (earlier today), it was at the root:
```
models/Qwen3-4B-Instruct-2507-rk3588-w8a8-opt-0-hybrid-ratio-0.0-16k.rkllm
```

Later it was reorganized into subfolders:
```
models/qwen3-4b/Qwen3-4B-Instruct-2507-rk3588-w8a8-opt-0-hybrid-ratio-0.0-16k.rkllm
```

Git deleted it from tracking but kept it in history, bloating the repository.

## Verification

Check what would be pushed:
```bash
git count-objects -vH
# Shows: size-pack: 4.14 GiB

git ls-files | grep -E "\.rkllm$"
# Shows: (nothing - models not tracked)

du -sh .git
# Shows: 4.6G (includes pack + refs + logs)
```

## Recommendation

**Clean the history before pushing!** Otherwise:
- ❌ Slow pushes (uploading 4 GB)
- ❌ Slow clones (downloading 4 GB)  
- ❌ GitHub may reject >5 GB repos
- ❌ Wasted storage on every clone

After cleanup:
- ✅ Fast pushes (~20 MB)
- ✅ Fast clones (~20 MB)
- ✅ Clean repository
- ✅ Models stay local (not in git)
