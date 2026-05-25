"""Smoke tests for AgentAsJudge post-hooks (Docs, Dash).

Each test runs the entity, then asserts the post-hook judge logged a row to
agno_eval_runs with the expected pass/fail verdict, retrieved via /eval-runs.
"""

from evals.cases.smoke import SmokeTest

POST_HOOK_TESTS: list[SmokeTest] = [
    SmokeTest(
        id="ph.1",
        name="docs post-hook — judge passes a simple Agno question",
        entity_type="agent",
        entity_id="docs",
        group="post_hooks",
        prompt="What is an Agno Agent in one sentence?",
        response_contains=["Agno"],
        response_not_contains=["Traceback"],
        expect_eval_judge="Docs Quality Judge",
        expect_eval_passed=True,
        max_duration=60.0,
    ),
    SmokeTest(
        id="ph.2",
        name="dash post-hook — judge passes a simple data question",
        entity_type="team",
        entity_id="dash",
        group="post_hooks",
        prompt="How many customers are in the customers table?",
        response_not_contains=["Traceback"],
        expect_eval_judge="Dash Quality Judge",
        expect_eval_passed=True,
        max_duration=120.0,
    ),
]
