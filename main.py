from videosdk.agents import Agent, AgentSession, Pipeline, JobContext, RoomOptions, WorkerJob,function_tool
from videosdk.plugins.google import GeminiRealtime, GeminiLiveConfig
import logging
from instructions import HINGLISH_FAREWELL, HINGLISH_INSTRUCTIONS, HINGLISH_GREETING
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", handlers=[logging.StreamHandler()])
from pathlib import Path
import logging

import asyncio
import traceback
import logging
import os
import sys
import csv
import uuid
from datetime import datetime
from pathlib import Path
from videosdk.agents import Agent, AgentSession, Pipeline, JobContext, RoomOptions, WorkerJob, Options, MCPServerHTTP
from videosdk.plugins.google import GeminiRealtime, GeminiLiveConfig
from dotenv import load_dotenv
from tools import AgentTools

load_dotenv()


LANGUAGES = {
    "hinglish": {
        "greeting":      HINGLISH_GREETING,
        "farewell":      HINGLISH_FAREWELL,
        "instructions":  HINGLISH_INSTRUCTIONS,
    }
}


DEFAULT_LANGUAGE = "hinglish"

AGENT_ID        = "ag_cxaoex"
GEMINI_MODEL       = "gemini-3.1-flash-live-preview"
GEMINI_VOICE    = "Puck"          # casual, youthful — fits Hinglish/delivery context
MAX_PROCESSES   = 10
REPORTS_DIR     = Path("feedback_reports")
REPORTS_DIR.mkdir(exist_ok=True)

logger = logging.getLogger(__name__)



def get_all_transcripts(history) -> str:
    conversation = ""

    for msg in history:
        role = msg.get("role", "").lower()
        content = msg.get("content", "")

        if isinstance(content, list):
            text_blocks = [
                c if isinstance(c, str) else "[Image/Other]"
                for c in content
            ]
            content = " ".join(text_blocks)

        if role == "user":
            conversation += f"User: {content}\n"
        elif role in ("assistant", "agent"):
            conversation += f"Agent: {content}\n"

    return conversation

class MyVoiceAgent(Agent, AgentTools):
    def __init__(self, language: str = DEFAULT_LANGUAGE):
        lang = LANGUAGES.get(language, LANGUAGES[DEFAULT_LANGUAGE])
        self.language = language
        self.lang_cfg = lang
        super().__init__(
            instructions=lang["instructions"],
        )

        self.set_thinking_audio(volume=0.9)  

    async def on_enter(self) -> None:
        await self.play_background_audio(
        override_thinking=True,
        looping=True
    )
        await self.session.say(self.lang_cfg["greeting"])
    
    async def on_exit(self) -> None:
        await self.stop_background_audio()
        await self.session.say(self.lang_cfg["farewell"])
        try:
            conversation = get_all_transcripts(self.session.get_context_history())
            logger.info("=" * 25 + " CONVERSATION ON_EXIT " + "=" * 25)
            logger.info(conversation)
            logger.info("=" * 50)

            # summary = await generate_summary(conversation)
            # logger.info("=" * 25 + " SUMMARY " + "=" * 25)
            # logger.info(summary)
            # logger.info("=" * 50)
        except Exception as e:
            logger.error(f"Error during on_exit: {e}")
            import traceback
            traceback.print_exc()
    
 
async def start_session(context: JobContext):
    language = DEFAULT_LANGUAGE
    try:
        meta = getattr(context, "metadata", {}) or {}
        language = meta.get("language", DEFAULT_LANGUAGE)
    except Exception:
        pass

    agent = MyVoiceAgent(language=language)
    model = GeminiRealtime(
        model=GEMINI_MODEL,
        api_key=os.getenv("GOOGLE_API_KEY"),
        config=GeminiLiveConfig(
            voice=GEMINI_VOICE,
            response_modalities=["AUDIO"]
        )
    )

    pipeline = Pipeline(llm=model)
    session = AgentSession(
        agent=agent,
        pipeline=pipeline
    )

    await session.start(wait_for_participant=True, run_until_shutdown=True)

def make_context() -> JobContext:
    room_options = RoomOptions(
        # room_id="<room_id>", # Replace it with your actual room_id
        name="Gemini Realtime Agent",
        playground=True,
        recording=True,
        background_audio=True,
    )


    return JobContext(room_options=room_options)

def validate_env() -> None:
    errors = []
    if not os.getenv("GOOGLE_API_KEY"):
        errors.append("GOOGLE_API_KEY is missing.")

    has_token = bool(os.getenv("VIDEOSDK_AUTH_TOKEN"))
    has_keys  = bool(os.getenv("VIDEOSDK_API_KEY") and os.getenv("VIDEOSDK_SECRET_KEY"))
    if not (has_token or has_keys):
        errors.append(
            "Either VIDEOSDK_AUTH_TOKEN or both VIDEOSDK_API_KEY + VIDEOSDK_SECRET_KEY must be set."
        )

    if errors:
        for err in errors:
            logger.critical(err)
        sys.exit(1)

    logger.info("Environment variables validated ✓")


if __name__ == "__main__":
    try:
        validate_env()

        logger.info(f"Starting Zomato Feedback Agent | id={AGENT_ID} | model={GEMINI_MODEL}")
        logger.info(f"Default language : {DEFAULT_LANGUAGE.upper()}")
        logger.info(f"Reports directory: {REPORTS_DIR.resolve()}")

        options = Options(
            agent_id=AGENT_ID,
            register=True,
            # max_processes=MAX_PROCESSES,
            # host="localhost",
            # port=57500,
        )

        job = WorkerJob(
            entrypoint=start_session,
            jobctx=make_context,
            options=options,
        )
        job.start()

    except KeyboardInterrupt:
        logger.info("Interrupted — shutting down...")
    except Exception:
        logger.critical("Fatal startup error:")
        traceback.print_exc()
        sys.exit(1)