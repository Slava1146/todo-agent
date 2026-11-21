import asyncio
import json
import pathlib
import sys
import threading
from contextlib import AsyncExitStack

import ollama
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

MODEL = "qwen2.5:14b"
HERE = pathlib.Path(__file__).parent
SERVER_FILES = ["server.py", "notes_server.py"]

SYSTEM_PROMPT = (
    "You are a helpful assistant with two abilities: a to-do list for tasks, "
    "and a notebook for ideas, facts, and things to remember. "
    "Always reply in English, no matter what. "
    "At the end of these instructions is a section called CURRENT DATA. "
    "It is read fresh from the files before every user message, so it is "
    "always correct and up to date. Use it to answer every question about "
    "tasks and notes. Always include every item, never leave any out. "
    "If the user asks for everything, show open tasks, done tasks, and all "
    "notes with their content. "
    "Tools are used only to change things. Pick the right one: "
    "add_todo creates a brand new task. "
    "complete_todo marks a task as done. "
    "reopen_todo marks a done task as not done again (never use add_todo "
    "for this). "
    "delete_todo removes a task. "
    "save_note creates or updates a note (never use it to delete). "
    "delete_note removes a note. "
    "For tools that need an id, take it from CURRENT DATA. If two tasks "
    "have the same text, ask the user which one they mean. "
    "Call each tool at most once per request. If no tool can do what the "
    "user asks, say so instead of trying a different tool. "
    "After complete_todo, use the 'Still open now' part of its result to "
    "tell the user what is left. "
    "If the user asks for a note title that is not in CURRENT DATA, say it "
    "does not exist and show the available titles. Never show a different "
    "note instead. If the wording is clearly close to an existing title, "
    "such as 'idea' for 'Ideas', use that existing title. "
)

class Agent:
    def __init__(self):
        # A background thread that runs an event loop forever
        self.loop = asyncio.new_event_loop()
        threading.Thread(target=self.loop.run_forever, daemon=True).start()

        self.tool_to_session = {}
        self.tools = []
        self.messages = [{"role": "system", "content": SYSTEM_PROMPT}]

        # Connect to the servers (this waits until they are ready)
        self._run(self._connect())

    def _run(self, coroutine):
        """Run an async function in the background thread and wait for it."""
        return asyncio.run_coroutine_threadsafe(coroutine, self.loop).result()

    async def _connect(self):
        self.stack = AsyncExitStack()
        for script in SERVER_FILES:
            params = StdioServerParameters(
                command=sys.executable, args=[str(HERE / script)]
            )
            read, write = await self.stack.enter_async_context(stdio_client(params))
            session = await self.stack.enter_async_context(ClientSession(read, write))
            await session.initialize()

            result = await session.list_tools()
            for t in result.tools:
                self.tool_to_session[t.name] = session
                self.tools.append(
                    {
                        "type": "function",
                        "function": {
                            "name": t.name,
                            "description": t.description,
                            "parameters": t.inputSchema,
                        },
                    }
                )
            print(f"Connected to {script}:", [t.name for t in result.tools])

    async def _snapshot(self):
        """Read the current to-dos and notes with plain code, no model."""
        r = await self.tool_to_session["list_todos"].call_tool("list_todos", {})
        todos = [json.loads(c.text) for c in r.content if hasattr(c, "text")]
        r = await self.tool_to_session["read_all_notes"].call_tool("read_all_notes", {})
        notes = "\n".join(c.text for c in r.content if hasattr(c, "text"))

        open_lines = [f"- {t['text']} (id {t['id']})" for t in todos if not t["done"]]
        done_lines = [f"- {t['text']} (id {t['id']})" for t in todos if t["done"]]
        print(f"  [snapshot] {len(open_lines)} open, {len(done_lines)} done")

        return (
            "\n\nCURRENT DATA (read just now)\n"
            "Open tasks:\n" + ("\n".join(open_lines) or "- none") + "\n"
            "Done tasks:\n" + ("\n".join(done_lines) or "- none") + "\n"
            "Notes:\n" + (notes or "There are no saved notes.") + "\n"
        )

    def chat(self, user_text):
        """Send one message to the agent and get the final answer back."""
        return self._run(self._chat(user_text))

    def get_todos(self):
        """Read the to-do list directly, with no model involved."""
        return self._run(self._get_todos())

    async def _get_todos(self):
        session = self.tool_to_session["list_todos"]
        result = await session.call_tool("list_todos", {})
        return [json.loads(c.text) for c in result.content if hasattr(c, "text")]

    async def _chat(self, user_text):
        fresh = SYSTEM_PROMPT + await self._snapshot()
        self.messages[0] = {"role": "system", "content": fresh}
        self.messages.append({"role": "user", "content": user_text})
        while True:
            # ollama.chat blocks, so we run it in a helper thread
            response = await asyncio.to_thread(
                ollama.chat,
                model=MODEL,
                messages=self.messages,
                tools=self.tools,
                options={"temperature": 0, "num_ctx": 8192},
            )
            self.messages.append(response.message)

            if not response.message.tool_calls:
                return response.message.content

            for call in response.message.tool_calls:
                name = call.function.name
                args = dict(call.function.arguments)
                print(f"  [tool] {name} {args}")

                session = self.tool_to_session.get(name)
                if session is None:
                    text = f"Unknown tool: {name}"
                else:
                    result = await session.call_tool(name, args)
                    text = "\n".join(
                        c.text for c in result.content if hasattr(c, "text")
                    )
                print("    [result]", text)
                self.messages.append(
                    {"role": "tool", "tool_name": name, "content": text or "(empty)"}
                )