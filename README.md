# envdiff

> Diff environment variable sets across staging and production configs.

---

## Installation

```bash
pip install envdiff
```

Or install from source:

```bash
git clone https://github.com/yourname/envdiff.git
cd envdiff && pip install -e .
```

---

## Usage

Compare two `.env` files or config sources directly from the command line:

```bash
envdiff staging.env production.env
```

**Example output:**

```
+ API_TIMEOUT=30        # only in production
- DEBUG=true            # only in staging
~ DATABASE_URL          # value differs between files
```

You can also use it programmatically:

```python
from envdiff import diff_envs

results = diff_envs("staging.env", "production.env")
for change in results:
    print(change)
```

### Options

| Flag | Description |
|------|-------------|
| `--only-missing` | Show only keys missing from one side |
| `--only-changed` | Show only keys present in both but with different values |
| `--format json` | Output results as JSON |

---

## License

This project is licensed under the [MIT License](LICENSE).