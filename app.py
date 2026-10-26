import streamlit as st
import json
import os
import io
import csv
from datetime import datetime
from pypdf import PdfReader
from ai_service import generate_study_material

st.set_page_config(page_title="AI Revision Studio", layout="wide", page_icon="📚")

# --- CUSTOM MODERN UI STYLING ---
st.markdown("""
<style>
    .stApp {
        background-color: #0d1117;
        color: #e6edf3;
        font-family: 'Segoe UI', -apple-system, Roboto, sans-serif;
    }
    div[data-testid="stExpander"] {
        border: 1px solid #30363d !important;
        background: #161b22 !important;
        border-radius: 12px !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
    }
    button[kind="primary"] {
        background: linear-gradient(135deg, #2563eb 0%, #7c3aed 100%) !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
    }
    .flashcard-box {
        background: #161b22;
        border: 1px solid #388bfd;
        border-radius: 16px;
        padding: 35px 25px;
        min-height: 220px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        text-align: center;
        box-shadow: 0 8px 24px rgba(0,0,0,0.4);
        margin: 15px 0;
    }
    .flashcard-label {
        font-size: 13px;
        letter-spacing: 1.5px;
        text-transform: uppercase;
        color: #58a6ff;
        font-weight: 700;
        margin-bottom: 12px;
    }
    .flashcard-content {
        font-size: 20px;
        font-weight: 500;
        color: #f0f6fc;
        line-height: 1.5;
    }
    .score-banner {
        background: #161b22;
        border: 1px solid #30363d;
        border-radius: 12px;
        padding: 16px 20px;
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

# --- ZERO-DEPENDENCY PRINTABLE GUIDE GENERATOR ---
def create_printable_guide(study_data):
    cards_html = "".join([
        f"""
        <div class="card">
            <div class="card-front"><strong>Card #{i}:</strong> {c['front']}</div>
            <div class="card-back"><strong>Answer:</strong> {c['back']}</div>
        </div>
        """ for i, c in enumerate(study_data.get("flashcards", []), 1)
    ])

    quiz_html = "".join([
        f"""
        <div class="quiz-item">
            <p><strong>Q{i}. {q['question']}</strong></p>
            <ul>{''.join([f'<li>{opt}</li>' for opt in q['options']])}</ul>
            <p class="answer"><strong>Correct Answer:</strong> {q['options'][q['correct_index']]}<br>
            <em>Explanation: {q['explanation']}</em></p>
        </div>
        """ for i, q in enumerate(study_data.get("quiz", []), 1)
    ])

    return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>AI Revision Guide</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif;
            color: #1a202c;
            line-height: 1.6;
            margin: 40px;
        }}
        h1 {{ color: #2563eb; border-bottom: 2px solid #e2e8f0; padding-bottom: 10px; }}
        h2 {{ color: #1e293b; margin-top: 30px; border-bottom: 1px solid #cbd5e1; padding-bottom: 6px; }}
        .summary-box {{ background: #f8fafc; border-left: 4px solid #2563eb; padding: 15px; margin: 15px 0; }}
        .card {{ border: 1px solid #e2e8f0; border-radius: 8px; padding: 12px 16px; margin: 10px 0; background: #fff; page-break-inside: avoid; }}
        .card-front {{ color: #0f172a; margin-bottom: 6px; }}
        .card-back {{ color: #475569; }}
        .quiz-item {{ margin: 18px 0; padding: 12px; border-left: 3px solid #10b981; background: #f0fdf4; page-break-inside: avoid; }}
        .answer {{ color: #065f46; margin-top: 6px; }}
        @media print {{
            body {{ margin: 15mm; }}
        }}
    </style>
</head>
<body>
    <h1>AI Study Revision Guide</h1>
    <p><em>Generated on {datetime.now().strftime("%Y-%m-%d %H:%M")}</em></p>

    <h2>📌 Topic Summary</h2>
    <div class="summary-box">{study_data.get("summary", "N/A")}</div>

    <h2>🗂️ Flashcard Deck</h2>
    {cards_html}

    <h2>📝 Practice Quiz & Answer Key</h2>
    {quiz_html}
</body>
</html>
"""

# --- PERSISTENT STORAGE ---
USER_DB_FILE = "users.json"
HISTORY_DB_FILE = "history.json"

def load_users():
    if not os.path.exists(USER_DB_FILE):
        default_users = {"student": "hackathon123", "demo": "demo123"}
        with open(USER_DB_FILE, "w") as f:
            json.dump(default_users, f, indent=2)
        return default_users
    try:
        with open(USER_DB_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {}

def save_user(username, password):
    users = load_users()
    users[username] = password
    with open(USER_DB_FILE, "w") as f:
        json.dump(users, f, indent=2)

def load_user_history(username):
    if not os.path.exists(HISTORY_DB_FILE):
        return []
    try:
        with open(HISTORY_DB_FILE, "r") as f:
            return json.load(f).get(username, [])
    except Exception:
        return []

def save_to_history(username, study_data):
    all_history = {}
    if os.path.exists(HISTORY_DB_FILE):
        try:
            with open(HISTORY_DB_FILE, "r") as f:
                all_history = json.load(f)
        except Exception:
            all_history = {}
    
    if username not in all_history:
        all_history[username] = []
        
    record = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "title": study_data.get("summary", "Revision Set")[:40] + "...",
        "data": study_data
    }
    all_history[username].insert(0, record)
    with open(HISTORY_DB_FILE, "w") as f:
        json.dump(all_history, f, indent=2)

# --- SESSION STATES ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "study_set" not in st.session_state:
    st.session_state.study_set = None
if "card_index" not in st.session_state:
    st.session_state.card_index = 0
if "card_flipped" not in st.session_state:
    st.session_state.card_flipped = False
if "celebrated" not in st.session_state:
    st.session_state.celebrated = False

# --- AUTHENTICATION SCREEN ---
def render_auth_page():
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        st.markdown("<h2 style='text-align: center;'>📚 AI Revision Studio</h2>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: gray;'>Sign in to access your revision decks & quizzes</p>", unsafe_allow_html=True)
        
        auth_mode = st.radio("Choose action:", ["Login", "Sign Up"], horizontal=True)
        
        with st.form("auth_form"):
            uname = st.text_input("Username").strip()
            pword = st.text_input("Password", type="password").strip()
            submitted = st.form_submit_button("Continue", type="primary", use_container_width=True)

            if submitted:
                users_db = load_users()
                if not uname or not pword:
                    st.error("Please fill in both fields.")
                elif auth_mode == "Login":
                    if uname in users_db and users_db[uname] == pword:
                        st.session_state.logged_in = True
                        st.session_state.username = uname
                        st.rerun()
                    else:
                        st.error("Invalid username or password.")
                elif auth_mode == "Sign Up":
                    if uname in users_db:
                        st.warning("Username already registered.")
                    else:
                        save_user(uname, pword)
                        st.session_state.logged_in = True
                        st.session_state.username = uname
                        st.rerun()

        st.info("💡 **Demo User:** `student` | Password: `hackathon123`")

# --- MAIN DASHBOARD SCREEN ---
def render_dashboard():
    st.sidebar.markdown(f"👤 Logged in as: **{st.session_state.username}**")
    if st.sidebar.button("Log out"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.session_state.study_set = None
        st.session_state.card_index = 0
        st.session_state.card_flipped = False
        st.session_state.celebrated = False
        st.rerun()

    st.sidebar.divider()

    # Revision History
    st.sidebar.subheader("🕒 Revision History")
    history_items = load_user_history(st.session_state.username)
    
    if history_items:
        options = {f"{h['timestamp']} - {h['title']}": h['data'] for h in history_items}
        selected_history = st.sidebar.selectbox("Load saved deck:", list(options.keys()), index=None, placeholder="Select past session...")
        
        if selected_history:
            if st.sidebar.button("Load This Deck"):
                st.session_state.study_set = options[selected_history]
                st.session_state.card_index = 0
                st.session_state.card_flipped = False
                st.session_state.celebrated = False
                st.rerun()
    else:
        st.sidebar.caption("No saved revision sets yet.")

    st.sidebar.divider()

    # Input Section
    st.sidebar.subheader("New Material Generator")
    input_mode = st.sidebar.radio("Input format:", ["Paste Text", "Upload PDF"])
    notes_text = ""

    if input_mode == "Paste Text":
        notes_text = st.sidebar.text_area("Paste lecture notes here:", height=180)
    else:
        uploaded_file = st.sidebar.file_uploader("Upload PDF note", type=["pdf"])
        if uploaded_file:
            reader = PdfReader(uploaded_file)
            notes_text = "\n".join([page.extract_text() or "" for page in reader.pages])

    if st.sidebar.button("Generate Material", type="primary"):
        if not notes_text.strip():
            st.sidebar.warning("Please paste some text or upload a PDF first!")
        else:
            with st.spinner("Generating flashcards and quiz..."):
                try:
                    res = generate_study_material(notes_text)
                    st.session_state.study_set = res.model_dump()
                    st.session_state.card_index = 0
                    st.session_state.card_flipped = False
                    st.session_state.celebrated = False
                    save_to_history(st.session_state.username, st.session_state.study_set)
                    st.rerun()
                except Exception as e:
                    st.sidebar.error(f"Error: {e}")

    # Main Area
    st.title("📚 Quick Revision Deck & Quiz Generator")
    data = st.session_state.study_set

    if data:
        st.info(f"**Topic Summary:** {data['summary']}")
        tab1, tab2, tab3 = st.tabs(["🗂️ Interactive Deck", "📝 Practice Quiz", "💾 Export"])

        # TAB 1: INTERACTIVE DECK
        with tab1:
            cards = data["flashcards"]
            total_cards = len(cards)
            curr_idx = st.session_state.card_index
            curr_card = cards[curr_idx]

            prog_col1, prog_col2 = st.columns([3, 1])
            with prog_col1:
                st.markdown(f"#### Card {curr_idx + 1} of {total_cards}")
            with prog_col2:
                st.progress((curr_idx + 1) / total_cards)

            side_label = "BACK (ANSWER / EXPLANATION)" if st.session_state.card_flipped else "FRONT (TERM / CONCEPT)"
            card_text = curr_card["back"] if st.session_state.card_flipped else curr_card["front"]

            st.markdown(f"""
            <div class="flashcard-box">
                <div class="flashcard-label">{side_label}</div>
                <div class="flashcard-content">{card_text}</div>
            </div>
            """, unsafe_allow_html=True)

            btn_prev, btn_flip, btn_next = st.columns([1, 1.5, 1])
            with btn_prev:
                if st.button("⬅️ Previous", use_container_width=True, disabled=(curr_idx == 0)):
                    st.session_state.card_index -= 1
                    st.session_state.card_flipped = False
                    st.rerun()

            with btn_flip:
                flip_label = "🔄 Flip to Front" if st.session_state.card_flipped else "🔄 Flip to Back"
                if st.button(flip_label, use_container_width=True, type="primary"):
                    st.session_state.card_flipped = not st.session_state.card_flipped
                    st.rerun()

            with btn_next:
                if st.button("Next ➡️", use_container_width=True, disabled=(curr_idx == total_cards - 1)):
                    st.session_state.card_index += 1
                    st.session_state.card_flipped = False
                    st.rerun()

            with st.expander("✏️ Edit This Card's Text"):
                new_front = st.text_input("Front Text", value=curr_card["front"], key=f"edit_f_{curr_idx}")
                new_back = st.text_area("Back Text", value=curr_card["back"], key=f"edit_b_{curr_idx}")
                if new_front != curr_card["front"] or new_back != curr_card["back"]:
                    curr_card["front"] = new_front
                    curr_card["back"] = new_back

        # TAB 2: GAMIFIED PRACTICE QUIZ WITH WEAK-SPOT DIAGNOSIS
        with tab2:
            st.subheader("🎯 Interactive Quiz & Mastery Tracker")
            quiz_list = data["quiz"]
            total_questions = len(quiz_list)

            # Calculate current user responses and score
            answered_count = 0
            correct_count = 0
            missed_questions = []

            for i, q in enumerate(quiz_list):
                user_choice = st.session_state.get(f"q_{i}")
                if user_choice is not None:
                    answered_count += 1
                    chosen_idx = q["options"].index(user_choice)
                    if chosen_idx == q["correct_index"]:
                        correct_count += 1
                    else:
                        missed_questions.append((i + 1, q))

            # Live Score Board
            score_col1, score_col2 = st.columns([2, 1])
            with score_col1:
                percentage = int((correct_count / total_questions) * 100) if total_questions > 0 else 0
                st.markdown(f"### Score: **{correct_count} / {total_questions}** ({percentage}% Mastery)")
                st.progress(correct_count / total_questions if total_questions > 0 else 0.0)
            
            with score_col2:
                if answered_count == total_questions and correct_count == total_questions:
                    st.success("🎉 Perfect Score!")
                    if not st.session_state.celebrated:
                        st.balloons()
                        st.session_state.celebrated = True
                elif answered_count > 0:
                    st.caption(f"Answered: {answered_count} of {total_questions}")

            # Weak Spot Diagnostic Box
            if missed_questions:
                with st.expander("🔍 **Weak Spot Diagnosis & Recommended Review**", expanded=True):
                    st.markdown("Here are the specific areas you should revisit in your revision deck:")
                    for q_num, q_item in missed_questions:
                        st.markdown(f"- **Question {q_num}:** Review _\"{q_item['question'][:65]}...\"_")
                        st.caption(f"  👉 Key takeaway: {q_item['explanation']}")

            st.divider()

            # Render Questions
            for i, q in enumerate(quiz_list):
                st.markdown(f"**Q{i+1}. {q['question']}**")
                selection = st.radio(
                    f"Options for Q{i+1}:",
                    q["options"],
                    key=f"q_{i}",
                    index=None,
                    label_visibility="collapsed"
                )

                if selection:
                    chosen_idx = q["options"].index(selection)
                    if chosen_idx == q["correct_index"]:
                        st.success(f"✅ **Correct!** {q['explanation']}")
                    else:
                        correct_answer = q["options"][q["correct_index"]]
                        st.error(f"❌ **Incorrect.** Correct answer: **{correct_answer}**\n\n_{q['explanation']}_")
                st.write("")

        # TAB 3: EXPORT
        with tab3:
            st.subheader("Export Formats")
            html_doc = create_printable_guide(data)
            st.download_button(
                label="📄 Download Printable Study Guide (Save as PDF)",
                data=html_doc,
                file_name="revision_guide.html",
                mime="text/html",
                type="primary",
                use_container_width=True
            )
            st.caption("💡 *Tip: Open this downloaded file in any browser and press **Ctrl + P** to save directly as a clean PDF.*")
            
            st.markdown("---")
            col_csv, col_json = st.columns(2)
            
            with col_csv:
                csv_buffer = io.StringIO()
                writer = csv.writer(csv_buffer)
                for card in data["flashcards"]:
                    writer.writerow([card["front"], card["back"]])
                    
                st.download_button(
                    label="🗂️ Download Flashcards (Anki CSV)",
                    data=csv_buffer.getvalue(),
                    file_name="flashcards_anki.csv",
                    mime="text/csv",
                    use_container_width=True
                )
            
            with col_json:
                st.download_button(
                    label="💾 Download Raw Data (JSON)",
                    data=json.dumps(data, indent=2),
                    file_name="study_material.json",
                    mime="application/json",
                    use_container_width=True
                )
    else:
        st.write("👈 Paste your lecture notes or load a past deck from the sidebar to begin.")

# --- CONTROLLER ---
if not st.session_state.logged_in:
    render_auth_page()
else:
    render_dashboard()