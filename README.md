# To-Do & Notes Agent (MCP + Ollama)

A small, fully local AI agent that manages a to-do list and a notebook through
a chat window in the browser. It shows how **MCP servers**, **tool calling**,
and an **agent loop** work together, using only free tools. No paid
subscriptions or API keys.

## How it works

```
You type in the browser (app.py, Gradio)
        |
        v
  agent_core.py  -- before every message, plain code reads the
        |           current to-dos and notes (the "snapshot")
        v
  Ollama model (qwen2.5:14b)  <-- answers from the snapshot,
        |                          asks for tools only to CHANGE things
        v
  MCP servers (server.py, notes_server.py)
        |
        v
  todos.json / notes.json
```

- **Ollama** runs the language model locally.
- **MCP servers** expose the tools the model can use:
  - `server.py` (to-dos): `add_todo`, `list_todos`, `complete_todo`,
    `reopen_todo`, `delete_todo`
  - `notes_server.py` (notes): `save_note`, `list_notes`, `read_note`,
    `read_all_notes`, `delete_note`
- **agent_core.py** contains the `Agent` class. It keeps both servers
  connected, runs the tools the model asks for, and feeds the results back
  until the model gives a final answer.
- **app.py** is the Gradio chat window. Its greeting is built by plain code,
  not by the model.

### Design lesson: let code handle what must be exact

Small models sometimes answer from memory instead of calling a tool, drop
items from long lists, or drift into another language. Prompts alone did not
fix this. What worked:

1. Before every message, plain code reads the to-dos and notes and puts them
   into the system prompt as a "CURRENT DATA" section. The model reads
   fresh, correct data instead of relying on tool calls.
2. Tools are used only to change things (add, complete, reopen, delete, save).
3. Every action has its own clearly described tool, so the model does not
   improvise with the wrong one.## Requirements

- Windows (the launcher is a `.bat` file; the Python code also runs on
  Mac/Linux)
- Python 3.10 or higher
- [Ollama](https://ollama.com/download)
- Node.js (only for MCP Inspector, the optional testing tool)
- For `qwen2.5:14b`: about 12 GB of free RAM and 10 GB of disk space.
  The smaller `qwen2.5:7b` needs about 6 GB and 5 GB, but it is less reliable.

## Setup

1. **Install Ollama** and download the model:

   ```
   ollama pull qwen2.5:14b
   ```

2. **Open a terminal in the project folder** and create a virtual environment:

   ```
   python -m venv venv
   ```

3. **Activate it:**

   - Windows (Command Prompt): `venv\Scripts\activate`
   - Mac/Linux: `source venv/bin/activate`

4. **Install the dependencies:**

   ```
   pip install -r requirements.txt
   ```

   Note: the MCP library is pinned to version 1.x (`mcp<2`). Version 2.x
   renamed `FastMCP`, and this code was written for 1.x.

## Run the app

### Easy way (Windows)

Double-click **`start_agent.bat`**. It checks that Ollama is running (and
tries to start it), checks that the model is installed, activates the
virtual environment, and starts the app. The browser opens at
http://127.0.0.1:7860.

If you change the model in `agent_core.py` (`MODEL = ...`), change the
`set MODEL=...` line in `start_agent.bat` too.

### Manual way

Make sure Ollama is running, then, with the virtual environment active:

```
python app.py
```

Stop the app with Ctrl+C.

### Example things to say

- `What do I still need to do?`
- `Add a to-do: buy bread`
- `Mark buy bread as done`
- `Reopen "walk the dog"`
- `Delete the to-do "pay rent"`
- `Save a note titled Trip: Visit Prague in May`
- `What is in my Trip note?`
- `Remove the note about the door lock`
- `Tell me everything about my notes and to-dos`

Your data is stored in `todos.json` and `notes.json`, which are created
automatically in the project folder.

## Test the servers without AI

MCP Inspector lets you call tools by hand in a browser:

```
npx @modelcontextprotocol/inspector python server.py
npx @modelcontextprotocol/inspector python notes_server.py
```

Click **Connect**, open the **Tools** tab, and run the tools yourself.

## Project files

| File | Purpose |
|---|---|
| `start_agent.bat` | Double-click launcher with Ollama and model checks |
| `app.py` | Gradio chat window; builds the greeting with plain code |
| `agent_core.py` | `Agent` class: MCP connections, snapshot, agent loop |
| `server.py` | MCP server with the to-do tools |
| `notes_server.py` | MCP server with the notes tools |
| `test_core.py` | Test for the `Agent` class |
| `hello_ui.py` | Experiment: first Gradio window |
| `tool_test.py` | Experiment: the model requests a tool call |
| `agent_test.py` | Experiment: running the tool and returning the result |
| `agent.py` | Old console version (uses its own loop and qwen2.5:7b; no snapshot) |
| `requirements.txt` | Python dependencies |

## Troubleshooting

- **`ollama` is not recognized:** close and reopen the terminal after
  installing.
- **`No module named 'mcp.server.fastmcp'`:** you have mcp 2.x. Run
  `pip install "mcp[cli]<2"`.
- **Connection error to Ollama:** start the Ollama app, then try again.
- **The model is not installed:** run `ollama pull qwen2.5:14b`.
- **Answers look wrong:** the terminal prints `[snapshot]`, `[tool]` and
  `[result]` lines. They show what the code read and what the tools returned.
- **The model replies in another language:** the system prompt says to reply
  in English. If it still drifts, restart the app to clear the chat history.
- **Long lists lose an item:** the model sometimes drops an item when copying
  a long list. The data is still correct in the files and in the `[snapshot]`
  line.
- **Tool changes don't show up:** the MCP servers load when the app starts.
  Restart the app after editing `server.py` or `notes_server.py`.

## Ideas for extending

- A weather server using the free Open-Meteo API
- A file reader server limited to one folder
- An expense tracker backed by SQLite
- An overview built in plain code, so long lists are never shortened