import asyncio
import logging
import os
from videosdk.agents import function_tool
from videosdk.agents.warm_transfer import WarmTransferConfig, SIPDestination

logger = logging.getLogger(__name__)

class AgentTools:
    @function_tool
    async def end_call(self, message: str) -> dict:
        """Call ko tab end/disconnect karein jab customer phone rakhne ko bole, conversation khatam ho jaye, ya goodbye bole.
            message: Call end karne se pehle jo aakhri message bolna hai. Yeh bilkul natural aur situation ke hisaab se personalized hona chahiye. Generic message mat use karein. In scenarios ke hisaab se message dein:
            - Normal call close (sare sawal khatam, trial setup done) -> "Aapka bahut samay le liya — shukriya itni achhi baat karne ke liye. Take care, bye-bye!"
            - Galat number / wrong person -> "Oh, I am so sorry about that! Main apne records update kar deta hoon taaki aapko dobara pareshani na ho. Goodbye."
            - Customer abhi busy hai aur baad mein call karne ko bola -> "Bilkul samajh sakta hoon — kya main baad mein call kar sakta hoon aapko?"
            - Software mein interest nahi hai / relevant nahi hai -> "Koi baat nahi — aapka samay dene ke liye shukriya. Agar kabhi zaroorat pade toh hum hamesha available hain. Shukriya, bye-bye!"
        """
        logger.info(f"[AgentTools] end_call triggered. Message to say: '{message}'")
        asyncio.create_task(self._announce_and_hangup(message=message))
        return {"status": "ending_call"}

    @function_tool
    async def escalate_to_human(self, reason: str) -> str:
        """Call ko kisi human supervisor/manager ke paas warm transfer karne ke liye is tool ko call karein.
            reason: Short description ki call kyun transfer ki ja rahi hai.
        """
        logger.info(f"[AgentTools] escalate_to_human triggered. Reason: '{reason}'")
        config = WarmTransferConfig(
            destination=SIPDestination(
                routing_rule_id=os.getenv("SIP_ROUTING_RULE_ID", "rr_xxxxxxxx"),
                sip_call_to=os.getenv("SIP_CALL_TO", "+1XXXXXXXXXX"),
                sip_call_from=os.getenv("SIP_CALL_FROM", "+1XXXXXXXXXX"),
            ),
        )
        result = await self.session.warm_transfer(config)
        if result.success:
            logger.info("[AgentTools] Warm transfer successfully initiated.")
            return "Connected to a supervisor."
        logger.warning("[AgentTools] Warm transfer failed or could not reach supervisor.")
        return "I couldn't reach a supervisor right now. Let me keep helping you."
    
    async def _announce_and_hangup(self, message: str = "") -> None:
        if not self.session:
            logger.warning("[AgentTools] _announce_and_hangup called but self.session is None.")
            return
        logger.info("[AgentTools] Interrupting current session and preparing to hang up.")
        self.session.interrupt()
        await asyncio.sleep(0.5)
        handle = await self.session.say(message, interruptible=False)
        await handle
        await asyncio.sleep(0.5)
        logger.info("[AgentTools] Executing hangup...")
        await self.hangup()
        logger.info("[AgentTools] Hangup executed successfully.")
