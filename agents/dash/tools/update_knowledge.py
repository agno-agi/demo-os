"""Record schema changes and discoveries to the knowledge base."""

from agno.knowledge import Knowledge
from agno.knowledge.reader.text_reader import TextReader
from agno.tools import tool
from agno.utils.log import logger


def create_update_knowledge_tool(knowledge: Knowledge):
    """Create update_knowledge tool with knowledge injected."""

    @tool
    def update_knowledge(title: str, content: str) -> str:
        """Save metadata to the knowledge base so the Analyst can discover it.

        Call this after every schema change — new view, new table, altered
        column, dropped object. Also use it to record data discoveries
        (unexpected NULLs, type quirks, useful join patterns).

        Args:
            title: Short identifier (e.g., "Schema: dash.monthly_mrr",
                   "Discovery: annual billing discount").
            content: What was created/changed and how to use it.
                     Include column names, types, and example queries.
        """
        if not title or not title.strip():
            return "Error: Title required."
        if not content or not content.strip():
            return "Error: Content required."

        try:
            knowledge.insert(
                name=title.strip(),
                text_content=content.strip(),
                reader=TextReader(),
                skip_if_exists=False,
            )
            return f"Knowledge updated: {title}"
        except (AttributeError, TypeError, ValueError, OSError) as e:
            logger.error(f"Failed to update knowledge: {e}")
            return f"Error: {e}"

    return update_knowledge
