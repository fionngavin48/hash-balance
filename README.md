# Hash Balance

**Hash Balance** is a fast distribution test tool for hash output uniformity. It uses a
chi-squared goodness-of-fit test to spot bucket bias in sharding, hash tables,
and custom reducers.

> **Disclaimer:** This is not a security test. Hash Balance is intended for research and education purposes only.
<img width="1437" height="900" alt="image" src="https://github.com/user-attachments/assets/c2659346-e4df-45b9-8ef6-2e4d97a8c4ca" />


## Featured modes

The interactive UI is built around selectable analysis modes. **This version ships with one mode:**

| Mode | Description |
|------|-------------|
| **Hash balance** | Chi-squared goodness-of-fit test for hash bucket uniformity |

Use **m) change mode** on the control panel to view available modes. Additional modes will be added in future releases.

`flawed_hash` wraps SHA-256 but forces bit 0 to zero, so only 128 of 256
possible values are reachable. `reference_hash` uses the first byte of SHA-256
as a near-ideal baseline for comparison.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Run tests

```bash
pytest
```

## Run the interactive analysis

**Quick start (no install needed):**

```bash
python3 run.py
```

**Or install the package first, then use the module command:**

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
python -m hash_balance.report
```

If you see `ModuleNotFoundError: No module named 'hash_balance'`, you are using
system Python without installing the package. Use `python3 run.py` instead, or
activate the virtualenv and run `pip install -e .` before `python -m ...`.

### What you can configure

- **Analysis mode** — hash balance (chi-squared goodness-of-fit); more modes coming later
- **Sample size** — how many inputs to hash
- **Bucket count** — simulates `hash(bytes) % bucket_count` for deployable routing
- **Input mode** — sequential integers, prefixed strings (`user:0`, `user:1`, ...), or deterministic random bytes
- **Chi² threshold** — auto-scales with bucket count, or set manually
- **Hash functions** — point at any callable `bytes -> int`

The default hash set includes the bundled examples:

- `hash_balance.flawed_hash:flawed_hash`
- `hash_balance.flawed_hash:reference_hash`

Use **Manage hash functions** to point at any callable that takes `bytes` and
returns an `int`. Paths can be:

- `package.module:function`
- `package.module.function`
- `path/to/file.py:function`

See `examples/custom_hashes.py` for a custom hash you can try:

```text
examples/custom_hashes.py:low_nibble_hash
```
