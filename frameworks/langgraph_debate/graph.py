"""
LangGraph debate graph: Pro argues, then Con argues, then a Judge decides.

Flow:
    START ── pro ── con ── judge ── END

Each node has its own role and prompt. State is shared across nodes via the
`arguments` list, and the Judge synthesizes a verdict from both sides as the
assistant's final message.
"""

from functools import lru_cache
from operator import add
from typing import Annotated, TypedDict

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langgraph.graph import END, START, StateGraph


class DebateState(TypedDict):
    messages: Annotated[list[BaseMessage], add]
    arguments: Annotated[list[str], add]


@lru_cache(maxsize=1)
def _llm():
    from langchain_openai import ChatOpenAI

    return ChatOpenAI(model="gpt-5.4")


def _topic(state: DebateState) -> str:
    for msg in reversed(state["messages"]):
        if isinstance(msg, HumanMessage):
            return str(msg.content)
    return ""


def pro_advocate(state: DebateState) -> dict:
    prompt = (
        f"You are arguing PRO on the following topic. Make your case in flowing prose — "
        f"a few well-formed paragraphs that build a persuasive argument. Avoid bullet "
        f"lists.\n\nTopic: {_topic(state)}"
    )
    response = _llm().invoke(prompt)
    return {"arguments": [f"**PRO**\n\n{response.content}"]}


def con_advocate(state: DebateState) -> dict:
    prompt = (
        f"You are arguing CON on the following topic. Make your case in flowing prose — "
        f"a few well-formed paragraphs that build a persuasive argument. Avoid bullet "
        f"lists.\n\nTopic: {_topic(state)}"
    )
    response = _llm().invoke(prompt)
    return {"arguments": [f"**CON**\n\n{response.content}"]}


def judge(state: DebateState) -> dict:
    args = "\n\n".join(state["arguments"])
    prompt = (
        f"You are an impartial judge. Read both sides and write your verdict in one or two "
        f"clear paragraphs: declare a winner, explain your reasoning, and acknowledge the "
        f"strongest counterpoint. Write in flowing prose, not bullet lists.\n\n"
        f"Topic: {_topic(state)}\n\n{args}"
    )
    response = _llm().invoke(prompt)
    verdict = f"{args}\n\n---\n\n**VERDICT**\n\n{response.content}"
    return {"messages": [AIMessage(content=verdict)]}


def build_graph():
    graph = StateGraph(DebateState)
    graph.add_node("pro", pro_advocate)
    graph.add_node("con", con_advocate)
    graph.add_node("judge", judge)

    graph.add_edge(START, "pro")
    graph.add_edge("pro", "con")
    graph.add_edge("con", "judge")
    graph.add_edge("judge", END)

    return graph.compile()
