import gradio as gr

from agent_core import Agent

print("Starting agent...")
agent = Agent()

# Build the greeting in plain code, so it can't contain model mistakes
items = agent.get_todos()
open_items = [i["text"] for i in items if not i["done"]]

if open_items:
    lines = "\n".join(f"- {t}" for t in open_items)
    greeting = (
        f"Hi! You have {len(open_items)} unfinished tasks:\n\n{lines}\n\n"
        "I can manage your to-dos, or save and read your notes."
    )
else:
    greeting = (
        "Hi! You have no unfinished tasks. "
        "I can manage your to-dos, or save and read your notes."
    )

initial_messages = [{"role": "assistant", "content": greeting}]


def reply(message, history):
    return agent.chat(message)


# Different Gradio versions need slightly different settings,
# so we try one and fall back to the other.
try:
    chatbot = gr.Chatbot(value=initial_messages, type="messages", height=500)
    demo = gr.ChatInterface(
        fn=reply, type="messages", chatbot=chatbot, title="To-Do & Notes Agent"
    )
except TypeError:
    chatbot = gr.Chatbot(value=initial_messages, height=500)
    demo = gr.ChatInterface(
        fn=reply, chatbot=chatbot, title="To-Do & Notes Agent"
    )

demo.launch(inbrowser=True)