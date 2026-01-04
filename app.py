import streamlit as st
import re
from io import BytesIO
from pdf2image import convert_from_bytes
import pytesseract
from PyPDF2 import PdfReader
import google.generativeai as genai

# =======================
# GEMINI API SETUP (FORCED WORKING – WINDOWS SAFE)
# =======================
if "GEMINI_API_KEY" not in st.session_state:
    st.session_state.GEMINI_API_KEY = ""

if not st.session_state.GEMINI_API_KEY:
    st.info("🔑 Enter your Google Gemini API key to enable AI feedback")
    st.session_state.GEMINI_API_KEY = st.text_input(
        "Gemini API Key",
        type="password"
    )

if st.session_state.GEMINI_API_KEY:
    genai.configure(api_key=st.session_state.GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-pro")
else:
    model = None

# =======================
# SESSION STATE INIT
# =======================
for key, value in {
    "resume_text": "",
    "matched_skills": [],
    "missing_skills": [],
    "placement_score": 0,
    "ai_feedback": ""
}.items():
    if key not in st.session_state:
        st.session_state[key] = value

# =======================
# PAGE TITLE
# =======================
st.title("📊 Placement Readiness Analyzer")

# =======================
# INPUTS
# =======================
uploaded_file = st.file_uploader("📄 Upload Resume (PDF)", type=["pdf"])
job_desc = st.text_area(
    "📝 Paste Job Description",
    height=200,
    placeholder="Python, Java, SQL, Data Structures, Algorithms..."
)

# =======================
# FUNCTIONS
# =======================
def extract_text_from_pdf(pdf_file):
    pdf_bytes = pdf_file.read()
    text = ""

    # 1️⃣ Try text-based PDF extraction
    try:
        reader = PdfReader(BytesIO(pdf_bytes))
        for page in reader.pages:
            extracted = page.extract_text()
            if extracted:
                text += extracted
    except:
        pass

    # 2️⃣ OCR fallback for scanned PDFs
    if not text.strip():
        images = convert_from_bytes(pdf_bytes)
        for img in images:
            text += pytesseract.image_to_string(img)

    return text.lower()

def analyze_skills(resume_text, job_description):
    job_skills = [
        skill.strip().lower()
        for skill in re.split(r",|\n", job_description)
        if skill.strip()
    ]

    matched = [s for s in job_skills if s in resume_text]
    missing = [s for s in job_skills if s not in resume_text]
    score = int((len(matched) / len(job_skills)) * 100) if job_skills else 0

    return matched, missing, score

def get_ai_feedback(resume_text, job_description, missing_skills):
    if model is None:
        return "❌ Gemini API key not provided."

    prompt = f"""
You are a professional placement trainer.

Job Description:
{job_description}

Resume Content:
{resume_text[:3000]}

Missing Skills:
{', '.join(missing_skills)}

Provide:
1. Resume improvement suggestions
2. Skill gap advice
3. Interview preparation tips
"""

    response = model.generate_content(prompt)
    return response.text

# =======================
# BUTTONS
# =======================
col1, col2 = st.columns(2)

with col1:
    if st.button("🔍 Analyze Skills"):
        if uploaded_file:
            with st.spinner("Analyzing resume..."):
                st.session_state.resume_text = extract_text_from_pdf(uploaded_file)
                (
                    st.session_state.matched_skills,
                    st.session_state.missing_skills,
                    st.session_state.placement_score
                ) = analyze_skills(st.session_state.resume_text, job_desc)
        else:
            st.warning("Please upload a resume!")

with col2:
    if st.button("🤖 Get AI Feedback"):
        if st.session_state.resume_text:
            with st.spinner("Generating AI feedback..."):
                st.session_state.ai_feedback = get_ai_feedback(
                    st.session_state.resume_text,
                    job_desc,
                    st.session_state.missing_skills
                )
        else:
            st.warning("Please analyze skills first!")

# =======================
# OUTPUT
# =======================
if st.session_state.resume_text:
    st.subheader("📄 Resume Preview")
    st.text_area(
        "Extracted Text",
        st.session_state.resume_text[:2000],
        height=200
    )

    st.subheader("📌 Skill Analysis")
    st.success(f"✅ Matched Skills: {st.session_state.matched_skills}")
    st.error(f"❌ Missing Skills: {st.session_state.missing_skills}")
    st.metric("📈 Placement Readiness Score", f"{st.session_state.placement_score}%")

if st.session_state.ai_feedback:
    st.divider()
    st.subheader("🧠 Gemini AI Feedback")
    st.markdown(st.session_state.ai_feedback)

