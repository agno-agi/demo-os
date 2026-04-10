"""Custom knowledge tool — lets the agent save metadata to pal_knowledge."""

from agno.knowledge import Knowledge
from agno.tools import tool


def create_update_knowledge(knowledge: Knowledge):
    """Create an update_knowledge tool bound to a specific knowledge base.

    The returned tool lets the agent save metadata (file manifests, schema
    index entries, source capabilities, discoveries) to the knowledge base.

    Args:
        knowledge: The Knowledge instance to insert into.

    Returns:
        A tool function that the agent can call.
    """

    @tool
    def update_knowledge(title: str, content: str) -> str:
        """Save metadata to the knowledge base.

        Use this to record structural information about Pal's context graph:
        - File manifests: what files exist and what they contain
        - Schema index: what SQL tables exist and their structure
        - Source capabilities: what tools are available
        - Discoveries: where information was found for specific topics
        - Wiki articles: what compiled articles exist
        - Raw sources: what ingested documents exist

        Args:
            title: A descriptive title prefixed with its category
                (e.g. "Schema: pal_projects", "File: brand-voice.md",
                "Discovery: Project X", "Source: Gmail",
                "Wiki: context-engineering", "Raw: rag-survey-2026").
            content: The metadata content describing the resource —
                columns, purpose, location, tags, etc.

        Returns:
            Confirmation message.
        """
        knowledge.insert(name=title, text_content=content)
        return f"Knowledge updated: {title}"

    return update_knowledge
