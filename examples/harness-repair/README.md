# harness-repair

`harness-repair` edits an agent harness and keeps an edit only when the train score goes up.

The harness is three files in one directory.

- `system.md` is the system prompt.
- `tools.json` lists the tools the agent may call.
- `done.md` tells the agent when to stop.

The scorer is not one of those files. The optimizer cannot change it.

## What this is not

Google Cloud AI Research describes a larger loop in RRSI (arXiv:2609.24972). The title is "Regularized Recursive Self-Improvement of Agent Harnesses". The paper says harness edits can overfit the tasks they train on. RRSI adds a shrinking edit budget, a critic, a noise floor, a token-cost rule and pruning. This tool has none of those. Scores in that paper are not scores from this tool.

[This post](https://x.com/akshay_pachaar/status/2123030996899774607) describes that plain loop. It reads failure traces, edits the prompt, tools and done check, and keeps a higher score. This page does not add further claims from that post.

## What you need

Python 3.9 or newer. No extra packages.

The offline example needs no key and no model CLI. A real agent needs one of these:

1. Claude Code, as `claude` on `PATH`.
2. Codex CLI, as `codex` on `PATH`.
3. An API key in the environment. See below.

## Try the example

The example prompt says not to use tools, so the mock fails every task. The mock then writes a prompt that uses the tools. The mock is scripted. It is not a model. From the repo:

```sh
bin/harness-repair optimize \
  --harness examples/harness-repair/harness \
  --tasks examples/harness-repair/tasks.jsonl \
  --runner command \
  --runner-cmd "python3 examples/harness-repair/mock_runner.py" \
  --max-iterations 1
```

The report prints the train score, the held-out score and the output directory. The source harness is not changed. History goes under `harness-repair-runs/<timestamp>/` unless you pass `--out`.

Copy the example:

```sh
bin/harness-repair init ./my-agent
```

`--dry-run` prints the plan. It calls no model and writes no files.

## Score without editing

```sh
bin/harness-repair run \
  --harness examples/harness-repair/harness \
  --tasks examples/harness-repair/tasks.jsonl \
  --runner command \
  --runner-cmd "python3 examples/harness-repair/mock_runner.py"
```

## Point it at your agent

`--runner command` runs your program once per model call. The program reads one JSON object on stdin. It writes one JSON object on stdout.

Request:

```json
{"role":"agent","system":"...","messages":[{"role":"user","content":"..."}],"tools":[]}
```

Reply:

```json
{"content":"ANSWER: 4","tool_calls":[],"usage":{"input_tokens":1,"output_tokens":1,"cost_usd":0}}
```

`tool_calls` is a list of `{id, name, arguments}`. This tool runs `calc` and `read_file` when `tools.json` sets `impl` to those names. Any other `impl` is rejected. There is no shell tool.

`--runner claude` runs `claude -p --output-format json`. The harness is passed with `--append-system-prompt`. Set `HARNESS_CLAUDE` if the binary is not on `PATH`. Claude uses its own tools. `calc` is not registered as a Claude tool. One Claude call is one turn.

`--runner codex` runs `codex exec --json --skip-git-repo-check --sandbox read-only`. Set `HARNESS_CODEX` if needed. The default sandbox is read-only. Set `HARNESS_CODEX_SANDBOX` to `workspace-write` or `danger-full-access` only when you mean to. Codex output parsing is best-effort. If your CLI differs, wrap it with `--runner command`.

`--runner api --provider openai` calls `POST $BASE/chat/completions`. The key is `OPENAI_API_KEY` or `HARNESS_API_KEY`. The base is `OPENAI_BASE_URL` or `HARNESS_API_BASE`. The default base is `https://api.openai.com/v1`. Set `--model` or `HARNESS_MODEL`.

`--runner api --provider anthropic` calls the Anthropic messages API. The key is `ANTHROPIC_API_KEY`. The base is `ANTHROPIC_BASE_URL` or `HARNESS_API_BASE`. The default base is `https://api.anthropic.com`.

To enforce `--max-cost`, return `usage.cost_usd`, or set both price variables. The variables are `HARNESS_USD_PER_MILLION_IN` and `HARNESS_USD_PER_MILLION_OUT`. If the cost is missing, the run stops.

## Tasks

`tasks.jsonl` is one JSON object per line. `tasks.json` is a list. Each task has `id`, `split` (`train` or `heldout`), `prompt` and `expect`. `files` maps a relative path to text. Those files are the task workspace.

`check` can replace `expect`.

- `{"type":"answer","expect":"51"}` matches the last `ANSWER:` line. With no marker, it matches the last line.
- `{"type":"contains","expect":"51"}` matches that substring in the final reply.
- `{"type":"command","argv":["python3","check.py"]}` runs that argv in the workspace. Exit 0 passes. The final reply is written to `answer.txt`. The command runs on your machine. Do not point it at tasks you do not trust.

## What optimize keeps

1. Score the current harness on the train split.
2. Ask the optimizer for a new harness file.
3. Reject a proposal that will not parse or that edits any other path.
4. Reject a proposal that does not change the files.
5. Reject a proposal that pastes a long train answer into the harness.
6. Score the rest on the train split.
7. Keep a proposal only when more train tasks pass.
8. Stop at the iteration cap, a budget cap, or a proposal with no change.
9. Score the best harness on the held-out split once.

A tie does not replace the current harness. The held-out score does not accept or reject an edit.

Step 5 is a substring check on train answers of 4 or more characters. `--no-answer-screen` turns it off. A shorter answer can still be pasted. A reworded answer can also pass the screen.

Held-out prompts are not sent to the optimizer. Train prompts, train answers and failure traces are. Read the held-out score before you trust an edit.

Each candidate is a directory under `versions/`, including rejected ones. `history.jsonl` stores the verdict, the score and the diff. `best/` is the kept harness. `report.json` is the summary.

## Budgets and dry-run

`--max-iterations` defaults to 3. `--max-calls` defaults to 40. `--max-turns` is the call cap per task and defaults to 4. `--timeout` defaults to 120 seconds per call.

`--max-cost` is a USD cap. The next call is refused once reported cost reaches the cap. One call can cross the cap. The cost is known only after the call returns.

`--dry-run` checks the harness and the tasks, then prints the plan. It calls no model and writes no files.

`--max-calls` must be at least 1. `--max-iterations 0` scores the baseline and the held-out split. It proposes nothing.

## Limits

The model weights stay as they are. Only the three harness files can change.

Claude and Codex are one-shot calls. Their tools are not this tool's `calc` or `read_file`.

There is no noise floor. A gain of one train task is enough to keep an edit.

The held-out score is one pass over the tasks you marked `heldout`. It is not a second benchmark suite.

`read_file` stays inside the task workspace. `calc` allows only numbers and `+ - * /`. A command check runs the argv you wrote, on your machine.

Do not commit an API key. Runners read keys from the environment only.
