List recent Claude Code sessions for this project so you can pick one to continue.

## Instructions

1. **List recent sessions** — run the following bash command to extract the last 10 conversations for this project:

```bash
PROJECT_DIR="$HOME/.claude/projects/$(echo "$PWD" | sed 's/[^a-zA-Z0-9]/-/g')"
# Sort by file BIRTH time, not mtime — iCloud sync scrambles mtimes.
# Inline $(...) inside `for` so word splitting works under both bash and zsh.
for f in $(stat -f '%SB %N' -t '%s' "$PROJECT_DIR"/*.jsonl 2>/dev/null \
  | sort -rn | head -25 | sed 's/^[0-9]* //'); do
  fname="${f##*/}"
  id="${fname%.jsonl}"
  mod_date=$(stat -f '%SB' -t '%Y-%m-%d %H:%M' "$f" 2>/dev/null)
  first_msg=$(/usr/bin/python3 -c "
import json, sys
with open('$f') as fh:
    for line in fh:
        try:
            obj = json.loads(line)
            if obj.get('type') == 'user':
                content = obj.get('message', {}).get('content', '')
                if isinstance(content, list):
                    for c in content:
                        if isinstance(c, dict) and c.get('type') == 'text':
                            t = c['text'].strip().split(chr(10))[0][:80]
                            if t and not t.startswith('<'):
                                print(t)
                                sys.exit()
                elif isinstance(content, str) and content.strip():
                    t = content.strip().split(chr(10))[0][:80]
                    if t and not t.startswith('<'):
                        print(t)
                        sys.exit()
        except Exception: pass
print('(slash command / session start)')
" 2>/dev/null)
  echo "$mod_date | $id | $first_msg"
done
```

2. **Format the output** as a table. Use this format:

```
## Recent Sessions

| # | Date | First Message | Resume Command |
|---|------|---------------|----------------|
| 1 | YYYY-MM-DD HH:MM | first user message... | `claude -r SESSION_ID` |
| 2 | ... | ... | ... |
```

- Sorted by most recent first (the bash output is already sorted by modification time)
- Truncate long messages to ~60 chars with `...`
- The session ID is the UUID filename without `.jsonl`

3. **If `$ARGUMENTS` is provided**, filter the session list — only show sessions whose first message matches the argument (case-insensitive substring match). If no matches, show the full list and note that no sessions matched the filter.

4. **Show the resume instructions** after the table:

```
**To resume a session:**
- Exit this session first: `Ctrl+C` or type `exit`
- Then run: `claude -r <session-id>`
- Or resume the most recent: `claude -c`
- Or use the interactive picker: `claude -r`
```

5. **Keep it concise.** This is a quick reference, not a context dump. Just the table and instructions.

## Input
$ARGUMENTS
