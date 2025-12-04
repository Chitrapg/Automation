import os
import base64
from pathlib import Path
import requests
import PyPDF2
from groq import Groq
from dotenv import load_dotenv
import certifi
from datetime import datetime
import uuid

load_dotenv()
os.environ.setdefault("SSL_CERT_FILE", certifi.where())
os.environ.setdefault("REQUESTS_CA_BUNDLE", certifi.where())

# ========== CONFIG ==========
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

CONFLUENCE_BASE_URL = os.getenv("CONFLUENCE_BASE_URL")  # e.g. "https://your-domain.atlassian.net/wiki"
CONFLUENCE_USERNAME = os.getenv("CONFLUENCE_USERNAME")  # your Atlassian email
CONFLUENCE_API_TOKEN = os.getenv("CONFLUENCE_API_TOKEN")  # your Atlassian API token
CONFLUENCE_SPACE_KEY = os.getenv("CONFLUENCE_SPACE_KEY")# Vision model from Groq docs (supports text+image)
GROQ_VISION_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"
PARENT_PAGE_ID = None


# ========== HELPERS ==========

def extract_pdf_text(pdf_path: str) -> str:
    """Extract all text from a PDF file."""
    reader = PyPDF2.PdfReader(pdf_path)
    text_chunks = []
    for page in reader.pages:
        text_chunks.append(page.extract_text() or "")
    return "\n".join(text_chunks)


def encode_image_to_base64(image_path: str) -> str:
    """Encode local image file as base64 string (for Groq image_url input)."""
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def generate_help_text_for_screen(client: Groq, frd_text: str, base64_image: str, screen_name: str) -> str:
    """
    Call Groq vision model with:
    - FRD text
    - Screenshot as image
    to generate help text for that screen.
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

    # Build user content: text + image in one message (Groq vision format) :contentReference[oaicite:2]{index=2}
    user_content = [
        {
            "type": "text",
            "text": (
                f"Screen name: {screen_name}\n\n"
                "Here is the functional requirement text (FRD) for this module:\n"
                "----- FRD START -----\n"
                f"{frd_text[:8000]}\n"  # safety: truncate if FRD is huge
                "----- FRD END -----\n\n"
                "Now analyze the attached screenshot image of this screen and generate the full help text "
                "for this screen in HTML suitable for Confluence."
            )
        },
        {
            "type": "image_url",
            "image_url": {
                # base64 inline data URL
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


def create_confluence_page(title: str, html_content: str) -> dict:
    """Create a Confluence page using the REST API."""
    if not all([CONFLUENCE_USERNAME, CONFLUENCE_API_TOKEN, CONFLUENCE_BASE_URL, CONFLUENCE_SPACE_KEY]):
        raise RuntimeError("Confluence config (email/token/base URL/space key) is missing.")

    url = f"{CONFLUENCE_BASE_URL}/rest/api/content"
    
    
    # Add unique timestamp to title so each run creates a new page
    unique_title = f"{title} – {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    

    

    payload = {
        "type": "page",
        "title": unique_title,
        "space": {"key": CONFLUENCE_SPACE_KEY},
        "body": {
            "storage": {
                "value": html_content,
                "representation": "storage"  # 'storage' == Confluence XHTML format
            }
        }
    }

    response = requests.post(
        url,
        json=payload,
        auth=(CONFLUENCE_USERNAME, CONFLUENCE_API_TOKEN),
        headers={"Content-Type": "application/json"},
        timeout=60,
    )
    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        print(f"Error: {e}")
        print(f"Response Body: {response.text}")
        raise
    data = response.json()

    page_id = data["id"]
    webui = data["_links"]["webui"]
    base = data["_links"]["base"]
    full_url = base + webui

    print("✅ Confluence page created successfully!")
    print("Page ID:", page_id)
    print("URL    :", full_url)

    return data


# ========== MAIN PIPELINE ==========

def main():
    # 1) Configure paths
    pdf_path = "Complete_OLMS_FRD.pdf"          # your FRD
    screenshots_folder = Path("screenshots")    # folder with PNG/JPG images

    # 2) Basic checks
    print("GROQ key loaded?", bool(GROQ_API_KEY))
    if GROQ_API_KEY:
        print("GROQ key starts with:", GROQ_API_KEY[:8], "length:", len(GROQ_API_KEY))
    if not GROQ_API_KEY:
        raise RuntimeError("GROQ_API_KEY not set in environment.")
    if not CONFLUENCE_BASE_URL:
        raise RuntimeError("Confluence env variables not set.")

    client = Groq(api_key=GROQ_API_KEY)

    print(f"📄 Reading PDF: {pdf_path}")
    frd_text = extract_pdf_text(pdf_path)

    # 3) Loop through all screenshots
    for image_path in screenshots_folder.glob("*.*"):
        if image_path.suffix.lower() not in {".png", ".jpg", ".jpeg"}:
            continue

        screen_name = image_path.stem  # e.g. "Customer_Profile" → "Customer_Profile"
        print(f"🖼️ Processing screenshot: {image_path.name} (screen: {screen_name})")

        base64_image = encode_image_to_base64(str(image_path))

        print("🤖 Generating help text using Groq Vision...")
        help_html = generate_help_text_for_screen(
            client=client,
            frd_text=frd_text,
            base64_image=base64_image,
            screen_name=screen_name,
        )

        # 4) Create Confluence page (one per screen)
        page_title = f"Help – {screen_name.replace('_', ' ')}"
        print(f"📨 Creating Confluence page: {page_title}")
        result = create_confluence_page(title=page_title, html_content=help_html)

        page_id = result.get("id")
        link = result.get("_links", {})
        webui = link.get("webui", "")
        full_url = f"{CONFLUENCE_BASE_URL}{webui}" if webui else "N/A"

        print("✅ Confluence page created successfully!")
        print(f"Page ID: {page_id}")
        print(f"URL    : {full_url}")
        print("-" * 60)


if __name__ == "__main__":
    main()
