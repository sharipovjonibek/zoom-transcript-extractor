def build_short_summary_prompt(transcript_text: str) -> str:
        return f"""
            You are summarizing a meeting transcript.

            Your goal is to produce a clear and concise overview of what was discussed during the meeting.

            Rules:
            - Use only the information present in the transcript.
            - Ignore filler words such as "um", "yeah", "you know", etc.
            - Do not invent information that is not mentioned.
            - Keep the summary concise and easy to read.
            - Return plain text only (no markdown symbols like #, ##, *,**).

            Structure the output like this:

            Meeting Overview
            Write 3–5 sentences summarizing the overall discussion and purpose of the meeting.

            Key Discussion Points
            List the most important topics discussed during the meeting.

            Important Updates or Decisions
            Mention any updates, progress reports, or decisions made.

            Tasks or Action Items (if mentioned)
            List any tasks or follow-ups that were discussed.
            If no tasks were mentioned, write: No specific tasks were discussed.

            Transcript:
            {transcript_text}
            """.strip()



def build_detailed_summary_prompt(transcript_text: str) -> str:
    return f"""
        You are summarizing a meeting transcript.

        Your goal is to produce a clear and concise overview of what was discussed during the meeting.

        Rules:
        - Use only the information present in the transcript.
        - Ignore filler words such as "um", "yeah", "you know", etc.
        - Do not invent information that is not mentioned.
        - Keep the summary concise and easy to read.
        - Return plain text only (no markdown symbols like #, ##, **).

        Structure the output like this:

        Meeting Overview
        Write 3–5 sentences summarizing the overall discussion and purpose of the meeting.

        Key Discussion Points
        List the most important topics discussed during the meeting.

        Important Updates or Decisions
        Mention any updates, progress reports, or decisions made.

        Tasks or Action Items (if mentioned)
        List any tasks or follow-ups that were discussed.
        If no tasks were mentioned, write: No specific tasks were discussed.

        Transcript:
        {transcript_text}
        """.strip()
