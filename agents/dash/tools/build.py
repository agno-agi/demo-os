"""
Tool Assembly
=============

Factory functions that assemble tools per agent role.

Schema boundaries:
- Analyst: read-only SQL against public (company data) + can read dash schema.
- Engineer: full SQL scoped to dash schema. Creates views, summary tables,
  computed data. Records changes to knowledge.
"""

from agno.knowledge import Knowledge
from agno.tools.reasoning import ReasoningTools
from agno.tools.sql import SQLTools

from agents.dash.db_utils import DASH_SCHEMA, get_readonly_engine, get_sql_engine
from agents.dash.tools.introspect import create_introspect_schema_tool
from agents.dash.tools.save_query import create_save_validated_query_tool
from agents.dash.tools.update_knowledge import create_update_knowledge_tool
from db import db_url


def build_analyst_tools(knowledge: Knowledge) -> list:
    """Assemble tools for the Analyst agent.

    Read-only SQL enforced at the PostgreSQL level via
    ``default_transaction_read_only``. Any DML/DDL is rejected by the database.
    """
    ro_engine = get_readonly_engine()
    return [
        SQLTools(db_engine=ro_engine),
        create_introspect_schema_tool(db_url, engine=ro_engine),
        create_save_validated_query_tool(knowledge),
        ReasoningTools(),
    ]


def build_engineer_tools(knowledge: Knowledge) -> list:
    """Assemble tools for the Engineer agent.

    Full SQL scoped to the dash schema via search_path=dash,public.
    Can read company data in public, writes only to dash.
    """
    eng = get_sql_engine()
    return [
        SQLTools(db_engine=eng, schema=DASH_SCHEMA),
        create_introspect_schema_tool(db_url, engine=eng),
        create_update_knowledge_tool(knowledge),
        ReasoningTools(),
    ]
