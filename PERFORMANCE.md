# LTM Performance Benchmarks

Performance analysis of LTM operations, measured on a standard development machine.

## Summary

| Operation | Mean | Throughput | Status |
|-----------|------|------------|--------|
| Sign Memory | 0.013ms | 77,545 ops/sec | Excellent |
| Verify Signature | 0.017ms | 57,782 ops/sec | Excellent |
| Recall by ID | 0.48ms | 2,093 ops/sec | Fast |
| Search (full-text) | 1.54ms | 650 ops/sec | Fast |
| Recall by Kind | 1.70ms | 586 ops/sec | Fast |
| Decay Processing | 3.65ms | 274 ops/sec | Fast |
| Create Memory | 4.87ms | 205 ops/sec | Good |
| **Injection (20 mem)** | ~80ms | 12 ops/sec | Good (optimized) |
| **Injection (500 mem)** | ~2,900ms | 0.3 ops/sec | Acceptable |

## Detailed Results

### Fast Operations (No optimization needed)

#### Signature Operations
```
Signature Creation:
  Mean: 0.013ms | Median: 0.012ms
  Throughput: 77,545 ops/sec

Signature Verification:
  Mean: 0.017ms | Median: 0.011ms
  Throughput: 57,782 ops/sec
```
HMAC-SHA256 is extremely fast. No concerns here.

#### Database Operations
```
Memory Recall (by ID):
  Mean: 0.48ms | Median: 0.41ms
  Throughput: 2,093 ops/sec

Memory Search (full-text):
  Mean: 1.54ms | Median: 1.41ms
  Throughput: 650 ops/sec

Memory Recall (by kind):
  Mean: 1.70ms | Median: 1.58ms
  Throughput: 586 ops/sec

Decay Processing (100 memories):
  Mean: 3.65ms | Median: 3.38ms
  Throughput: 274 ops/sec

Memory Creation (single):
  Mean: 4.87ms | Median: 4.88ms
  Throughput: 205 ops/sec
```
SQLite performs well for all database operations.

### Injection Performance (After Token Caching Optimization)

#### Memory Injection
```
Injection (20 memories):
  Mean: ~80ms | Median: ~80ms
  Throughput: 12 ops/sec
  Per memory: ~4ms (save_memory for last_accessed update)

Injection (500 memories, budget-limited):
  Mean: ~2,900ms | Median: ~2,900ms
  Throughput: 0.3 ops/sec
  Note: ~80-100 memories fit in 20k token budget
```

#### Full Session Simulation
```
Full Session (50 existing + 3 new memories):
  Mean: ~650ms | Median: ~635ms
  Throughput: 1.5 ops/sec
```

## Optimization History

### Token Caching (Implemented)

**Problem:** tiktoken was being called for every memory during injection (~6ms per call).

**Solution:** Cache `token_count` in the database when saving memories.

**Results:**
- Token counting during injection: **6ms → 0ms** (uses cached value)
- New bottleneck: `save_memory()` to update `last_accessed` (~4ms per memory)

Before optimization:
```
Injection (20 memories): 125ms
Injection (500 memories): 3,097ms
```

After optimization:
```
Injection (20 memories): ~80ms (36% faster)
Injection (500 memories): ~2,900ms (6% faster)
```

### Remaining Bottleneck: save_memory()

Each injected memory triggers a `save_memory()` call to update `last_accessed`.
This is a design choice that enables accurate access tracking for decay.

**Potential future optimizations:**
1. Batch updates for `last_accessed`
2. Skip save during injection (less accurate tracking)
3. Defer updates to session end

## Token Counting Details

We use tiktoken (`cl100k_base` encoding) because:
- It has ~70% vocabulary overlap with Claude's tokenizer
- It's the standard for OpenAI-compatible token counting
- It's offline (no API calls required)

Token counts are calculated once when memories are saved, then reused
during injection. If no cached count exists, a fast approximation
(`len(text) // 4`) is used.

## Verdict

**Python is suitable for LTM.**

Core operations (create, recall, search, sign) are all <5ms. Injection
is dominated by database I/O for `last_accessed` updates, not by token
counting. A typical session (~50 memories) takes ~600ms for injection,
which is acceptable UX for a session start.

## Running Benchmarks

```bash
# Run all performance tests with output
uv run pytest tests/test_performance.py -v -s

# Run just the summary
uv run pytest tests/test_performance.py::TestPerformanceSummary -v -s
```

## Test Environment

- Python 3.13
- SQLite 3.x
- tiktoken (cl100k_base encoding)
- pytest with timing assertions

---

*Last updated: 2025-12-20*
