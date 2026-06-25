from os import getenv

from agno.agent import Agent
from agno.tools.openai import OpenAITools

from agents.studio.instructions import INSTRUCTIONS
from app.settings import MODEL, agent_db

# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------
tools: list = [
    OpenAITools(
        image_model="gpt-image-1",
        image_size="1024x1024",
        enable_transcription=False,
        enable_speech_generation=False,
    )
]

if getenv("FAL_KEY"):
    from agno.tools.fal import FalTools

    tools.append(FalTools(model="fal-ai/flux/dev/image-to-image", api_key=getenv("FAL_KEY")))

if getenv("ELEVEN_LABS_API_KEY"):
    from agno.tools.eleven_labs import ElevenLabsTools

    tools.append(
        ElevenLabsTools(
            voice_id="21m00Tcm4TlvDq8ikWAM",
            model_id="eleven_multilingual_v2",
            enable_text_to_speech=True,
            enable_generate_sound_effect=True,
            enable_get_voices=True,
        )
    )

if getenv("LUMAAI_API_KEY"):
    from agents.studio.tools import StudioLumaLabTools

    tools.append(StudioLumaLabTools())

# ---------------------------------------------------------------------------
# Create Agent
# ---------------------------------------------------------------------------
studio = Agent(
    id="studio",
    name="Media Lab",
    description="Multimodal media agent that generates images, audio, and video.",
    model=MODEL,
    db=agent_db,
    tools=tools,
    instructions=INSTRUCTIONS,
    add_datetime_to_context=True,
    add_history_to_context=True,
    read_chat_history=True,
    num_history_runs=5,
    markdown=True,
)
