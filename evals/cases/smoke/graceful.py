"""Graceful degradation tests — verify no crashes when optional API keys are missing."""

from evals.cases.smoke import SmokeTest

GRACEFUL_TESTS: list[SmokeTest] = [
    SmokeTest(
        id="g.1",
        name="studio — TTS without ElevenLabs",
        entity_type="agent",
        entity_id="studio",
        group="graceful",
        prompt="Read this aloud: hello",
        response_not_contains=["Traceback", "traceback"],
        requires=["!ELEVEN_LABS_API_KEY"],  # Run only when key is MISSING
    ),
    SmokeTest(
        id="g.2",
        name="studio — image-to-image without FAL",
        entity_type="agent",
        entity_id="studio",
        group="graceful",
        prompt="Transform this photo",
        response_not_contains=["Traceback", "traceback"],
        requires=["!FAL_KEY"],
    ),
    SmokeTest(
        id="g.3",
        name="reasoner — research without Exa",
        entity_type="agent",
        entity_id="reasoner",
        group="graceful",
        prompt="Research quantum computing",
        response_matches=[r"(?i)(quantum|comput)"],
        requires=["!EXA_API_KEY"],
    ),
]
