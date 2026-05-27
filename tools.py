import asyncio
from videosdk.agents import function_tool

class AgentTools:
    @function_tool
    async def end_call(self, message: str) -> dict:
        """End the call when the user asks to hang up, end the conversation, or says goodbye.
            message: The message to say before ending the call. It should be warm, human, and personalised based on what the user said. The message should NOT be generic. Use the exact closing lines defined in the agent instructions for each scenario:
            - Normal call close (no more questions) -> "Goodbye! Have a nice day."
            - Wrong person / wrong number -> "Oh, I am so sorry about that! I'll update our records. Goodbye."
            - Customer is unable to pay -> "I understand things come up. I will note a request for an extension and pass this to our support team. Take care."
            - Dispute raised (wrong amount / wrong invoice) -> Say a brief acknowledgement that the dispute has been logged, then close warmly. For example: "I understand your concern. I've logged this for our specialist team and someone will contact you within 2-3 business days. Take care. Goodbye."
            - Customer claims already paid and payment is confirmed -> "I can see this invoice has been paid. I apologize for the trouble - our team will reconcile this and update your records. Goodbye."
            - Customer claims already paid but not found -> "Thank you for letting us know. I've logged this for our team to investigate and they will update you shortly. Take care. Goodbye."
            - Callback scheduled -> Confirm the scheduled time and close warmly. For example: "Perfect, I've noted the callback for [date] at [time]. We'll be in touch then. Have a great day. Goodbye."
            - Customer is busy / bad time -> "No problem at all. We'll reach out at a better time. Have a great day. Goodbye."
            - Customer promises to pay by a specific date -> Confirm the date warmly and close. For example: "That's great to hear! I've noted the payment for [date]. We appreciate your commitment. Have a great day. Goodbye."
            - Customer asked for invoice to be resent -> "Of course, I've arranged for the invoice to be sent to your email. Please review it and reach out if you have any questions. Have a great day. Goodbye."
            - Customer refuses to pay / no cooperation -> "I respect your position. I'll escalate this case for further review. A senior representative may contact you. Goodbye."
            - Customer says they need more time -> "I understand. I'll make a note and our team will follow up. Take care. Goodbye."
        """
        asyncio.create_task(self._announce_and_hangup(message=message))
        return {"status": "ending_call"}
    
    async def _announce_and_hangup(self, message: str = "") -> None:
        if not self.session:
            return
        self.session.interrupt()
        await asyncio.sleep(0.5)
        handle = await self.session.say(message, interruptible=False)
        await handle
        await asyncio.sleep(0.5)
        await self.hangup()
