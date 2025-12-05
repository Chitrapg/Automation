import os
from pathlib import Path

from config import (
    GROQ_API_KEY,
    CONFLUENCE_BASE_URL,
    get_groq_client,
)
from pdf_utils import extract_pdf_text
from image_utils import encode_image_to_base64
from groq_vision import generate_help_text_for_screen
from confluence_client import create_confluence_page


def main() -> None:
    # 1) Configure paths
    pdf_path = "data/Complete_OLMS_FRD.pdf"          # your FRD file
    screenshots_folder = Path("data/screenshots")    # folder with PNG/JPG images

    # 2) Basic checks
    print("GROQ key loaded?", bool(GROQ_API_KEY))
    if GROQ_API_KEY:
        print("GROQ key starts with:", GROQ_API_KEY[:8], "length:", len(GROQ_API_KEY))

    if not GROQ_API_KEY:
        raise RuntimeError("GROQ_API_KEY not set in environment.")

    if not CONFLUENCE_BASE_URL:
        raise RuntimeError("CONFLUENCE_BASE_URL not set in environment.")

    if not Path(pdf_path).exists():
        raise FileNotFoundError(f"FRD PDF not found at path: {pdf_path}")

    if not screenshots_folder.exists():
        raise FileNotFoundError(f"'screenshots' folder not found at path: {screenshots_folder}")

    client = get_groq_client()

    print(f"📄 Reading PDF: {pdf_path}")
    frd_text = extract_pdf_text(pdf_path)

    # 3) Loop through all screenshots
    for image_path in sorted(screenshots_folder.glob("*.*")):
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
