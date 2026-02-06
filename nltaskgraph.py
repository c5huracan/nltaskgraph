import json, re, subprocess
from pathlib import Path
from claudette import Chat

SYSTEM_PROMPT = """You convert natural language task descriptions into structured task graphs.
Output JSON with this schema:
{"tasks": [{"id": "task_name", "depends_on": [...], "run_on": "success|failure|always"}]}
Rules:
- "run_on" defaults to "success" (omit if success)
- Sequential words (then, after, finally) create dependencies
- Parallel words (while, in parallel, also) share the same dependency
- "if it fails" → run_on: failure
- "always" or "regardless" → run_on: always"""

TOOLS_PROMPT = """You have these tools:
- run_bash(cmd) - execute bash command, returns {stdout, stderr, code}
- read_file(path) - read file contents
- write_file(path, content) - write content to file
To use a tool, respond with ONLY a Python function call, no markdown."""

def extract_json(text):
    match = re.search(r'```(?:json)?\s*(.*?)\s*```', text, re.DOTALL)
    return match.group(1) if match else text

def run_bash(cmd):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return dict(stdout=r.stdout, stderr=r.stderr, code=r.returncode)

def read_file(path): return Path(path).read_text()
def write_file(path, content): Path(path).write_text(content)

def parse_task_graph(description, model="claude-sonnet-4-20250514"):
    chat = Chat(model=model, sp=SYSTEM_PROMPT)
    return json.loads(extract_json(chat(description).content[0].text))

def make_tool_task_fn(model="claude-sonnet-4-20250514", fail_tasks=None):
    fail_tasks, tools, context = fail_tasks or [], {'run_bash': run_bash, 'read_file': read_file, 'write_file': write_file}, {}
    def task_fn(task_id):
        if task_id in fail_tasks: return (print(f"[{task_id}]: FAILED"), "failure")[1]
        chat = Chat(model=model, sp=TOOLS_PROMPT)
        ctx_str = "\n".join(f"{k}: {v}" for k,v in context.items()) if context else "None"
        call = chat(f"Previous results:\n{ctx_str}\n\nExecute: {task_id}. Respond with ONLY the function call, no markdown.").content[0].text.strip()
        print(f"[{task_id}]: {call}")
        try: result = eval(call, tools)
        except Exception as e: return (print(f"  Error: {e}"), "failure")[1]
        context[task_id] = str(result)[:200]
        print(f"  Result: {str(result)[:100]}")
        return "success"
    return task_fn

def execute_task_graph(graph, task_fn=None):
    if task_fn is None: task_fn = lambda name: (print(f"Running: {name}"), "success")[1]
    status, tasks = {}, {t["id"]: t for t in graph["tasks"]}
    while len(status) < len(tasks):
        for task_id, task in tasks.items():
            if task_id in status: continue
            run_on, deps = task.get("run_on", "success"), task["depends_on"]
            deps_done = all(dep in status for dep in deps)
            conditions_met = all(run_on == "always" or run_on == status[dep] for dep in deps)
            if deps_done and conditions_met: status[task_id] = task_fn(task_id)
            elif deps_done and not conditions_met: status[task_id] = "skipped"
    return status

def go(task, model="claude-sonnet-4-20250514"):
    return execute_task_graph(parse_task_graph(task, model), make_tool_task_fn(model))