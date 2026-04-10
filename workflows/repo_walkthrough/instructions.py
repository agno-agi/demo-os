"""Instruction prompts for the Repo Walkthrough workflow agents."""

ANALYST_INSTRUCTIONS = """\
Analyze the repository structure. Read key files: README, main entry point,
config, and 2-3 core modules.

Produce a structured summary:
- What the project does (1 sentence)
- Architecture (how it's organized)
- Key components (3-5 most important files/modules)
- How it works (the main flow)

Keep it factual. Cite file paths.\
"""

SCRIPT_WRITER_INSTRUCTIONS = """\
Write a 1-2 minute narration script based on the code analysis.

Structure:
- Opening hook (what this does)
- Architecture walkthrough
- How the pieces connect
- Closing takeaway

Write for spoken delivery -- conversational, clear, no jargon without
explanation. Target 200-300 words.\
"""

NARRATOR_INSTRUCTIONS = """\
Narrate the walkthrough script as spoken audio using text-to-speech.
Read it naturally with good pacing.

If TTS is not available, return the script as text with a note that audio
generation requires ELEVENLABS_API_KEY.\
"""
