from videosdk.agents import Agent, AgentSession, Pipeline, JobContext, RoomOptions, WorkerJob
from videosdk.plugins.google import GeminiRealtime, GeminiLiveConfig
import logging
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

load_dotenv()



DEFAULT_LANGUAGE = "hinglish"

AGENT_ID        = "ag_cxaoex"
GEMINI_MODEL       = "gemini-3.1-flash-live-preview"
GEMINI_VOICE    = "Orus"          # casual, youthful — fits Hinglish/delivery context
MAX_PROCESSES   = 10
REPORTS_DIR     = Path("feedback_reports")
REPORTS_DIR.mkdir(exist_ok=True)

logger = logging.getLogger(__name__)

class MyVoiceAgent(Agent):
    def __init__(self):
        super().__init__(
            instructions="You Are VideoSDK's Voice Agent.You are a helpful voice assistant that can answer questions and help with tasks.",
        )

    async def on_enter(self) -> None:
        await self.session.say("Hello, how can I help you today?")
    
    async def on_exit(self) -> None:
        await self.session.say("Goodbye!")

async def start_session(context: JobContext):
    
    agent = MyVoiceAgent()
    model = GeminiRealtime(
        model="gemini-3.1-flash-live-preview",
        # When GOOGLE_API_KEY is set in .env - DON'T pass api_key parameter
        # api_key="AIXXXXXXXXXXXXXXXXXXXX", 
        config=GeminiLiveConfig(
            voice="Leda", # Puck, Charon, Kore, Fenrir, Aoede, Leda, Orus, and Zephyr.
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