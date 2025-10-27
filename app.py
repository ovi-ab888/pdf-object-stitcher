import streamlit as st
import fitz  # PyMuPDF
import io

# -------------------------
# STREAMLIT UI
# -------------------------
st.set_page_config(page_title="PDF Object Stitcher", page_icon="📄", layout="wide")
st.title("📄 PDF Object Stitcher (Illustrator Logic in Python)")
st.write("Upload multiple PDFs → extract defined box from each → combine all into a new PDF")

# -------------------------
# BOX CONFIGURATION (same as Illustrator script)
# -------------------------
BOX_CONFIG = {
    "offsetX": -51,
    "offsetY": +123,
    "X": 68.035,
    "Y": 181.8821,
    "W": 102.05,
    "H": 233.86
}

# -------------------------
# FUNCTIONS
# -------------------------
def extract_box_from_pdf(pdf_bytes, cfg):
    """Extracts a rectangular box from first page of PDF."""
    doc = fitz.open("pdf", pdf_bytes)
    page = doc[0]

    # Calculate area (Illustrator coordinate → PDF coordinate)
    rect = fitz.Rect(
        cfg["X"] + cfg["offsetX"],
        page.rect.height - (cfg["Y"] - cfg["offsetY"]),
        cfg["X"] + cfg["W"] + cfg["offsetX"],
        page.rect.height - (cfg["Y"] + cfg["H"] - cfg["offsetY"])
    )

    # Crop region to new PDF
    new_pdf = fitz.open()
    new_page = new_pdf.new_page(width=rect.width, height=rect.height)
    new_page.show_pdf_page(new_page.rect, doc, 0, clip=rect)

    pdf_out = io.BytesIO()
    new_pdf.save(pdf_out)
    return pdf_out.getvalue()


def combine_pdfs(pdf_data_list):
    """Combine all cropped PDFs into one"""
    combined = fitz.open()
    for pdf_bytes in pdf_data_list:
        part = fitz.open("pdf", pdf_bytes)
        combined.insert_pdf(part)
    output_bytes = io.BytesIO()
    combined.save(output_bytes)
    return output_bytes.getvalue()


# -------------------------
# STREAMLIT WORKFLOW
# -------------------------
uploaded_files = st.file_uploader("Upload multiple PDF files", type=["pdf"], accept_multiple_files=True)

if uploaded_files:
    st.info(f"{len(uploaded_files)} টা ফাইল পাওয়া গেছে।")
    
    if st.button("🧩 Extract & Combine"):
        cropped_list = []
        progress = st.progress(0)
        
        for i, file in enumerate(uploaded_files):
            st.write(f"Processing: {file.name}")
            cropped_pdf = extract_box_from_pdf(file.read(), BOX_CONFIG)
            cropped_list.append(cropped_pdf)
            progress.progress((i + 1) / len(uploaded_files))
        
        final_pdf = combine_pdfs(cropped_list)
        
        st.success("✅ সব ফাইল প্রসেস করা শেষ! নিচের বাটন দিয়ে ডাউনলোড করো।")
        st.download_button(
            label="📥 Download Combined PDF",
            data=final_pdf,
            file_name="stitched_output.pdf",
            mime="application/pdf"
        )
else:
    st.warning("⬆️ উপরের বাটন দিয়ে কিছু PDF ফাইল আপলোড করো।")
