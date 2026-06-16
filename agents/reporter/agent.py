from agno.agent import Agent
from agno.tools.file_generation import FileGenerationTools

from agents.reporter.instructions import INSTRUCTIONS
from app.settings import MODEL, agent_db
from utils.exa import get_exa_mcp_tools

# ---------------------------------------------------------------------------
# Create Agent
# ---------------------------------------------------------------------------
reporter = Agent(
    id="researcher",
    name="Researcher",
    description="Researches across the web and generates polished, self-contained HTML reports.",
    model=MODEL,
    db=agent_db,
    tools=[
        FileGenerationTools(
            enable_json_generation=False,
            enable_csv_generation=False,
            enable_pdf_generation=False,
            enable_docx_generation=False,
            enable_txt_generation=False,
            enable_html_generation=True,
        ),
        *get_exa_mcp_tools("web_search_exa,company_research_exa,crawling_exa,web_fetch_exa"),
    ],
    instructions=INSTRUCTIONS,
    add_datetime_to_context=True,
    add_history_to_context=True,
    read_chat_history=True,
    num_history_runs=5,
    markdown=True,
)
