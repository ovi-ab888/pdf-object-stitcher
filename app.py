import streamlit as st
import fitz  # PyMuPDF
import io

st.title("📄 PDF Object Extractor & Combiner")
st.write("একাধিক PDF আপলোড করো ➜ প্রতিটি থেকে নির্দিষ্ট অংশ কেটে ➜ একত্রে নতুন PDF তৈরি করো")

# --- Box Coordinates (তুমি নিজের মতো পরিবর্তন করতে পারো)
box = {"X": 68.035, "Y": 181.8821, "W": 102.05, "H": 233.86}

# --- File Uploader
uploaded_files = st.file_uploader(
    "Upload multiple PDF files",
    type=["pdf"],
    accept_multiple_files=True
)

# --- Function: নির্দিষ্ট অংশ কেটে আনা
def extract_box(pdf_bytes, box):
    doc = fitz.open("pdf", pdf_bytes)
    page = doc[0]
    rect = fitz.Rect(box["X"], box["Y"], box["X"] + box["W"], box["Y"] + box["H"])

    # নতুন PDF তৈরি
    new_pdf = fitz.open()
    new_page = new_pdf.new_page(width=rect.width, height=rect.height)
    new_page.show_pdf_page(new_page.rect, doc, 0, clip=rect)

    pdf_bytes_out = io.BytesIO()
    new_pdf.save(pdf_bytes_out)
    return pdf_bytes_out.getvalue()

# --- যদি ফাইল আপলোড করা হয়
if uploaded_files:
    st.info(f"{len(uploaded_files)} টা PDF ফাইল পাওয়া গেছে ✔️")

    if st.button("🧩 Generate Combined PDF"):
        output_pdf = fitz.open()

        for i, file in enumerate(uploaded_files):
            st.write(f"Processing file {i+1} ➜ {file.name}")
            cropped_data = extract_box(file.read(), box)
            cropped_pdf = fitz.open("pdf", cropped_data)
            output_pdf.insert_pdf(cropped_pdf)

        # Save final output in memory
        final_bytes = io.BytesIO()
        output_pdf.save(final_bytes)
        st.success("✅ কাজ শেষ! নিচের বাটনে ক্লিক করে নতুন PDF নামাও:")

        st.download_button(
            label="📥 Download New PDF",
            data=final_bytes.getvalue(),
            file_name="combined_output.pdf",
            mime="application/pdf"
        )
else:
    st.warning("⬆️ উপরের বাটন দিয়ে কিছু PDF ফাইল আপলোড করো।")
