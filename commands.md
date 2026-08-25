# Commands

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Create QA Entries (Interactive)
```bash
# Run with default username (main)
python3 scripts/create_entry.py

# Run with custom username
python3 scripts/create_entry.py --username <username>
```
*Output files are saved to `output/<username>/001.json`, `002.json`, etc.*

### 3. Validate JSON Files
```bash
# Validate a single entry
python3 scripts/validate.py output/vadym/001.json

# Validate dataset examples
python3 scripts/validate.py schema/examples.json
```
