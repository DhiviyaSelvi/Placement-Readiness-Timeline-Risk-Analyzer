import streamlit as st
import re
from pdf2image import convert_from_bytes
import pytesseract
from PyPDF2 import PdfReader

# =======================
# PAGE CONFIG
# =======================
st.set_page_config(
    page_title="Placement Readiness Analyzer",
    layout="wide"
)

st.title("🚀 Placement Readiness Analyzer")
st.caption("Resume Analysis • Skill Gap Detection • Learning Timeline")

# =======================
# SESSION STATE INIT
# =======================
if "resume_text" not in st.session_state:
    st.session_state.resume_text = ""
if "matched" not in st.session_state:
    st.session_state.matched = []
if "missing" not in st.session_state:
    st.session_state.missing = []
if "score" not in st.session_state:
    st.session_state.score = 0
if "feedback" not in st.session_state:
    st.session_state.feedback = ""
if "analyzed" not in st.session_state:
    st.session_state.analyzed = False

# =======================
# INPUT SECTION
# =======================
uploaded_file = st.file_uploader("📄 Upload Resume (PDF)", type=["pdf"])

job_desc = st.text_area(
    "📝 Paste Job Description",
    placeholder="Paste your job description here...",
    height=180
)

# =======================
# FUNCTIONS
# =======================
def extract_text_from_pdf(pdf_file):
    text = ""
    pdf_bytes = pdf_file.read()

    try:
        reader = PdfReader(pdf_bytes)
        for page in reader.pages:
            text += page.extract_text() or ""
    except:
        pass

    # OCR fallback
    if not text.strip():
        images = convert_from_bytes(pdf_bytes)
        for img in images:
            text += pytesseract.image_to_string(img)

    return text.lower()


def analyze_skills(resume_text, job_description):
    SKILL_DB = [
        "python",
        "java",
        "sql",
        "data structures",
        "algorithms",
        "git",
        "docker",
        "rest apis",
        "restful apis",
        "machine learning",
        "cloud computing"
    ]

    resume_text = resume_text.lower()
    job_description = job_description.lower()

    matched = []
    missing = []

    for skill in SKILL_DB:
        if skill in job_description:
            if skill in resume_text:
                matched.append(skill)
            else:
                missing.append(skill)

    score = int((len(matched) / len(SKILL_DB)) * 100)

    return matched, missing, score


def learning_timeline_with_reason(missing):
    order = [
        ("python", "Easy to learn and forms the foundation for many technologies"),
        ("java", "Builds strong object-oriented programming concepts"),
        ("data structures", "Required to write optimized and efficient code"),
        ("algorithms", "Essential for technical interviews and problem solving"),
        ("sql", "Needed to manage and query databases"),
        ("rest apis", "Used to connect frontend and backend systems"),
        ("git", "Industry standard for version control"),
        ("docker", "Helps deploy applications consistently"),
        ("machine learning", "Advanced skill for intelligent systems"),
        ("cloud computing", "Used for scalable and real-world deployments")
    ]

    timeline = {}
    week = 1

    for skill, reason in order:
        if skill in missing:
            timeline[f"Week {week}"] = (skill.title(), reason)
            week += 1

    return timeline


def mock_ai_feedback(score, matched, missing):
    feedback = []

    feedback.append(
        "Your resume demonstrates a good academic foundation with practical exposure."
    )

    if matched:
        feedback.append(
            f"You already possess skills like {', '.join(matched[:3])}, which align with the job role."
        )

    if missing:
        feedback.append(
            f"To improve placement readiness, focus on acquiring {', '.join(missing[:3])}."
        )

    feedback.append(
        "Strengthening project descriptions and highlighting measurable outcomes will enhance your resume."
    )

    feedback.append(
        "Overall, you are suitable for entry-level roles with focused skill improvement."
    )

    return "\n\n".join(feedback)

# =======================
# ANALYZE BUTTON
# =======================
if st.button("🔍 Analyze Skills"):
    if uploaded_file and job_desc.strip():
        with st.spinner("Analyzing resume..."):
            st.session_state.resume_text = extract_text_from_pdf(uploaded_file)
            (
                st.session_state.matched,
                st.session_state.missing,
                st.session_state.score,
            ) = analyze_skills(st.session_state.resume_text, job_desc)

            st.session_state.analyzed = True
            st.session_state.feedback = ""
    else:
        st.warning("Please upload a resume and paste a job description.")

# =======================
# OUTPUT SECTION
# =======================
if st.session_state.analyzed:
    st.divider()
    st.subheader("📊 Placement Readiness Result")

    st.progress(st.session_state.score / 100)
    st.metric("Readiness Score", f"{st.session_state.score}%")

    col1, col2 = st.columns(2)

    with col1:
        st.success("✅ Matched Skills")
        st.write(st.session_state.matched or "None")

    with col2:
        st.error("❌ Missing Skills")
        st.write(st.session_state.missing or "None")

    # =======================
    # LEARNING TIMELINE
    # =======================
    st.subheader("🗓️ Personalized Learning Timeline")
    st.caption("Skills are ordered from foundational to advanced with reasons.")

    timeline = learning_timeline_with_reason(st.session_state.missing)

    for week, (skill, reason) in timeline.items():
        st.info(f"**{week}: {skill}**\n\n📌 Why this week? {reason}")

    # =======================
    # AI FEEDBACK BUTTON
    # =======================
    st.divider()
    if st.button("🤖 Get AI Feedback"):
        st.session_state.feedback = mock_ai_feedback(
            st.session_state.score,
            st.session_state.matched,
            st.session_state.missing,
        )

# =======================
# AI FEEDBACK OUTPUT
# =======================
if st.session_state.feedback:
    st.subheader("🧠 AI Feedback Summary")
    st.markdown(st.session_state.feedback)
