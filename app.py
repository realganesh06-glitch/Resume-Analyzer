import os
import json
import re
import time
from pathlib import Path

import requests
import streamlit as st
from PyPDF2 import PdfReader

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent / ".env")
except ImportError:
    pass

OPENAI_BASE_URL = os.environ.get("OPENAI_BASE_URL", "https://integrate.api.nvidia.com/v1").rstrip("/")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
MODEL = os.environ.get("MODEL_ID", "meta/llama-3.1-70b-instruct")


def extract_text_from_pdf(file) -> str:
    reader = PdfReader(file)
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
    return text


def analyze_resume(resume_text: str) -> dict:
    system_prompt = (
        "You are an expert career coach who reviews resumes. "
        "You will be given the text of a resume. You must respond with ONLY a JSON "
        "object (no markdown, no code fences) with exactly these keys:\n"
        '  "score": an integer from 0 to 100 rating the overall quality of the resume,\n'
        '  "skills": an array of strings listing the technical and soft skills you detected,\n'
        '  "tips": an array of exactly 3 strings, each a concrete suggestion to improve the resume.\n'
        "Do not include any text outside the JSON object."
    )
    user_prompt = f"Here is the resume text:\n\n{resume_text}"

    url = f"{OPENAI_BASE_URL.rstrip('/')}/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.2,
    }

    # retry with exponential backoff on 429 / 5xx
    max_retries = 4
    base_delay = 2.0
    response = None
    for attempt in range(max_retries):
        response = requests.post(url, headers=headers, json=payload, timeout=120)
        if response.status_code == 429 or 500 <= response.status_code < 600:
            if attempt < max_retries - 1:
                time.sleep(base_delay * (2 ** attempt))
                continue
            response.raise_for_status()
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]

        match = re.search(r"\{.*\}", content, re.DOTALL)
        if match:
            content = match.group(0)
        return json.loads(content)

    # all retries exhausted
    if response is not None:
        response.raise_for_status()
    raise RuntimeError("analyze_resume: exhausted retries with no response")


