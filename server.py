from mcp.server.fastmcp import FastMCP
import json
import pathlib

# Create the server and give it a name
mcp = FastMCP("todo")

# The to-do list will be saved in this file, next to server.py
FILE = pathlib.Path(__file__).parent / "todos.json"


def load():
    if FILE.exists():
        return json.loads(FILE.read_text())
    return []


@mcp.tool()
def add_todo(text: str) -> str:
    """Add a new to-do item."""
    todos = load()
    new_id = max([t["id"] for t in todos], default=0) + 1
    todos.append({"id": new_id, "text": text, "done": False})
    FILE.write_text(json.dumps(todos))
    return f"Added: {text}"


@mcp.tool()
def list_todos(only_open: bool = False) -> list:
    """List to-do items. By default it returns ALL items, both done and
    not done. Set only_open to true to get ONLY the items that are not
    done yet. Use only_open=true whenever the user asks what is left,
    what is still to do, or what is open."""
    todos = load()
    if only_open:
        todos = [t for t in todos if not t["done"]]
    return todos


@mcp.tool()
def complete_todo(id: int) -> str:
    """Mark a to-do item as done, using its id number. The result also
    lists the items that are still open, so there is no need to call
    list_todos afterwards."""
    todos = load()
    for item in todos:
        if item["id"] == id:
            item["done"] = True
            FILE.write_text(json.dumps(todos))
            still_open = [t["text"] for t in todos if not t["done"]]
            left = ", ".join(still_open) if still_open else "nothing"
            return f"Completed: {item['text']}. Still open now: {left}"
    return f"No to-do found with id {id}"

@mcp.tool()
def reopen_todo(id: int) -> str:
    """Mark a finished to-do item as NOT done again, using its id number.
    Use this when the user wants to undo a completion. Do NOT use
    add_todo for this."""
    todos = load()
    for item in todos:
        if item["id"] == id:
            item["done"] = False
            FILE.write_text(json.dumps(todos))
            return f"Reopened: {item['text']}"
    return f"No to-do found with id {id}"


@mcp.tool()
def delete_todo(id: int) -> str:
    """Permanently delete a to-do item, using its id number."""
    todos = load()
    for item in todos:
        if item["id"] == id:
            todos.remove(item)
            FILE.write_text(json.dumps(todos))
            return f"Deleted: {item['text']}"
    return f"No to-do found with id {id}"

if __name__ == "__main__":
    mcp.run()