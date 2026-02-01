from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
import json
import re

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

prompt_template = PromptTemplate(
    input_variables=["invoice_text"],
    template="""
Extract invoice data and return ONLY valid JSON with these keys:

{{
  "vendor_name": "",
  "invoice_number": "",
  "invoice_date": "",
  "total_amount": "",
  "currency": "",
  "tax_amount": "",
  "line_items": ""
}}

Rules:
- If value not found, use null.
- Do not add commentary.
- Output must be pure JSON.

Invoice text:
{invoice_text}
"""
)

def extract_invoice_fields(clean_text):
    prompt = prompt_template.format(invoice_text=clean_text[:6000])

    response = llm.invoke(prompt).content

    # Try to isolate JSON if LLM adds junk
    match = re.search(r'\{.*\}', response, re.DOTALL)

    if not match:
        return None, "no_json_found"

    try:
        data = json.loads(match.group())
        return data, "ok"
    except Exception:
        return None, "json_parse_error"