# ---------- Custom CSS ----------
def inject_css():
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@500;600;700;800&family=Inter:wght@400;500;600;700&display=swap');

        :root {
            --bg: #f7f9fc;
            --card-bg: #ffffff;
            --primary: #2563eb;
            --primary-dark: #1d4ed8;
            --navy: #0f1f3d;
            --accent-light: #eaf2ff;
            --soft-blue-grad-1: #e8f1ff;
            --soft-blue-grad-2: #f3f8ff;
            --muted: #64748b;
            --border: #e2e8f0;
            --shadow: 0 6px 24px rgba(15, 31, 61, 0.08);
            --shadow-sm: 0 2px 8px rgba(15, 31, 61, 0.06);
            --radius: 16px;
            --radius-sm: 12px;
        }

        html, body, [class*="stApp"] {
            background: var(--bg);
            font-family: 'Inter', sans-serif;
            color: var(--navy);
        }

        h1, h2, h3, h4, .hero-title, .nav-brand {
            font-family: 'Poppins', sans-serif !important;
            color: var(--navy) !important;
        }

        /* ---------- Top navigation bar ---------- */
        .topnav {
            position: sticky;
            top: 0;
            z-index: 999;
            background: var(--card-bg);
            border-bottom: 1px solid var(--border);
            box-shadow: var(--shadow-sm);
            padding: 14px 36px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin: -86px -16px 0 -16px;
            border-radius: 0;
        }
        .nav-brand {
            font-size: 22px;
            font-weight: 800;
            letter-spacing: -0.3px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .nav-brand .logo-dot {
            width: 30px; height: 30px;
            background: var(--primary);
            border-radius: 9px;
            display: inline-block;
            color: #fff;
            font-size: 16px;
            font-weight: 700;
            text-align: center;
            line-height: 30px;
        }
        .nav-links { display: flex; gap: 28px; }
        .nav-links a {
            color: var(--navy);
            font-weight: 500;
            font-size: 15px;
            text-decoration: none;
            opacity: 0.8;
            transition: opacity .2s, color .2s;
        }
        .nav-links a:hover { opacity: 1; color: var(--primary); }

        /* ---------- Hero ---------- */
        .hero {
            background: linear-gradient(135deg, var(--soft-blue-grad-1) 0%, var(--soft-blue-grad-2) 100%);
            border-radius: var(--radius);
            padding: 44px 40px;
            margin: 24px 0 12px 0;
            box-shadow: var(--shadow-sm);
            border: 1px solid var(--border);
        }
        .hero-title {
            font-size: 32px;
            font-weight: 800;
            letter-spacing: -0.5px;
            margin: 0 0 10px 0;
            line-height: 1.15;
        }
        .hero-sub {
            font-size: 17px;
            color: var(--muted);
            margin: 0;
            line-height: 1.5;
            max-width: 680px;
        }

        /* ---------- Cards ---------- */
        .card {
            background: var(--card-bg);
            border-radius: var(--radius);
            padding: 28px;
            box-shadow: var(--shadow);
            border: 1px solid var(--border);
            margin-top: 18px;
        }
        .card-title {
            font-family: 'Poppins', sans-serif;
            font-size: 20px;
            font-weight: 700;
            color: var(--navy);
            margin: 0 0 6px 0;
        }
        .card-sub { color: var(--muted); font-size: 14px; margin-bottom: 18px; }

        /* ---------- Upload card ---------- */
        .upload-card {
            border: 2px dashed #bfdbfe;
            border-radius: var(--radius);
            padding: 34px;
            text-align: center;
            background: linear-gradient(180deg, #fbfdff 0%, #f5f9ff 100%);
            transition: border-color .2s, box-shadow .2s;
        }
        .upload-card:hover { border-color: var(--primary); box-shadow: var(--shadow-sm); }
        .upload-icon { font-size: 40px; margin-bottom: 8px; }
        .upload-hint { color: var(--muted); font-size: 14px; margin-top: 10px; }

        /* ---------- Buttons ---------- */
        .btn-primary {
            background: var(--primary) !important;
            color: #fff !important;
            border: none !important;
            border-radius: 10px !important;
            padding: 11px 24px !important;
            font-family: 'Inter', sans-serif !important;
            font-weight: 600 !important;
            font-size: 15px !important;
            box-shadow: 0 4px 12px rgba(37, 99, 235, 0.25) !important;
            cursor: pointer;
        }
        div.stButton > button {
            background: var(--primary) !important;
            color: #fff !important;
            border: none !important;
            border-radius: 10px !important;
            padding: 10px 22px !important;
            font-weight: 600 !important;
            font-family: 'Inter', sans-serif !important;
            box-shadow: 0 4px 12px rgba(37, 99, 235, 0.25) !important;
        }
        div.stButton > button:hover {
            background: var(--primary-dark) !important;
        }

        /* ---------- File uploader button ---------- */
        [data-testid="stFileUploaderDropzone"] button,
        .stFileUploader button,
        [data-testid="stFileUploaderFile"] button {
            background: var(--primary) !important;
            color: #ffffff !important;
            border: none !important;
            border-radius: 10px !important;
            padding: 10px 22px !important;
            font-weight: 600 !important;
            font-family: 'Inter', sans-serif !important;
            font-size: 15px !important;
            box-shadow: 0 4px 12px rgba(37, 99, 235, 0.25) !important;
        }
        [data-testid="stFileUploaderDropzone"] button:hover,
        .stFileUploader button:hover {
            background: var(--primary-dark) !important;
            color: #ffffff !important;
        }
        [data-testid="stFileUploaderDropzone"],
        .stFileUploader {
            border-radius: var(--radius) !important;
        }

        /* ---------- Tabs ---------- */
        .stTabs [data-baseweb="tab-list"] { gap: 8px; }
        .stTabs [data-baseweb="tab"] {
            background: transparent;
            border-radius: 10px 10px 0 0;
            padding: 12px 20px;
            font-family: 'Inter', sans-serif;
            font-weight: 600;
            color: var(--muted);
            border-bottom: 3px solid transparent;
        }
        .stTabs [aria-selected="true"] {
            color: var(--primary) !important;
            border-bottom-color: var(--primary) !important;
            background: transparent !important;
        }
        .stTabs [data-baseweb="tab-highlight"] { background-color: var(--primary) !important; }
        .stTabs [data-baseweb="tab-border"] { display: none; }

        /* ---------- Score ring ---------- */
        .ring-wrap {
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 10px;
            padding: 14px 0 4px 0;
        }
        .ring {
            -- pct: 0;
            --size: 180px;
            --thickness: 16px;
            --clr: #16a34a;
            --track: #e6f0ff;
            width: var(--size);
            height: var(--size);
            border-radius: 50%;
            display: grid;
            place-items: center;
            background:
                conic-gradient(var(--clr) calc(var(--pct) * 1%), var(--track) 0);
            position: relative;
        }
        .ring::before {
            content: "";
            position: absolute;
            inset: var(--thickness);
            background: var(--card-bg);
            border-radius: 50%;
            box-shadow: inset 0 2px 6px rgba(15,31,61,0.05);
        }
        .ring-num {
            position: relative;
            z-index: 1;
            font-family: 'Poppins', sans-serif;
            font-weight: 800;
            font-size: 38px;
            color: var(--navy);
            line-height: 1;
        }
        .ring-num small { font-size: 16px; color: var(--muted); font-weight: 600; }
        .ring-label { font-family: 'Inter', sans-serif; font-weight: 600; color: var(--muted); font-size: 14px; }

        /* ---------- Skill pills ---------- */
        .pill-row { display: flex; flex-wrap: wrap; gap: 10px; }
        .pill {
            background: var(--accent-light);
            color: var(--navy);
            font-weight: 600;
            font-size: 14px;
            padding: 8px 16px;
            border-radius: 999px;
            border: 1px solid #d6e4ff;
            font-family: 'Inter', sans-serif;
        }
        .empty-note { color: var(--muted); font-style: italic; }

        /* ---------- Tips ---------- */
        .tips-list { list-style: none; padding: 0; margin: 0; }
        .tips-list li {
            display: flex;
            align-items: flex-start;
            gap: 14px;
            padding: 14px 0;
            border-bottom: 1px solid var(--border);
        }
        .tips-list li:last-child { border-bottom: none; }
        .tip-num {
            flex: 0 0 32px;
            height: 32px;
            width: 32px;
            border-radius: 50%;
            background: var(--accent-light);
            color: var(--primary);
            font-family: 'Poppins', sans-serif;
            font-weight: 700;
            font-size: 15px;
            display: grid;
            place-items: center;
        }
        .tip-text { font-size: 15px; color: var(--navy); line-height: 1.55; }

        /* ---------- History ---------- */
        .history-item {
            padding: 16px 18px;
            border: 1px solid var(--border);
            border-radius: var(--radius-sm);
            margin-bottom: 12px;
            box-shadow: var(--shadow-sm);
            background: var(--card-bg);
        }
        .history-top { display: flex; justify-content: space-between; align-items: center; }
        .history-name { font-weight: 600; color: var(--navy); font-family: 'Poppins', sans-serif; }
        .history-score {
            font-family: 'Poppins', sans-serif; font-weight: 700;
            padding: 4px 12px; border-radius: 999px; font-size: 14px;
        }
        .score-badge-green { background: #dcfce7; color: #166534; }
        .score-badge-amber { background: #fef3c7; color: #92400e; }
        .score-badge-red   { background: #fee2e2; color: #991b1b; }

        /* ---------- Misc Streamlit cleanup ---------- */
        section[data-testid="stMarkdownContainer"] p { color: inherit; }
        .block-container { padding-top: 1rem !important; max-width: 1100px; }
        .stAlert { border-radius: var(--radius-sm) !important; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def topnav():
    st.markdown(
        """
        <div class="topnav">
            <div class="nav-brand">
                <span class="logo-dot">R</span> ResumeLab
            </div>
            <div class="nav-links">
                <a href="#upload">Upload</a>
                <a href="#results">Results</a>
                <a href="#history">History</a>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def hero():
    st.markdown(
        """
        <div class="hero">
            <h1 class="hero-title">Land your next job with a resume that stands out</h1>
            <p class="hero-sub">Upload your resume PDF and our AI career coach will score it out of 100,
            surface the skills recruiters will notice, and give you three concrete tips to improve.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_score_ring(score):
    if isinstance(score, (int, float)):
        pct = max(0, min(100, int(score)))
        if pct >= 80:
            label = "Excellent"
        elif pct >= 60:
            label = "Good — keep refining"
        else:
            label = "Needs work"
    else:
        pct = 0
        label = "No score"

    st.markdown(
        f"""
        <div class="ring-wrap">
            <div class="ring" style="--pct:{pct};">
                <div class="ring-num">{pct}<small>/100</small></div>
            </div>
            <div class="ring-label">{label}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_skills(skills):
    if not skills:
        st.markdown('<div class="empty-note">No skills detected.</div>', unsafe_allow_html=True)
        return
    pills = "".join(f'<span class="pill">{s}</span>' for s in skills)
    st.markdown(f'<div class="pill-row">{pills}</div>', unsafe_allow_html=True)


def render_tips(tips):
    if not tips:
        st.markdown('<div class="empty-note">No tips returned.</div>', unsafe_allow_html=True)
        return
    items = "".join(
        f'<li><span class="tip-num">{i}</span><span class="tip-text">{t}</span></li>'
        for i, t in enumerate(tips, 1)
    )
    st.markdown(f'<ul class="tips-list">{items}</ul>', unsafe_allow_html=True)


def score_badge(score):
    if isinstance(score, (int, float)):
        s = int(score)
    else:
        s = 0
    if s >= 80:
        return f'<span class="history-score score-badge-green">{s}/100</span>'
    if s >= 60:
        return f'<span class="history-score score-badge-amber">{s}/100</span>'
    return f'<span class="history-score score-badge-red">{s}/100</span>'


def render_history():
    history = st.session_state.get("history", [])
    if not history:
        st.markdown(
            '<div class="empty-note">No analyses yet. Upload a resume to get started.</div>',
            unsafe_allow_html=True,
        )
        return
    for item in reversed(history):
        st.markdown(
            f"""
            <div class="history-item">
                <div class="history-top">
                    <span class="history-name">{item['name']}</span>
                    {score_badge(item['score'])}
                </div>
                <div style="color:var(--muted); font-size:13px; margin-top:6px;">
                    {len(item['skills'])} skills detected &middot; 3 tips
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    if st.button("Clear history", key="clear_hist"):
        st.session_state["history"] = []
        st.rerun()


# ---------- App ----------
st.set_page_config(page_title="ResumeLab — AI Resume Analyzer", page_icon="📄", layout="centered")

if "history" not in st.session_state:
    st.session_state["history"] = []

inject_css()
topnav()
hero()

if not OPENAI_API_KEY:
    st.error(
        "OPENAI_API_KEY environment variable is not set. "
        "Please set it before running the app."
    )
    st.stop()

upload_tab, results_tab, history_tab = st.tabs(["Upload", "Results", "History"])

# per-tab view state so results show inline without manual tab switching
if "view" not in st.session_state:
    st.session_state["view"] = "upload"

# ----- Upload tab -----
with upload_tab:
    st.markdown('<div id="upload"></div>', unsafe_allow_html=True)
    result = st.session_state.get("result")

    if st.session_state["view"] == "result" and result:
        # ---- Inline results view (replaces the upload card) ----
        st.markdown(
            f"""
            <div class="card">
                <div class="card-title">Resume Score</div>
                <div class="card-sub">An overall quality rating out of 100 for
                <code>{st.session_state.get('resume_name','')}</code>.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        render_score_ring(result.get("score", 0))

        with st.expander("View extracted resume text", expanded=False):
            st.text(st.session_state.get("resume_text", ""))

        st.markdown(
            """
            <div class="card">
                <div class="card-title">Detected Skills</div>
                <div class="card-sub">Technical and soft skills identified in your resume.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        render_skills(result.get("skills", []))

        st.markdown(
            """
            <div class="card">
                <div class="card-title">Improvement Tips</div>
                <div class="card-sub">Three concrete suggestions to strengthen your resume.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        render_tips(result.get("tips", []))

        if st.button("Analyze another resume", key="reset_btn", type="primary"):
            st.session_state["view"] = "upload"
            st.session_state["result"] = None
            st.rerun()
    else:
        # ---- Upload view ----
        st.markdown(
            """
            <div class="card">
                <div class="card-title">Upload your resume</div>
                <div class="card-sub">PDF only. Your file is processed in-memory and never stored.</div>
                <div class="upload-card">
                    <div class="upload-icon">📄</div>
                    <div style="font-weight:600; color:var(--navy); font-size:17px;">
                        Drag & drop your resume here
                    </div>
                    <div class="upload-hint">or click below to browse — PDF up to 10MB</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        uploaded_file = st.file_uploader("Browse file", type=["pdf"], label_visibility="collapsed")
        if uploaded_file is not None:
            st.markdown(f"**Selected file:** `{uploaded_file.name}`")
            if st.button("Analyze resume", key="analyze_btn", type="primary"):
                with st.spinner("Extracting text from PDF..."):
                    try:
                        resume_text = extract_text_from_pdf(uploaded_file)
                    except Exception as e:
                        st.error(f"Failed to read PDF: {e}")
                        st.stop()

                if not resume_text.strip():
                    st.warning("No text could be extracted from this PDF. Try a different file.")
                    st.stop()

                st.session_state["resume_text"] = resume_text
                st.session_state["resume_name"] = uploaded_file.name

                with st.spinner(f"Analyzing resume with {MODEL}..."):
                    try:
                        result = analyze_resume(resume_text)
                    except requests.exceptions.HTTPError as e:
                        st.error(f"API request failed: {e}")
                        if e.response is not None:
                            st.text(
                                f"Model: {MODEL}\n"
                                f"URL: {OPENAI_BASE_URL}\n"
                                f"Status: {e.response.status_code}\n"
                                f"Body:\n{e.response.text}"
                            )
                        st.stop()
                    except json.JSONDecodeError as e:
                        st.error(f"Could not parse the model's response as JSON: {e}")
                        st.stop()

                st.session_state["result"] = result
                st.session_state["history"].append(
                    {
                        "name": uploaded_file.name,
                        "score": result.get("score", 0),
                        "skills": result.get("skills", []),
                        "tips": result.get("tips", []),
                    }
                )
                st.session_state["view"] = "result"
                st.toast("✅ Resume analyzed successfully!")
                st.rerun()

# ----- Results tab -----
with results_tab:
    st.markdown('<div id="results"></div>', unsafe_allow_html=True)
    result = st.session_state.get("result")
    if not result:
        st.markdown(
            '<div class="empty-note">No results yet. Upload and analyze a resume first.</div>',
            unsafe_allow_html=True,
        )
    else:
        # Score card
        st.markdown(
            """
            <div class="card">
                <div class="card-title">Resume Score</div>
                <div class="card-sub">An overall quality rating out of 100.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        render_score_ring(result.get("score", 0))

        # Extracted text
        with st.expander("View extracted resume text", expanded=False):
            st.text(st.session_state.get("resume_text", ""))

        # Skills card
        st.markdown(
            """
            <div class="card">
                <div class="card-title">Detected Skills</div>
                <div class="card-sub">Technical and soft skills identified in your resume.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        render_skills(result.get("skills", []))

        # Tips card
        st.markdown(
            """
            <div class="card">
                <div class="card-title">Improvement Tips</div>
                <div class="card-sub">Three concrete suggestions to strengthen your resume.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        render_tips(result.get("tips", []))

# ----- History tab -----
with history_tab:
    st.markdown('<div id="history"></div>', unsafe_allow_html=True)
    st.markdown(
        """
        <div class="card">
            <div class="card-title">Analysis History</div>
            <div class="card-sub">Every resume you analyze is listed here for your reference.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    render_history()
