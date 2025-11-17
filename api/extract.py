#pylint: disable=C0304
import os
import json
import fitz  # PyMuPDF
from google import genai
from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import JSONResponse
from prompts import ResumeExtractionPrompt

GEMINI_MODEL_ID = os.environ.get("GEMINI_MODEL_ID", "gemini-2.5-flash")

router = APIRouter()
client = genai.Client()

def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """
    Extract text from a PDF, including complex and multi-column layouts,
    using block-based extraction and coordinate sorting.
    """
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid PDF file: {e}")

    all_text = []

    for page in doc:
        # Extract blocks, each block: (x0, y0, x1, y1, text, block_type, block_no)
        blocks = page.get_text("blocks")

        if not blocks:
            continue

        # Sort blocks by vertical position then horizontal position
        blocks = sorted(blocks, key=lambda b: (round(b[1], 1), round(b[0], 1)))

        page_text_parts = []
        for block in blocks:
            text = block[4]
            if text and text.strip():
                page_text_parts.append(text.strip())

        page_text = "\n".join(page_text_parts)
        all_text.append(page_text)

    doc.close()

    # Join pages with spacing
    return "\n\n".join(all_text)


@router.post("/api/extract")
async def extract_pdf_text(file: UploadFile = File(...)):
    """
    Endpoint to extract text from uploaded PDF file.
    Handles complex PDFs including multi-column layouts.
    """
    # Validate PDF
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    pdf_bytes = await file.read()
    if not pdf_bytes:
        raise HTTPException(status_code=400, detail="Empty file uploaded.")

    # Extract text using improved logic
    extracted_text = extract_text_from_pdf(pdf_bytes)
    prompt_text = ResumeExtractionPrompt.prompt(raw_text=extracted_text)
    print("Prompt Text:", prompt_text)  # Debug print
    response = client.models.generate_content(
        model=GEMINI_MODEL_ID,
        contents=prompt_text
    )
    response_message = response.text
    print("Response Message:", response_message)  # Debug print

    # Extract from first { to last }
    start_index = response_message.find('{')
    end_index = response_message.rfind('}') + 1
    if start_index == -1 or end_index == -1:
        raise HTTPException(status_code=500, detail="Failed to parse response from language model.")

    json_str = response_message[start_index:end_index]
    parsed_json = json.loads(json_str)

    return parsed_json