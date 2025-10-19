# Documentation Index

This file provides an overview of all documentation in the RockchipLlama project.

## 📋 Documentation Guidelines

**All documentation files are kept in the `docs/` folder.**

AI assistants should:
1. ✅ Keep all `.md` documentation files in `docs/` folder
2. ✅ Update existing documentation rather than creating new phase files
3. ✅ Use `copilot.md` as the central design document and session log
4. ✅ Update session notes at the end of each work session
5. ❌ Do NOT create separate PHASE*.md files - consolidate into copilot.md
6. ❌ Do NOT create separate SUMMARY.md files - update copilot.md instead

## 📚 Documentation Files

### Core Documentation

- **[copilot.md](./copilot.md)** (28KB)
  - Central design document
  - Session notes and progress tracking
  - Architecture decisions
  - Implementation guidelines for AI assistants

- **[rkllm.md](./rkllm.md)** (36KB)
  - RKLLM runtime API documentation
  - Parameter reference
  - Performance characteristics
  - Technical implementation details

### User Guides

- **[QUICKSTART.md](./QUICKSTART.md)** (5.2KB)
  - Getting started guide
  - Installation instructions
  - First-run setup
  - Basic usage examples

- **[MODEL_MANAGEMENT.md](./MODEL_MANAGEMENT.md)** (6.3KB)
  - Model lifecycle management
  - Loading/unloading models
  - API endpoint reference
  - Usage examples (curl, Python, OpenAI client)

- **[BENCHMARKING.md](./BENCHMARKING.md)** (11KB)
  - Performance benchmarking guide
  - Metrics explanation (TTFT, tokens/sec)
  - Expected RK3588 performance values
  - Troubleshooting and optimization
  - Best practices

- **[BENCHMARK_QUICKREF.md](./BENCHMARK_QUICKREF.md)** (3.8KB)
  - Quick reference card for benchmarks
  - One-line commands
  - Metrics cheat sheet
  - Troubleshooting quick guide

### Implementation Summaries

- **[PHASE2_SUMMARY.md](./PHASE2_SUMMARY.md)** (5.1KB)
  - Phase 2 completion summary
  - FastAPI server implementation details
  - Architecture overview

- **[BENCHMARK_SUMMARY.md](./BENCHMARK_SUMMARY.md)** (10KB)
  - Benchmarking system implementation
  - Technical details
  - File descriptions
  - Integration information

### Reference Data

- **[benchmark_prompts.json](./benchmark_prompts.json)** (5.8KB)
  - Performance test prompts (5)
  - Quality test prompts (5)
  - Test categories and metadata

- **[model-requirements.md](./model-requirements.md)** (7.4KB)
  - Model selection guide
  - Hardware requirements
  - Performance expectations

## 🗂️ Documentation Organization

```
docs/
├── copilot.md              # Central design doc (UPDATE THIS!)
├── rkllm.md                # RKLLM technical docs
│
├── QUICKSTART.md           # User: Getting started
├── MODEL_MANAGEMENT.md     # User: Model lifecycle
├── BENCHMARKING.md         # User: Performance testing
├── BENCHMARK_QUICKREF.md   # User: Quick reference
│
├── PHASE2_SUMMARY.md       # Implementation summary
├── BENCHMARK_SUMMARY.md    # Implementation summary
│
├── benchmark_prompts.json  # Test data
└── model-requirements.md   # Reference
```

## 🔄 When to Update Which File

| File | Update When |
|------|-------------|
| `copilot.md` | Design decisions, session notes, phase progress, architecture changes |
| `QUICKSTART.md` | Setup process changes, new installation steps |
| `MODEL_MANAGEMENT.md` | New model management features, API changes |
| `BENCHMARKING.md` | New benchmark features, metrics, best practices |
| `rkllm.md` | RKLLM runtime updates, new capabilities discovered |
| `*_SUMMARY.md` | Major phase completions (rarely updated) |

## 📝 Best Practices

1. **Always check existing docs first** - Don't create new files if existing ones can be updated
2. **Use copilot.md for session tracking** - It's the central log
3. **Keep user guides focused** - Each guide should have a clear purpose
4. **Update README.md links** - When moving/renaming docs, update the main README
5. **Maintain this index** - Add new docs here when created

## 🔗 Quick Links

From project root:
- Main README: `../README.md`
- API Server: `../src/main.py`
- Tests & Benchmarks: `../scripts/`
- Server startup: `../start_server.sh`

## 📊 Documentation Stats

Total documentation: ~120 KB
Number of markdown files: 9
Number of data files: 1
Last updated: October 19, 2025
