# nltaskgraph

Natural language to task graph to execution. A minimal agent harness.

## Install

    pip install claudette graphviz rich
    export ANTHROPIC_API_KEY=your_key

## Usage

    from nltaskgraph import go
    go("list files, count python files, write count to out.txt")

## How it works

1. Parse natural language into task graph with dependencies
2. Execute tasks in order using bash, read_file, write_file
3. Pass context between tasks
4. Handle success/failure branching

## TUI

    python tui.py

## FOOTGUNS

This runs arbitrary code. eval(), run_bash(), no sandbox, prompt injection risk, no undo.

**Do NOT run on production systems. You have been warned**

## License

MIT