import streamlit as st
from PyPDF2 import PdfReader
import firebase_admin
from firebase_admin import credentials, firestore
import datetime

# ===============================
# FIREBASE INITIALIZATION
# ===============================
FIREBASE_KEY_PATH = "firebase_key.json"  # <-- Replace with your Firebase JSON

if not firebase_admin._apps:
    cred = credentials.Certificate(FIREBASE_KEY_PATH)
    firebase_admin.initialize_app(cred)

db = firestore.client()

# ===============================
# STREAMLIT PAGE CONFIG
# ===============================
st.set_page_config(
    page_title="Placement Readiness Analyzer",
    layout="wide"
)

st.title("🚀 Placement Readiness Analyzer")
st.caption("Resume Analysis • Skill Gap Detection • Personalized Learning Timeline • AI Feedback")

# ===============================
# SESSION STATE
# ===============================
if "resume_text" not in st.session_state:
    st.session_state.resume_text = ""
if "matched" not in st.session_state:
    st.session_state.matched = []
if "missing" not in st.session_state:
    st.session_state.missing = []
if "score" not in st.session_state:
    st.session_state.score = 0
if "analyzed" not in st.session_state:
    st.session_state.analyzed = False

# ===============================
# INPUT SECTION
# ===============================
uploaded_file = st.file_uploader("📄 Upload Resume (PDF)", type=["pdf"])

job_desc = st.text_area(
    "📝 Paste Job Description",
    placeholder="Example: Software Engineer, QA Automation, Data Analyst...",
    height=180
)

# ===============================
# SKILL DATABASE & REASONS
# ===============================
SKILL_DB = [
    "python", "java", "sql", "data structures", "algorithms",
    "git", "docker", "rest api", "selenium", "machine learning",
    "cloud computing", "testing", "automation"
]

LEARNING_REASONS = {
    "python": "Foundation for most development and automation roles",
    "java": "Builds strong object-oriented programming concepts",
    "data structures": "Required to write optimized and efficient code",
    "algorithms": "Essential for technical interviews and problem solving",
    "sql": "Needed to manage and query databases",
    "git": "Industry standard for version control",
    "docker": "Helps deploy applications consistently",
    "rest api": "Used to connect frontend and backend systems",
    "selenium": "Core skill for QA automation",
    "machine learning": "Advanced skill for intelligent systems",
    "cloud computing": "Used for scalable and real-world deployments",
    "testing": "Builds software reliability knowledge",
    "automation": "Improves efficiency and reduces manual work"
}

# ===============================
# FUNCTIONS
# ===============================
def extract_text_from_pdf(pdf_file):
    """Extract text from PDF using PyPDF2"""
    text = ""
    reader = PdfReader(pdf_file)
    for page in reader.pages:
        text += page.extract_text() or ""
    return text.lower()


def analyze_skills(resume_text, job_description):
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

    score = int((len(matched) / max(len(matched) + len(missing), 1)) * 100)
    return matched, missing, score


def build_learning_timeline(missing_skills):
    """Ordered roadmap with foundational -> advanced skills"""
    order = [
        "python", "java", "data structures", "algorithms",
        "sql", "rest api", "git", "docker", "selenium", "machine learning", "cloud computing",
        "testing", "automation"
    ]
    timeline = {}
    week = 1
    for skill in order:
        if skill in missing_skills:
            reason = LEARNING_REASONS.get(skill, "Important skill for this role")
            timeline[f"Week {week}"] = (skill.title(), reason)
            week += 1
    for skill in missing_skills:
        if skill not in order:
            reason = LEARNING_REASONS.get(skill, "Important skill for this role")
            timeline[f"Week {week}"] = (skill.title(), reason)
            week += 1
    return timeline


def save_to_firebase(job_desc, matched, missing, score):
    db.collection("analysis_results").add({
        "job_description": job_desc,
        "matched_skills": matched,
        "missing_skills": missing,
        "score": score,
        "timestamp": datetime.datetime.now()
    })


def generate_ai_feedback(resume, job_desc):
    """Mock AI feedback for resume and job description"""
    resume = resume.lower()
    job_desc = job_desc.lower()
    skills = SKILL_DB

    matched = [s for s in skills if s in resume and s in job_desc]
    missing = [s for s in skills if s in job_desc and s not in resume]

    feedback = []
    feedback.append("✅ Your resume shows good foundational skills.")
    if matched:
        feedback.append(f"Strengths detected: {', '.join(matched)}")
    if missing:
        feedback.append(f"Skills to improve or learn: {', '.join(missing)}")
    feedback.append("📌 Suggestion: Add relevant projects and achievements to strengthen your resume.")
    feedback.append("📌 Tip: Focus on missing skills in the next few weeks based on difficulty and importance.")
    return "\n".join(feedback)

# ===============================
# ANALYZE BUTTON
# ===============================
if st.button("🔍 Analyze Placement Readiness"):
    if uploaded_file and job_desc.strip():
        with st.spinner("Analyzing resume..."):
            st.session_state.resume_text = extract_text_from_pdf(uploaded_file)
            st.session_state.matched, st.session_state.missing, st.session_state.score = analyze_skills(
                st.session_state.resume_text, job_desc
            )
            save_to_firebase(
                job_desc,
                st.session_state.matched,
                st.session_state.missing,
                st.session_state.score
            )
            st.session_state.analyzed = True
            st.success("✅ Analysis saved to Firebase successfully!")
    else:
        st.warning("Please upload a resume and paste a job description.")

# ===============================
# OUTPUT SECTION
# ===============================
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

    # Learning Timeline
    st.subheader("🗓️ Personalized Learning Timeline")
    timeline = build_learning_timeline(st.session_state.missing)
    if timeline:
        for week, (skill, reason) in timeline.items():
            st.info(f"**{week}: {skill}**\n\n📌 {reason}")
    else:
        st.success("🎉 You already match the required skills for this role!")

    # AI Feedback
    st.subheader("🤖 AI Feedback Summary")
    feedback_text = generate_ai_feedback(st.session_state.resume_text, job_desc)
    st.markdown(feedback_text)
