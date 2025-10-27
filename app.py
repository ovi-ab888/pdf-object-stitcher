import streamlit as st
import fitz  # PyMuPDF
import io

st.set_page_config(page_title="PDF Object Stitcher (Vector Copy Version)", page_icon="📄", layout="wide")
st.title("📄 PDF Object Stitcher (Vector Copy Version)")
st.write("Upload multiple PDFs → copy selected vector region → arrange all on one A4 page (top-left layout)")

# -------------------------
# BOX CONFIGURATION (mm → pt)
# -------------------------
# 1 inch = 25.4 mm, 1 pt = 1/72 inch
# 36mm = 102.05pt, 82.5mm = 233.86pt
BOX_CONFIG = {
    "X": 68.035,       # starting X position on the source PDF
    "Y": 181.8821,     # starting Y position on the source PDF
    "W": 102.05,       # width (36mm)
    "H": 233.86        # height (82.5mm)
}

# -------------------------
# FUNCTION: Combine PDFs with vector copy
# -------------------------
def combine_pdfs(pdf_data_list):
    """Copy vector region (not raster) from each PDF and arrange all on one A4 page layout (top-left)."""
    A4_WIDTH, A4_HEIGHT = 595, 842  # A4 in pt
    combined = fitz.open()

    # Layout setup
    margin_left = 20
    margin_top = 20
    gap_x = 12
    gap_y = 18

    box_w = BOX_CONFIG["W"]
    box_h = BOX_CONFIG["H"]

    # Calculate how many columns fit in A4 width
    cols = int((A4_WIDTH - margin_left) // (box_w + gap_x))
    x_positions = [margin_left + i * (box_w + gap_x) for i in range(cols)]
    y_start = A4_HEIGHT - margin_top - box_h

    page = combined.new_page(width=A4_WIDTH, height=A4_HEIGHT)
    row, col = 0, 0

    for i, pdf_bytes in enumerate(pdf_data_list):
        src_doc = fitz.open("pdf", pdf_bytes)
        src_page = src_doc[0]

        # Define region to copy (from Illustrator coordinates)
        clip_rect = fitz.Rect(
            BOX_CONFIG["X"],
            BOX_CONFIG["Y"],
            BOX_CONFIG["X"] + BOX_CONFIG["W"],
            BOX_CONFIG["Y"] + BOX_CONFIG["H"]
        )

        # Destination placement on A4
        x = x_positions[col]
        y = y_start - row * (box_h + gap_y)
        dest_rect = fitz.Rect(x, y, x + box_w, y + box_h)

        # Create new page if current page filled
        if dest_rect.y0 < 0:
            page = combined.new_page(width=A4_WIDTH, height=A4_HEIGHT)
            row = 0
            col = 0
            x = x_positions[col]
            y = y_start - row * (box_h + gap_y)
            dest_rect = fitz.Rect(x, y, x + box_w, y + box_h)

        # --- Vector Copy (not raster) ---
        page.show_pdf_page(dest_rect, src_page.parent, 0, clip=clip_rect)

        col += 1
        if col >= cols:
            col = 0
            row += 1

    # Save final combined file
    output_bytes = io.BytesIO()
    combined.save(output_bytes)
    return output_bytes.getvalue()


# -------------------------
# STREAMLIT WORKFLOW
# -------------------------
uploaded_files = st.file_uploader("Upload multiple PDF files", type=["pdf"], accept_multiple_files=True)

if uploaded_files:
    st.info(f"{len(uploaded_files)} টা ফাইল পাওয়া গেছে ✔️")

    if st.button("🧩 Copy & Combine (Vector)"):
        combined_output = combine_pdfs([f.read() for f in uploaded_files])

        st.success("✅ সব ফাইল কপি করে একসাথে বসানো হয়েছে! নিচের বাটনে ক্লিক করে নতুন PDF ডাউনলোড করো।")
        st.download_button(
            label="📥 Download Final A4 PDF",
            data=combined_output,
            file_name="A4_Vector_Combined.pdf",
            mime="application/pdf"
        )
else:
    st.warning("⬆️ উপরের বাটন দিয়ে কিছু PDF ফাইল আপলোড করো।")
