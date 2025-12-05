from groq import Groq
from typing import Optional
from config import GROQ_VISION_MODEL


def generate_help_text_for_screen(
    client: Groq,
    frd_text: str,
    base64_image: str,
    screen_name: str,
    max_frd_chars: int = 8000,
) -> str:
    """
    Call Groq vision model with:
    - Functional requirement text (FRD)
    - Screenshot as image (base64)
    to generate help text for that screen.

    :param client: Groq client instance.
    :param frd_text: Full FRD text extracted from PDF.
    :param base64_image: Base64-encoded screenshot.
    :param screen_name: Logical name of the screen (usually from filename).
    :param max_frd_chars: Limit for FRD text passed into the prompt.
    :return: HTML help text string.
    """
    system_instruction = (
        "You are an assistant that writes detailed, user-friendly help text for a banking web application. "
        "You will be given:\n"
        "1) Functional requirement text (FRD) of the module.\n"
        "2) A screenshot of a specific screen.\n\n"
        "You must:\n"
        "- Identify all visible fields, dropdowns, buttons, sections, and labels from the screenshot.\n"
        "- Use the FRD text to understand behavior, validations, and purpose.\n"
        "- Generate help text ONLY for this screen.\n"
        "- Use clear, concise language.\n"
        "- Output in HTML that can be pasted into Confluence.\n"
        "- Include sections like: Overview, Field Descriptions (in a table), Buttons/Actions, Validation & Error Messages, Tips.\n"
    )

    truncated_frd = frd_text[:max_frd_chars]

    user_content = [
        {
            "type": "text",
            "text": (
                f"Screen name: {screen_name}\n\n"
                "Here is the functional requirement text (FRD) for this module:\n"
                "----- FRD START -----\n"
                f"{truncated_frd}\n"
                "----- FRD END -----\n\n"
                "Now analyze the attached screenshot image of this screen and generate the full help text "
                "for this screen in HTML suitable for Confluence."
            ),
        },
        {
            "type": "image_url",
            "image_url": {
                "url": f"data:image/png;base64,{base64_image}",
            },
        },
    ]

    completion = client.chat.completions.create(
        model=GROQ_VISION_MODEL,
        messages=[
            {
                "role": "system",
                "content": system_instruction,
            },
            {
                "role": "user",
                "content": user_content,
            },
        ],
        max_completion_tokens=2048,
        temperature=0.3,
    )

    return completion.choices[0].message.content
