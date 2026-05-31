# Tuidoist

A terminal power tool for Todoist. Not a TUI remake — a productivity multiplier.

Tuidoist extends Todoist with workflows its own UI can't do: bulk-add 20 tasks in one shot,
paste a recipe and let AI extract the steps, filter by task age or staleness, move entire
sets of tasks with a single command, and pipe tasks into scripts.

## Features

- **Smart parsing** — paste unstructured text (lists, recipes, messages) and let AI extract tasks with inferred properties
- **Bulk operations** — add, move, or reschedule many tasks at once with shared properties
- **Custom filters** — filter by task age, staleness, overdue duration, missing due dates, orphaned inbox items
- **Task templates** — save reusable task definitions with subtasks and default properties
- **Time tracking** — log time on tasks and visualize productivity with a GitHub-style heatmap
- **Pipe support** — compose with other CLI tools: `echo "Buy milk" | tuidoist add`, `tuidoist list --json | jq`
- **Vim keybindings** — j/k navigation, keyboard-driven everything

## Install

Requires Python 3.12+.

With [uv](https://docs.astral.sh/uv/) (recommended):
```
uv tool install tuidoist
```

Or with pipx:
```
pipx install tuidoist
```

Then launch:
```
tuidoist
```

On first run, you'll be prompted for your Todoist API token.
Find it at: **Todoist Settings → Integrations → Developer**

## Keybindings

| Key   | Action           |
|-------|------------------|
| j / k | Navigate down/up |
| Enter | Select           |
| Esc   | Back / Quit      |
| h / l | Cycle tabs       |
| q     | Quit             |

## Development

Clone and install in editable mode:
```
git clone https://github.com/tjlotz/tuidoist.git
cd tuidoist
uv venv
uv pip install -e .
uv run tuidoist
```

See [RELEASING.md](RELEASING.md) for the release process.
