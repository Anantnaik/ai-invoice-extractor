import streamlit as st
import pandas as pd
import io
from datetime import datetime

from extract_text import extract_text_from_pdf, clean_invoice_text
from extract_invoice import extract_invoice_fields

# IMPORTANT: Disable Sheets in public demo
DEMO_MODE = True

if not DEMO_MODE:
    from export_sheets import export_to_sheets


# -------------------------------
# Page Config
# -------------------------------
st.set_page_config(
    page_title="AI Invoice Extractor",
    layout="wide"
)


# -------------------------------
# Session State Init
# -------------------------------
if "results_df" not in st.session_state:
    st.session_state.results_df = None


# -------------------------------
# Constants
# -------------------------------
FINAL_COLUMNS = [
    "vendor_name",
    "invoice_number",
    "invoice_date",
    "total_amount",
    "currency",
    "tax_amount",
    "line_items",
    "status"
]


# -------------------------------
# Helper Functions
# -------------------------------

def validate_invoice(data):
    status = "OK"

    if not data.get("total_amount"):
        status = "Needs Review"

    if not data.get("invoice_date"):
        status = "Needs Review"

    return status


def normalize_date(date_str):
    try:
        return str(pd.to_datetime(date_str).date())
    except:
        return None


def normalize_amount(val):
    try:
        return float(str(val).replace(",", "").strip())
    except:
        return None


# -------------------------------
# UI
# -------------------------------

st.title("AI Invoice Extraction Assistant")

with st.expander("📘 How to Use This Tool"):

    st.markdown("""
    **Step 1:** Upload 1–5 PDF invoices  
    **Step 2:** Click *Process Invoices*  
    **Step 3:** Review extracted data  
    **Step 4:** Download CSV  

    ⚠️ Invoices marked *Needs Review* should be checked manually.
    """)


st.write("Upload PDF invoices and extract structured data automatically.")


uploaded_files = st.file_uploader(
    "Upload Invoice PDFs",
    type=["pdf"],
    accept_multiple_files=True
)


process_btn = st.button("Process Invoices")

st.divider()


# -------------------------------
# Processing
# -------------------------------

if process_btn and uploaded_files:

    results = []

    with st.spinner("Processing invoices..."):

        for file in uploaded_files:

            file_bytes = file.read()

            # Extract raw text
            raw_text, source = extract_text_from_pdf(file_bytes)

            # Clean text
            clean_text = clean_invoice_text(raw_text)

            # LLM extraction
            data, llm_status = extract_invoice_fields(clean_text)

            if data:

                # Normalize values
                data["invoice_date"] = normalize_date(
                    data.get("invoice_date")
                )

                data["total_amount"] = normalize_amount(
                    data.get("total_amount")
                )

                data["tax_amount"] = normalize_amount(
                    data.get("tax_amount")
                )

                # Validate
                status = validate_invoice(data)
                data["status"] = status

                results.append(data)

            else:

                # Fallback if LLM fails
                results.append({
                    "vendor_name": None,
                    "invoice_number": None,
                    "invoice_date": None,
                    "total_amount": None,
                    "currency": None,
                    "tax_amount": None,
                    "line_items": None,
                    "status": "Needs Review"
                })

    # Save results to session
    df = pd.DataFrame(results)
    st.session_state.results_df = df


# -------------------------------
# Results Display
# -------------------------------

if st.session_state.results_df is not None:

    df = st.session_state.results_df.copy()

    # Ensure all columns exist
    for col in FINAL_COLUMNS:
        if col not in df.columns:
            df[col] = None

    # Reorder columns
    df = df[FINAL_COLUMNS]

    st.subheader("Extracted Results")

    st.dataframe(df, use_container_width=True)


    # -------------------------------
    # CSV Export
    # -------------------------------

    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False)

    filename = f"invoices_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

    st.download_button(
        label="Download CSV",
        data=csv_buffer.getvalue(),
        file_name=filename,
        mime="text/csv"
    )

    st.divider()


    # -------------------------------
    # Google Sheets (Disabled in Demo)
    # -------------------------------

    if DEMO_MODE:

        st.info("📊 Google Sheets export available in client version.")

    else:

        if st.button("Export to Google Sheets"):

            with st.spinner("Uploading to Google Sheets..."):

                try:
                    sheet_url = export_to_sheets(
                        df,
                        sheet_name="Invoice Extraction " +
                        datetime.now().strftime("%Y-%m-%d %H:%M")
                    )

                    st.success("Export successful!")
                    st.markdown(f"[Open Spreadsheet]({sheet_url})")

                except Exception as e:

                    st.error("Export failed. Please try again.")
                    st.caption(str(e))


else:

    st.info("Upload invoices and click 'Process Invoices' to begin.")



# -------------------------------
# Footer
# -------------------------------

st.divider()

st.caption("AI Invoice Extraction Assistant • Built with Streamlit & LLMs")

