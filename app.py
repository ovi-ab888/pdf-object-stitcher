import streamlit as st
import fitz  # PyMuPDF
import io

st.set_page_config(page_title="PDF Object Stitcher", page_icon="📄", layout="wide")
st.title("📄 PDF Object Stitcher (Illustrator Logic in Python)")
st.write("Upload multiple PDFs → extract defined box from each → combine all into an A4-sized PDF")

# -------------------------
# BOX CONFIGURATION
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
    """Extracts a rectangular box from first page of PDF and fits it into an A4 page."""
    doc = fitz.open("pdf", pdf_bytes)
    page = doc[0]
    page_height = page.rect.height
    page_width = page.rect.width

    # Illustrator → PDF coordinate conversion
    x1 = cfg["X"] + cfg["offsetX"]
    y1 = page_height - (cfg["Y"] + cfg["H"] - cfg["offsetY"])
    x2 = cfg["X"] + cfg["W"] + cfg["offsetX"]
    y2 = page_height - (cfg["Y"] - cfg["offsetY"])

    # Clamp values inside page boundary
    x1 = max(0, x1)
    y1 = max(0, y1)
    x2 = min(page_width, x2)
    y2 = min(page_height, y2)

    if x2 <= x1 or y2 <= y1:
        raise ValueError("Calculated crop area is invalid (out of bounds). Check coordinate values.")

    crop_rect = fitz.Rect(x1, y1, x2, y2)

    # Crop region from original page
    temp_pdf = fitz.open()
    temp_page = temp_pdf.new_page(width=crop_rect.width, height=crop_rect.height)
    temp_page.show_pdf_page(temp_page.rect, doc, 0, clip=crop_rect)

    # Now fit it inside A4
    A4_WIDTH, A4_HEIGHT = 595, 842  # points
    output_pdf = fitz.open()
    out_page = output_pdf.new_page(width=A4_WIDTH, height=A4_HEIGHT)

    # Scale to fit
    scale = min(A4_WIDTH / crop_rect.width, A4_HEIGHT / crop_rect.height, 1.0)
    new_w = crop_rect.width * scale
    new_h = crop_rect.height * scale

    # Center position
    pos_x = (A4_WIDTH - new_w) / 2
    pos_y = (A4_HEIGHT - new_h) / 2

    out_rect = fitz.Rect(pos_x, pos_y, pos_x + new_w, pos_y + new_h)
    out_page.show_pdf_page(out_rect, temp_pdf, 0)

    pdf_out = io.BytesIO()
    output_pdf.save(pdf_out)
    return pdf_out.getvalue()


def combine_pdfs(pdf_data_list):
    """Combine all cropped PDFs into one A4 page layout (top-left start, grid layout)."""
    A4_WIDTH, A4_HEIGHT = 595, 842  # A4 size in points
    combined = fitz.open()

    # --- layout setup ---
    cols = 5                # প্রতি row-এ কয়টা বসবে (তুমি চাইলে পরিবর্তন করতে পারো)
    margin_left = 20
    margin_top = 30
    gap_x = 15
    gap_y = 20

    # প্রতিটা tag এর আনুমানিক প্রস্থ
    cell_w = (A4_WIDTH - (margin_left + gap_x * (cols - 1))) / cols
    cell_h = cell_w * 2.4  # একটু লম্বা লেবেল হিসেবে ratio রাখা হলো

    x_positions = [margin_left + i * (cell_w + gap_x) for i in range(cols)]
    y_start = A4_HEIGHT - margin_top - cell_h

    page = combined.new_page(width=A4_WIDTH, height=A4_HEIGHT)
    row, col = 0, 0

    for i, pdf_bytes in enumerate(pdf_data_list):
        part = fitz.open("pdf", pdf_bytes)

        x = x_positions[col]
        y = y_start - row * (cell_h + gap_y)
        rect = fitz.Rect(x, y, x + cell_w, y + cell_h)

        # যদি পেজে জায়গা না থাকে → নতুন পেজ
        if y < 0:
            page = combined.new_page(width=A4_WIDTH, height=A4_HEIGHT)
            row = 0
            col = 0
            x = x_positions[col]
            y = y_start - row * (cell_h + gap_y)
            rect = fitz.Rect(x, y, x + cell_w, y + cell_h)

        page.show_pdf_page(rect, part, 0)

        col += 1
        if col >= cols:
            col = 0
            row += 1

    # Final save
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
        
        st.success("✅ সব ফাইল প্রসেস শেষ! নিচের বাটনে ক্লিক করে ডাউনলোড করো।")
        st.download_button(
            label="📥 Download A4 Combined PDF",
            data=final_pdf,
            file_name="A4_combined_output.pdf",
            mime="application/pdf"
        )
else:
    st.warning("⬆️ উপরের বাটন দিয়ে কিছু PDF ফাইল আপলোড করো।")
