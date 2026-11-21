from mcp.server.fastmcp import FastMCP
import json
import pathlib

mcp = FastMCP("notes")

FILE = pathlib.Path(__file__).parent / "notes.json"


def load():
    if FILE.exists():
        return json.loads(FILE.read_text())
    return {}


@mcp.tool()
def save_note(title: str, content: str) -> str:
    """Save a note with a title and content. Use this for ideas, facts, or
    things to remember. Do NOT use this for tasks or to-dos."""
    notes = load()
    notes[title] = content
    FILE.write_text(json.dumps(notes))
    return f"Saved note: {title}"


@mcp.tool()
def list_notes() -> list:
    """List the titles of all saved notes. Returns titles only, NOT the
    content. To see what is inside one note, use read_note. To see ALL
    notes with their content, use read_all_notes."""
    return list(load().keys())


@mcp.tool()
def read_note(title: str) -> str:
    """Read the content of a saved note, using its exact title."""
    notes = load()
    for key, value in notes.items():
        if key.lower() == title.lower():
            return value
    return f"No note found with title '{title}'. Available titles: {', '.join(notes.keys())}"

@mcp.tool()
def read_all_notes() -> str:
    """Return ALL saved notes, with title and full content, in one call.
    Use this when the user asks for everything, all notes, or an
    overview of their notes."""
    notes = load()
    if not notes:
        return "There are no saved notes."
    return "\n\n".join(f"Title: {k}\nContent: {v}" for k, v in notes.items())

@mcp.tool()
def delete_note(title: str) -> str:
    """Permanently delete a saved note, using its exact title. Use this
    when the user wants to remove a note. Do NOT use save_note for this."""
    notes = load()
    for key in list(notes.keys()):
        if key.lower() == title.lower():
            del notes[key]
            FILE.write_text(json.dumps(notes))
            return f"Deleted note: {key}"
    return f"No note found with title '{title}'. Available titles: {', '.join(notes.keys())}"

if __name__ == "__main__":
    mcp.run()