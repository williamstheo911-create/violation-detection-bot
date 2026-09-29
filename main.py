import streamlit as st
import os
from google import genai
from google.genai import types
from PIL import Image
import pypdf

# Page config
st.set_page_config(page_title="Violation Detection Bot", page_icon="🔍", layout="wide")

st.title("🔍 Document & Picture Violation Detection Bot")
st.write("Upload documents (PDF) or images to check them against your compliance rules.")

# Initialize Gemini Client using the Railway environment variable
api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    st.error("⚠️ GEMINI_API_KEY is missing! Please add it in your Railway Variables tab.")
else:
    client = genai.Client(api_key=api_key)

    # Sidebar for custom rules
    st.sidebar.header("⚙️ Violation Rulebook")
    default_rules = (
        "1. Check for missing mandatory legal clauses or liability limits.\n"
        "2. Detect safety gear violations (e.g., missing hardhats, vests) in pictures.\n"
        "3. Look for expired dates, incorrect formatting, or unauthorized terms."
    )
    custom_rules = st.sidebar.text_area("Define what constitutes a violation:", value=default_rules, height=150)

    # File uploader
    uploaded_file = st.file_uploader("Upload a PDF document or an Image (PNG, JPG)", type=["pdf", "png", "jpg", "jpeg"])

    if uploaded_file is not None:
        file_extension = uploaded_file.name.split(".")[-1].lower()

        # Display preview / content info
        if file_extension in ["png", "jpg", "jpeg"]:
            image = Image.open(uploaded_file)
            st.image(image, caption="Uploaded Image Preview", use_container_width=True)
        elif file_extension == "pdf":
            st.info(f"📄 PDF Uploaded: `{uploaded_file.name}`")

        # Analyze Button
        if st.button("🚨 Run Violation Check", type="primary"):
            with st.spinner("Analyzing document/image for violations..."):
                try:
                    contents = []
                    prompt = (
                        f"You are an expert compliance auditor. Analyze the attached file strictly against these rules:\n"
                        f"{custom_rules}\n\n"
                        f"Provide a clear, structured report listing:\n"
                        f"1. Overall Status (PASS / FAIL)\n"
                        f"2. Detected Violations (with severity and descriptions)\n"
                        f"3. Recommendations for Correction"
                    )
                    contents.append(prompt)

                    # Handle image inputs
                    if file_extension in ["png", "jpg", "jpeg"]:
                        img_bytes = uploaded_file.getvalue()
                        contents.append(types.Part.from_bytes(data=img_bytes, mime_type=f"image/{file_extension}"))

                    # Handle PDF inputs
                    elif file_extension == "pdf":
                        reader = pypdf.PdfReader(uploaded_file)
                        pdf_text = ""
                        for page in reader.pages:
                            text = page.extract_text()
                            if text:
                                pdf_text += text + "\n"
                        contents.append(f"Document Text Content:\n{pdf_text}")

                    # Call Gemini 2.5 Flash (fast and multimodal)
                    response = client.models.generate_content(
                        model='gemini-2.5-flash',
                        contents=contents
                    )

                    st.markdown("---")
                    st.subheader("📋 Violation & Compliance Report")
                    st.markdown(response.text)

                except Exception as e:
                    st.error(f"An error occurred during analysis: {e}")
