import time
import uuid
from typing import Any, Dict, Literal, Optional

from agno.agent import Agent
from agno.media import Video
from agno.tools.function import ToolResult
from agno.tools.lumalab import LumaLabTools
from agno.utils.log import log_info, logger

# Luma's API now requires an explicit `model`; the SDK has no default.
LUMA_MODEL: Literal["ray-2", "ray-flash-2"] = "ray-2"
LUMA_DURATION = "5s"


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------
class StudioLumaLabTools(LumaLabTools):
    """LumaLabTools variant that passes the now-required `model` parameter.

    `lumaai>=1.x` makes `model` a required keyword arg on
    `generations.create`. Upstream `LumaLabTools` never sends it, so the API
    rejects calls with a "missing required model configuration" error. These
    overrides mirror the upstream polling logic but add `model` (and an
    explicit `duration`).
    """

    def generate_video(
        self,
        agent: Agent,
        prompt: str,
        loop: bool = False,
        aspect_ratio: Literal["1:1", "16:9", "9:16", "4:3", "3:4", "21:9", "9:21"] = "16:9",
        keyframes: Optional[Dict[str, Dict[str, str]]] = None,
    ) -> ToolResult:
        """Use this function to generate a video given a prompt."""
        try:
            generation_params: Dict[str, Any] = {
                "model": LUMA_MODEL,
                "prompt": prompt,
                "loop": loop,
                "aspect_ratio": aspect_ratio,
                "duration": LUMA_DURATION,
            }
            if keyframes is not None:
                generation_params["keyframes"] = keyframes

            generation = self.client.generations.create(**generation_params)  # type: ignore

            video_id = str(uuid.uuid4())
            if not self.wait_for_completion:
                return ToolResult(content="Async generation unsupported")

            return self._poll_for_video(generation, video_id)
        except Exception as e:
            logger.exception("Failed to generate video")
            return ToolResult(content=f"Error: {e}")

    def image_to_video(
        self,
        agent: Agent,
        prompt: str,
        start_image_url: str,
        end_image_url: Optional[str] = None,
        loop: bool = False,
        aspect_ratio: Literal["1:1", "16:9", "9:16", "4:3", "3:4", "21:9", "9:21"] = "16:9",
    ) -> ToolResult:
        """Generate a video from one or two images with a prompt."""
        try:
            keyframes: Dict[str, Dict[str, str]] = {"frame0": {"type": "image", "url": start_image_url}}
            if end_image_url:
                keyframes["frame1"] = {"type": "image", "url": end_image_url}

            generation = self.client.generations.create(
                model=LUMA_MODEL,
                prompt=prompt,
                loop=loop,
                aspect_ratio=aspect_ratio,
                duration=LUMA_DURATION,
                keyframes=keyframes,  # type: ignore
            )

            video_id = str(uuid.uuid4())
            if not self.wait_for_completion:
                return ToolResult(content="Async generation unsupported")

            return self._poll_for_video(generation, video_id)
        except Exception as e:
            logger.exception("Failed to generate video")
            return ToolResult(content=f"Error: {e}")

    def _poll_for_video(self, generation: Any, video_id: str) -> ToolResult:
        """Poll the generation until it completes, fails, or times out."""
        seconds_waited = 0
        while seconds_waited < self.max_wait_time:
            if not generation or not generation.id:
                return ToolResult(content="Failed to get generation ID")

            generation = self.client.generations.get(generation.id)

            if generation.state == "completed" and generation.assets:
                video_url = generation.assets.video
                if video_url:
                    video_artifact = Video(id=video_id, url=video_url, state="completed")
                    return ToolResult(
                        content=f"Video generated successfully: {video_url}",
                        videos=[video_artifact],
                    )
            elif generation.state == "failed":
                return ToolResult(content=f"Generation failed: {generation.failure_reason}")

            log_info(f"Generation in progress... State: {generation.state}")
            time.sleep(self.poll_interval)
            seconds_waited += self.poll_interval

        return ToolResult(content=f"Video generation timed out after {self.max_wait_time} seconds")
