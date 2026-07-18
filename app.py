""" 
Skillzhub Intern Tracker
------------------------
Streamlit + SQLite/PostgreSQL app to track intern task assignments,
completion timestamps, and scoring (0-10) with auto grading:
    8-10 -> Excellent | 5-7 -> Good | 0-4 -> Fail

Features:
- Role-based login (Admin / Intern)
- Admin: Dashboard, Interns, Assign Task, Review & Score, All Records, Manage Users
- Intern: Submit Task (scoped to their own tasks)
"""

import streamlit as st
# from PIL import Image
import pandas as pd
import os
import uuid
from datetime import datetime, date
import database as db

st.set_page_config(
    page_title="Skillzhub Intern Tracker",
    page_icon="🎓",
    layout="wide",
)

db.init_db()

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ---------------------------------------------------------------------------
# PREMIUM SKILLZHUB DESIGN SYSTEM (CSS)
# ---------------------------------------------------------------------------
st.markdown("""
<style>
    /* Global Styles */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    /* Main Dashboard Layout */
    .main-title {
        font-size: 200px;
        font-weight: 800;
        color: #014b94;
        margin-bottom: 2px;
        letter-spacing: -0.5px;
    }
    .main-title span {
        color: #f37021;
    }
    .sub-title {
        color: #64748b;
        font-size: 1.05rem;
        margin-top: 0px;
        margin-bottom: 2rem;
    }
    
    /* Custom Metric Cards */
    .metric-container {
        display: flex;
        gap: 1rem;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 1.25rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        text-align: center;
        flex: 1;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05), 0 2px 4px -1px rgba(0,0,0,0.03);
        border-color: #cbd5e1;
    }
    
    /* Badges & Status */
    .grade-excellent { 
        color: #10b981; 
        font-weight: 700; 
        background-color: #ecfdf5; 
        padding: 4px 10px; 
        border-radius: 20px;
        border: 1px solid #a7f3d0;
        display: inline-block;
    }
    .grade-good { 
        color: #f59e0b; 
        font-weight: 700; 
        background-color: #fffbeb; 
        padding: 4px 10px; 
        border-radius: 20px;
        border: 1px solid #fde68a;
        display: inline-block;
    }
    .grade-fail { 
        color: #ef4444; 
        font-weight: 700; 
        background-color: #fef2f2; 
        padding: 4px 10px; 
        border-radius: 20px;
        border: 1px solid #fecaca;
        display: inline-block;
    }
    
    /* Login Design Theme */
    .login-container {
        background-color: #ffffff;
        max-width: 450px;
        margin: 2.5rem auto;
        padding: 2.5rem;
        border: 1px solid #e2e8f0;
        border-radius: 16px;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.05), 0 4px 6px -2px rgba(0, 0, 0, 0.02);
    }
    .login-logo-header {
        text-align: center;
        margin-bottom: 1.5rem;
    }
    .login-title {
        text-align: center;
        font-size: 30px;
        font-weight: 800;
        color: #014b94;
        margin-bottom: 0.25rem;
    }
    .login-title span {
        color: #f37021;
    }
    .login-subtitle {
        text-align: center;
        color: #64748b;
        font-size: 0.95rem;
        margin-bottom: 2rem;
    }
    
    /* Styling Streamlit Buttons globally to match brand color */
    div.stButton > button:first-child {
        background-color: #014b94;
        color: white;
        border-radius: 8px;
        border: none;
        font-weight: 600;
        transition: background-color 0.2s;
    }
    div.stButton > button:first-child:hover {
        background-color: #003366;
        color: white;
    }
</style>
""", unsafe_allow_html=True)


# ===========================================================================
# AUTHENTICATION HELPERS
# ===========================================================================
def login_user(username, password):
    user = db.verify_user(username, password)
    if user:
        st.session_state["authenticated"] = True
        st.session_state["user"] = user
        return True
    return False


def logout_user():
    st.session_state["authenticated"] = False
    st.session_state["user"] = None
    st.rerun()


def is_authenticated():
    return st.session_state.get("authenticated", False)


def current_user():
    return st.session_state.get("user")


def is_admin():
    user = current_user()
    return user and user["role"] == "admin"


# ---------------------------------------------------------------------------
# SESSION STATE INIT
# ---------------------------------------------------------------------------
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
    st.session_state["user"] = None


# ===========================================================================
# PAGE: LOGIN / SIGNUP (Styled with Brand Logo)
# ===========================================================================
if not is_authenticated():
    
    left, center, right = st.columns([3, 2, 3])
    with center:
        st.image("images/logo.png", width=1080)
    # st.markdown('<p class="login-title" style="font-size: 50px;">Skillz<span>hub</span></p>', unsafe_allow_html=True)
    
    # Styled Login/Signup Tabs
    login_tab, signup_tab = st.tabs(["🔐 Sign In", "📝 Sign Up (Intern)"])

    # --- LOGIN TAB ---
    with login_tab:
        
        st.markdown('<p class="login-title"><span>Intern </span>Tracker</p>', unsafe_allow_html=True)
        st.markdown('<p class="login-subtitle">Sign in to your dashboard</p>', unsafe_allow_html=True)

        with st.form("login_form"):
            username = st.text_input("Username", placeholder="Enter your username")
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            submitted = st.form_submit_button("Sign In", use_container_width=True)

            if submitted:
                if not username or not password:
                    st.error("Please enter both username and password.")
                elif login_user(username, password):
                    st.success("Login successful!")
                    st.rerun()
                else:
                    st.error("Invalid username or password.")

        st.markdown('</div>', unsafe_allow_html=True)

    # --- SIGNUP TAB (Intern self-registration) ---
    with signup_tab:
        
        st.markdown('<p class="login-title">📝 Intern Registration</p>', unsafe_allow_html=True)
        st.markdown('<p class="login-subtitle">Create your account to submit tasks</p>', unsafe_allow_html=True)

        with st.form("signup_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                full_name = st.text_input("Full Name *", placeholder="e.g. Ali Raza")
                email = st.text_input("Email *", placeholder="you@example.com")
                phone = st.text_input("Phone", placeholder="0300-1234567")
            with col2:
                department = st.selectbox(
                    "Department / Track",
                    ["Ebay", "Web Development", "Graphic Design", "Social Media Manager", "Video Editor", "Other"],
                )
                joining_date = st.date_input("Joining Date", value=date.today())
                signup_username = st.text_input("Login Username *", placeholder="Choose a username")
                signup_password = st.text_input("Login Password *", type="password", placeholder="Min 6 characters")
                confirm_password = st.text_input("Confirm Password *", type="password")

            submitted_signup = st.form_submit_button("Create Account & Login", use_container_width=True)

            if submitted_signup:
                errors = []
                if not full_name:
                    errors.append("Full Name is required.")
                if not email:
                    errors.append("Email is required.")
                if not signup_username:
                    errors.append("Username is required.")
                if not signup_password:
                    errors.append("Password is required.")
                elif len(signup_password) < 6:
                    errors.append("Password must be at least 6 characters.")
                elif signup_password != confirm_password:
                    errors.append("Passwords do not match.")

                if errors:
                    for e in errors:
                        st.error(e)
                else:
                    success, msg = db.signup_intern(
                        full_name, email, phone, department, str(joining_date),
                        signup_username, signup_password,
                    )
                    if success:
                        st.success(msg)
                        # Auto-login after signup
                        if login_user(signup_username, signup_password):
                            st.rerun()
                    else:
                        st.error(msg)

        st.markdown('</div>', unsafe_allow_html=True)

    st.stop()


# ===========================================================================
# LOGGED IN UI (Sidebar & Top Headers Custom Designed)
# ===========================================================================
user = current_user()
is_admin_user = is_admin()

# Brand Identity at top of sidebar
with st.sidebar:
    if is_admin_user:
        st.markdown(f"**👑 Admin Profile:** `{user['username']}`")
    else:
        intern_info = db.get_intern_by_id(user["intern_id"]) if user.get("intern_id") else None
        display_name = intern_info["name"] if intern_info else user["username"]
        st.markdown(f"**👤 Intern:** {display_name}")

    st.markdown("---")

# Navigation - role based
if is_admin_user:
    page = st.sidebar.radio(
        "Navigation Portal",
        ["📊 Dashboard", "👤 Interns", "📝 Assign Task", "📤 Submit Task (Intern)",
         "✅ Review & Score (Admin)", "📋 All Records", "👥 Manage Users"],
    )
else:
    page = st.sidebar.radio("Navigation Portal", ["📤 Submit Task (Intern)", "👤 My Profile"])

# Logout and Grading Legend on Sidebar
st.sidebar.markdown("---")
if st.sidebar.button("🚪 Logout", use_container_width=True):
    logout_user()

st.sidebar.markdown("---")
st.sidebar.markdown("<p style='font-size:0.85rem; font-weight:700; color:#64748b; margin-bottom:5px;'>GRADING LEGEND</p>", unsafe_allow_html=True)
st.sidebar.markdown(
    "- **8–10** → <span class='grade-excellent'>🟢 Excellent</span>\n"
    "- **5–7** → <span class='grade-good'>🟠 Good</span>\n"
    "- **0–4** → <span class='grade-fail'>🔴 Fail</span>",
    unsafe_allow_html=True
)

# Header Title Block — Centered
left, center, right = st.columns([3, 2, 3])
with center:
    st.image("images/logo.png", width=1080)
st.markdown('<p class="main-title" style="text-align: center; color: #014b94;">Skillz<span>hub</span> Intern Tracker</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-title" style="text-align: center;">Unified tracking interface for intern task assignments, submissions, and grading metrics</p>', unsafe_allow_html=True)


def grade_badge(grade):
    if grade == "Excellent":
        return f'<span class="grade-excellent">🟢 {grade}</span>'
    elif grade == "Good":
        return f'<span class="grade-good">🟠 {grade}</span>'
    elif grade == "Fail":
        return f'<span class="grade-fail">🔴 {grade}</span>'
    return "—"


# ===========================================================================
# PAGE: DASHBOARD (Admin only)
# ===========================================================================
if page == "📊 Dashboard":
    stats = db.get_stats()

    # Premium custom metric cards using html formatting
    st.markdown(f"""
    <div class="metric-container">
        <div class="metric-card">
            <p style="margin:0; font-size:0.9rem; color:#64748b; font-weight:600;">Total Interns</p>
            <p style="margin:5px 0 0 0; font-size:2rem; font-weight:800; color:#014b94;">{stats["total_interns"]}</p>
        </div>
        <div class="metric-card">
            <p style="margin:0; font-size:0.9rem; color:#64748b; font-weight:600;">Total Tasks</p>
            <p style="margin:5px 0 0 0; font-size:2rem; font-weight:800; color:#014b94;">{stats["total_tasks"]}</p>
        </div>
        <div class="metric-card">
            <p style="margin:0; font-size:0.9rem; color:#64748b; font-weight:600;">Pending</p>
            <p style="margin:5px 0 0 0; font-size:2rem; font-weight:800; color:#f37021;">{stats["pending_tasks"]}</p>
        </div>
        <div class="metric-card">
            <p style="margin:0; font-size:0.9rem; color:#64748b; font-weight:600;">Awaiting Review</p>
            <p style="margin:5px 0 0 0; font-size:2rem; font-weight:800; color:#f59e0b;">{stats["submitted_tasks"]}</p>
        </div>
        <div class="metric-card">
            <p style="margin:0; font-size:0.9rem; color:#64748b; font-weight:600;">Completed</p>
            <p style="margin:5px 0 0 0; font-size:2rem; font-weight:800; color:#10b981;">{stats["completed_tasks"]}</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Grade Distribution")
        gc = stats["grade_counts"]
        if gc:
            grade_df = pd.DataFrame(
                {"Grade": list(gc.keys()), "Count": list(gc.values())}
            )
            st.bar_chart(grade_df.set_index("Grade"), color="#014b94")
        else:
            st.info("No graded tasks yet.")

    with col2:
        st.subheader("Average Score")
        st.metric("Overall Average Performance", f"{stats['avg_score']} / 10")
        tasks = db.get_all_tasks()
        pending_deadlines = [
            t for t in tasks
            if t["status"] == "Pending" and t["deadline"]
        ]
        if pending_deadlines:
            st.subheader("⏰ Upcoming Deadlines")
            dl_df = pd.DataFrame(pending_deadlines)[["intern_name", "title", "deadline"]]
            dl_df.columns = ["Intern", "Task", "Deadline"]
            st.dataframe(dl_df.sort_values("Deadline"), use_container_width=True, hide_index=True)

    st.markdown("---")
    st.subheader("Recent Activity")
    tasks = db.get_all_tasks()
    if tasks:
        df = pd.DataFrame(tasks)[["intern_name", "title", "status", "completed_at", "score", "grade"]].head(10)
        df.columns = ["Intern", "Task", "Status", "Completed At", "Score", "Grade"]
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No tasks recorded yet. Add an intern and assign a task to get started.")


# ===========================================================================
# PAGE: INTERNS (Admin only)
# ===========================================================================
elif page == "👤 Interns":
    tab1, tab2 = st.tabs(["Add Intern", "View / Manage Interns"])

    with tab1:
        st.subheader("Add New Intern Profile")
        with st.form("add_intern_form", clear_on_submit=True):
            name = st.text_input("Full Name *")
            email = st.text_input("Email *")
            phone = st.text_input("Phone")
            department = st.selectbox(
                "Department / Track",
                ["Ebay", "Web Development", "Graphic Design", "Social Media Manager", "Video Editor", "Other"],
            )
            joining_date = st.date_input("Joining Date", value=date.today())
            submitted = st.form_submit_button("Add Intern", use_container_width=True)

            if submitted:
                if not name or not email:
                    st.error("Name and Email are required.")
                else:
                    try:
                        db.add_intern(name, email, phone, department, str(joining_date))
                        st.success(f"Intern '{name}' added successfully!")
                    except Exception as e:
                        st.error(f"Could not add intern: {e}")

    with tab2:
        st.subheader("All Interns — Performance Summary")

        score_summary = db.get_intern_score_summary()
        if score_summary:
            summary_data = []
            for s in score_summary:
                avg = s["avg_score"] if s["avg_score"] is not None else 0
                grade = db.get_grade(avg)
                summary_data.append({
                    "ID": s["id"],
                    "Name": s["name"],
                    "Email": s["email"],
                    "Department": s["department"],
                    "Total Tasks": s["total_tasks"],
                    "Completed": s["completed_tasks"],
                    "Avg Score": f"{avg}/10",
                    "Grade": grade,
                    "Excellent": s["excellent_count"],
                    "Good": s["good_count"],
                    "Fail": s["fail_count"],
                })

            df_scores = pd.DataFrame(summary_data)

            # Color-coded grade column
            def color_grade(val):
                if val == "Excellent":
                    return '🟢 Excellent'
                elif val == "Good":
                    return '🟠 Good'
                elif val == "Fail":
                    return '🔴 Fail'
                return '—'

            df_scores["Grade"] = df_scores["Grade"].apply(color_grade)

            st.dataframe(df_scores, use_container_width=True, hide_index=True)

            st.markdown("---")
            st.subheader("📊 Detailed Intern Performance")

            intern_selector = {f'{s["name"]} (ID {s["id"]})': s["id"] for s in score_summary}
            selected = st.selectbox("Select intern to view details", list(intern_selector.keys()))
            selected_id = intern_selector[selected]

            intern_tasks = db.get_tasks_by_intern(selected_id)
            if intern_tasks:
                tasks_data = []
                for t in intern_tasks:
                    tasks_data.append({
                        "Task #": t["id"],
                        "Title": t["title"],
                        "Status": t["status"],
                        "Score": f'{t["score"]}/10' if t["score"] is not None else "—",
                        "Grade": grade_badge(t["grade"]) if t["grade"] else "—",
                        "Submitted": str(t["submitted_at"])[:16] if t["submitted_at"] else "—",
                        "Completed": str(t["completed_at"])[:16] if t["completed_at"] else "—",
                    })

                df_tasks = pd.DataFrame(tasks_data)

                st.dataframe(
                    df_tasks,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Grade": st.column_config.TextColumn("Grade"),
                    },
                )
            else:
                st.info("No tasks found for this intern.")

            st.markdown("---")
            st.subheader("✏️ Edit Intern Information")
            intern_edit_map = {f'{i["name"]} (ID {i["id"]})': i["id"] for i in db.get_all_interns()}
            selected_edit = st.selectbox("Select intern to edit", list(intern_edit_map.keys()), key="edit_intern_select")
            edit_id = intern_edit_map[selected_edit]
            edit_info = db.get_intern_by_id(edit_id)
            if edit_info:
                with st.form("edit_intern_form"):
                    edit_name = st.text_input("Full Name *", value=edit_info["name"])
                    edit_email = st.text_input("Email *", value=edit_info["email"])
                    edit_phone = st.text_input("Phone", value=edit_info["phone"] or "")
                    edit_dept = st.selectbox(
                        "Department / Track",
                        ["Ebay", "Web Development", "Graphic Design", "Social Media Manager", "Video Editor", "Other"],
                        index=["Ebay", "Web Development", "Graphic Design", "Social Media Manager", "Video Editor", "Other"].index(edit_info["department"]) if edit_info["department"] in ["Ebay", "Web Development", "Graphic Design", "Social Media Manager", "Video Editor", "Other"] else 0,
                    )
                    try:
                        edit_default_date = datetime.strptime(edit_info["joining_date"][:10], "%Y-%m-%d").date() if edit_info["joining_date"] else date.today()
                    except (ValueError, TypeError):
                        edit_default_date = date.today()
                    edit_date = st.date_input("Joining Date", value=edit_default_date)
                    submitted_edit = st.form_submit_button("💾 Update Intern", use_container_width=True)
                    if submitted_edit:
                        if not edit_name or not edit_email:
                            st.error("Name and Email are required.")
                        else:
                            try:
                                db.update_intern(edit_id, edit_name, edit_email, edit_phone, edit_dept, str(edit_date))
                                st.success("Intern profile updated successfully!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Could not update intern: {e}")

            st.markdown("---")
            st.markdown("##### Remove an intern")
            names = {f'{i["name"]} (ID {i["id"]})': i["id"] for i in db.get_all_interns()}
            to_delete = st.selectbox("Select intern to remove (permanent)", list(names.keys()))
            if st.button("🗑️ Delete Intern"):
                db.delete_intern(names[to_delete])
                st.success("Intern removed.")
                st.rerun()
        else:
            st.info("No interns added yet.")


# ===========================================================================
# PAGE: ASSIGN TASK (Admin only)
# ===========================================================================
elif page == "📝 Assign Task":
    st.subheader("Assign a New Task / Assignment")
    interns = db.get_all_interns()

    if not interns:
        st.warning("Add at least one intern first from the 'Interns' page.")
    else:
        with st.form("assign_task_form", clear_on_submit=True):
            intern_map = {f'{i["name"]} ({i["department"]})': i["id"] for i in interns}
            intern_choice = st.selectbox("Select Intern", list(intern_map.keys()))
            title = st.text_input("Task Title *")
            description = st.text_area("Task Description / Instructions")
            deadline = st.date_input("Deadline", value=date.today())
            submitted = st.form_submit_button("Assign Task", use_container_width=True)

            if submitted:
                if not title:
                    st.error("Task title is required.")
                else:
                    db.assign_task(intern_map[intern_choice], title, description, str(deadline))
                    st.success(f"Task '{title}' assigned to {intern_choice}.")


# ===========================================================================
# PAGE: SUBMIT TASK (INTERN-FACING)
# ===========================================================================
elif page == "📤 Submit Task (Intern)":
    st.subheader("Submit Your Completed Task")
    st.caption("Select your task, upload the completed file, and submit for review.")

    if is_admin_user:
        interns = db.get_all_interns()
        if not interns:
            st.warning("No interns found. Add an intern first.")
            st.stop()
        intern_map = {i["name"]: i["id"] for i in interns}
        intern_choice = st.selectbox("Select Intern", list(intern_map.keys()))
        intern_id = intern_map[intern_choice]
    else:
        intern_id = user.get("intern_id")
        if not intern_id:
            st.error("Your intern account is not linked to an intern profile. Contact admin.")
            st.stop()
        intern_info = db.get_intern_by_id(intern_id)
        if intern_info:
            st.info(f"Logged in as: **{intern_info['name']}**")
        else:
            st.error("Your linked intern profile was not found.")
            st.stop()

    all_tasks = db.get_tasks_by_intern(intern_id)

    completed_tasks = [t for t in all_tasks if t["status"] == "Completed"]
    my_pending_tasks = [t for t in all_tasks if t["status"] == "Pending"]
    my_submitted_tasks = [t for t in all_tasks if t["status"] == "Submitted"]

    if completed_tasks:
        st.markdown("### ✅ Your Completed Tasks — Marks & Grades")
        completed_data = []
        for t in completed_tasks:
            completed_data.append({
                "Task #": t["id"],
                "Title": t["title"],
                "Score": f'{t["score"]}/10' if t["score"] is not None else "—",
                "Grade": grade_badge(t["grade"]) if t["grade"] else "—",
                "Completed On": str(t["completed_at"])[:16] if t["completed_at"] else "—",
            })
        df_completed = pd.DataFrame(completed_data)
        for idx, row in df_completed.iterrows():
            col1, col2, col3 = st.columns([1, 3, 3])
            col1.markdown(f"**#{row['Task #']}**")
            col2.markdown(f"**{row['Title']}**")
            col3.markdown(f"Score: **{row['Score']}** —  {row['Grade']}", unsafe_allow_html=True)
        st.markdown("---")

    if my_submitted_tasks:
        st.markdown("### ⏳ Submitted — Awaiting Review")
        for t in my_submitted_tasks:
            st.markdown(f"- **#{t['id']}** — {t['title']} (submitted {str(t['submitted_at'])[:16] if t['submitted_at'] else ''})")
        st.markdown("---")

    st.markdown("### 📤 Submit New Task")

    if not my_pending_tasks:
        st.info("You have no pending tasks to submit. 🎉")
    else:
        task_map = {f'#{t["id"]} - {t["title"]} (due {t["deadline"]})': t["id"] for t in my_pending_tasks}
        task_choice = st.selectbox("Select Pending Task", list(task_map.keys()))
        task_id = task_map[task_choice]
        selected = next(t for t in my_pending_tasks if t["id"] == task_id)

        st.markdown(f"**Instructions:** {selected['description'] or '—'}")

        uploaded_file = st.file_uploader(
            "Upload your file (PDF, DOCX, XLSX/XLS, ZIP, image, code file, etc.)",
            type=["pdf", "docx", "xlsx", "xls", "zip", "png", "jpg", "jpeg", "py", "txt", "csv"],
        )

        if st.button("📤 Submit Task", use_container_width=True):
            if uploaded_file is None:
                st.warning("Please upload a file first.")
            else:
                ext = os.path.splitext(uploaded_file.name)[1]
                unique_name = f"{intern_id}_{task_id}_{uuid.uuid4().hex[:8]}{ext}"
                save_path = os.path.join(UPLOAD_DIR, unique_name)
                with open(save_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())

                db.submit_task(task_id, uploaded_file.name, save_path)
                st.success(f"Submitted '{uploaded_file.name}' at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}. Waiting for admin review.")
                st.rerun()


# ===========================================================================
# PAGE: MY PROFILE (Intern-facing) — View & Update Info
# ===========================================================================
elif page == "👤 My Profile":
    st.subheader("👤 My Profile")
    st.caption("View and update your personal information.")

    intern_id = user.get("intern_id")
    if not intern_id:
        st.error("Your intern account is not linked to an intern profile. Contact admin.")
        st.stop()

    intern_info = db.get_intern_by_id(intern_id)
    if not intern_info:
        st.error("Intern profile not found.")
        st.stop()

    # Display current info
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**Name:** {intern_info['name']}")
        st.markdown(f"**Email:** {intern_info['email']}")
        st.markdown(f"**Phone:** {intern_info['phone'] or '—'}")
    with col2:
        st.markdown(f"**Department:** {intern_info['department']}")
        st.markdown(f"**Joining Date:** {intern_info['joining_date']}")

    st.markdown("---")
    st.markdown("### ✏️ Update Your Information")

    with st.form("update_intern_profile_form"):
        new_name = st.text_input("Full Name *", value=intern_info["name"])
        new_email = st.text_input("Email *", value=intern_info["email"])
        new_phone = st.text_input("Phone", value=intern_info["phone"] or "")
        new_department = st.selectbox(
            "Department / Track",
            ["Ebay", "Web Development", "Graphic Design", "Social Media Manager", "Video Editor", "Other"],
            index=["Ebay", "Web Development", "Graphic Design", "Social Media Manager", "Video Editor", "Other"].index(intern_info["department"]) if intern_info["department"] in ["Ebay", "Web Development", "Graphic Design", "Social Media Manager", "Video Editor", "Other"] else 0,
        )
        try:
            default_date = datetime.strptime(intern_info["joining_date"][:10], "%Y-%m-%d").date() if intern_info["joining_date"] else date.today()
        except (ValueError, TypeError):
            default_date = date.today()
        new_joining_date = st.date_input("Joining Date", value=default_date)
        submitted = st.form_submit_button("💾 Update Profile", use_container_width=True)

        if submitted:
            if not new_name or not new_email:
                st.error("Name and Email are required.")
            else:
                try:
                    db.update_intern(intern_id, new_name, new_email, new_phone, new_department, str(new_joining_date))
                    st.success("Profile updated successfully!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Could not update profile: {e}")


# ===========================================================================
# PAGE: REVIEW & SCORE (ADMIN-FACING)
# ===========================================================================
elif page == "✅ Review & Score (Admin)":
    st.subheader("Review Submitted Work & Give Score")

    departments = ["All Departments", "Ebay", "Web Development", "Graphic Design", "Social Media Manager", "Video Editor", "Other"]
    selected_dept_review = st.selectbox("Filter by Department", departments, key="review_dept_filter")

    submitted = db.get_tasks_by_status("Submitted", department=selected_dept_review)

    if not submitted:
        st.info("No submissions waiting for review.")
    else:
        task_map = {}
        for t in submitted:
            submitted_str = str(t["submitted_at"])[:16] if t["submitted_at"] else ""
            task_map[f'#{t["id"]} - {t["title"]} ({t["intern_name"]}) - submitted {submitted_str}'] = t["id"]

        choice = st.selectbox("Select Submission", list(task_map.keys()))
        task_id = task_map[choice]
        selected_task = next(t for t in submitted if t["id"] == task_id)

        assigned_str = str(selected_task["assigned_date"])[:16] if selected_task["assigned_date"] else ""
        submitted_str = str(selected_task["submitted_at"])[:16] if selected_task["submitted_at"] else ""
        st.markdown(f"**Description:** {selected_task['description'] or '—'}")
        st.markdown(f"**Assigned:** {assigned_str}  |  **Deadline:** {selected_task['deadline']}  |  **Submitted:** {submitted_str}")

        if selected_task["file_path"] and os.path.exists(selected_task["file_path"]):
            with open(selected_task["file_path"], "rb") as f:
                st.download_button(
                    f"⬇️ Download submitted file ({selected_task['file_name']})",
                    f,
                    file_name=selected_task["file_name"],
                )
        else:
            st.warning("No file found for this submission.")

        score = st.slider("Score (0 = worst, 10 = best)", 0, 10, 5)
        grade_preview = db.get_grade(score)
        st.markdown(f"Grade preview: {grade_badge(grade_preview)}", unsafe_allow_html=True)

        if st.button("✅ Confirm Score & Complete", use_container_width=True):
            db.complete_task(task_id, score)
            st.success(f"Task completed with score {score}/10 ({grade_preview}).")
            st.rerun()


# ===========================================================================
# PAGE: ALL RECORDS (Admin only)
# ===========================================================================
elif page == "📋 All Records":
    st.subheader("All Task Records")

    departments = ["All Departments", "Ebay", "Web Development", "Graphic Design", "Social Media Manager", "Video Editor", "Other"]
    selected_dept_records = st.selectbox("Filter by Department", departments, key="records_dept_filter")

    tasks = db.get_all_tasks_by_department(department=selected_dept_records)
    if not tasks:
        st.info("No records yet.")
    else:
        df = pd.DataFrame(tasks)

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            intern_options = sorted(df["intern_name"].unique())
            intern_filter = st.multiselect("Filter by Intern Name", intern_options)
        with col2:
            intern_id_options = sorted(df["intern_id"].unique())
            intern_id_filter = st.multiselect("Filter by Intern ID", intern_id_options)
        with col3:
            status_filter = st.multiselect("Filter by Status", sorted(df["status"].unique()))
        with col4:
            grade_filter = st.multiselect("Filter by Grade", [g for g in df["grade"].dropna().unique()])

        filtered = df.copy()
        if intern_filter:
            filtered = filtered[filtered["intern_name"].isin(intern_filter)]
        if intern_id_filter:
            filtered = filtered[filtered["intern_id"].isin(intern_id_filter)]
        if status_filter:
            filtered = filtered[filtered["status"].isin(status_filter)]
        if grade_filter:
            filtered = filtered[filtered["grade"].isin(grade_filter)]

        st.markdown(f"**Showing {len(filtered)} record(s)**")

        for idx, row in filtered.iterrows():
            with st.container():
                c1, c2, c3, c4, c5 = st.columns([1, 2, 1.5, 1, 1.5])
                c1.markdown(f"**#{row['id']}**")
                c2.markdown(f"{row['intern_name']} (ID: {row['intern_id']})")
                c3.markdown(f"**{row['title']}**")
                c4.markdown(f"*{row['status']}*")
                grade_display = grade_badge(row['grade']) if row['grade'] else "—"
                c5.markdown(grade_display, unsafe_allow_html=True)

                file_path = row.get("file_path")
                file_name = row.get("file_name")

                # Show submitted file download button
                if file_name and isinstance(file_name, str) and file_name.strip():
                    file_bytes = None

                    # Try the stored absolute path first
                    if isinstance(file_path, str) and file_path and os.path.exists(file_path):
                        with open(file_path, "rb") as f:
                            file_bytes = f.read()
                    else:
                        # Search in uploads directory for any file matching this task
                        for fname in os.listdir(UPLOAD_DIR):
                            if str(row["id"]) in fname or (isinstance(file_path, str) and os.path.basename(file_path) and fname == os.path.basename(file_path)):
                                alt_path = os.path.join(UPLOAD_DIR, fname)
                                with open(alt_path, "rb") as f:
                                    file_bytes = f.read()
                                break

                    if file_bytes:
                        st.download_button(
                            f"⬇️ {file_name}",
                            file_bytes,
                            file_name=file_name,
                            key=f"dl_{row['id']}",
                        )
                    else:
                        st.markdown(f"📄 **Submitted File:** `{file_name}`")

                score_val = row.get("score")
                submitted_val = row.get("submitted_at")
                completed_val = row.get("completed_at")
                submitted_display = str(submitted_val)[:16] if submitted_val else "—"
                completed_display = str(completed_val)[:16] if completed_val else "—"
                info_parts = []
                if submitted_val:
                    info_parts.append(f"Submitted: {submitted_display}")
                if score_val is not None:
                    info_parts.append(f"Score: **{score_val}/10**")
                if completed_val:
                    info_parts.append(f"Completed: {completed_display}")
                if info_parts:
                    st.markdown(" | ".join(info_parts))

                st.markdown("---")

        with st.expander("📊 View as Table"):
            display_df = filtered[[
                "id", "intern_name", "intern_id", "title", "assigned_date", "deadline",
                "status", "file_name", "submitted_at", "completed_at", "score", "grade"
            ]].rename(columns={
                "id": "ID", "intern_name": "Intern", "intern_id": "Intern ID", "title": "Task",
                "assigned_date": "Assigned On", "deadline": "Deadline",
                "status": "Status", "file_name": "Submitted File",
                "submitted_at": "Submitted At", "completed_at": "Scored At",
                "score": "Score", "grade": "Grade",
            })

            st.dataframe(display_df, use_container_width=True, hide_index=True)

            csv = display_df.to_csv(index=False).encode("utf-8")
            st.download_button("⬇️ Download as CSV", csv, "skillzhub_records.csv", "text/csv")


# ===========================================================================
# PAGE: MANAGE USERS (Admin only)
# ===========================================================================
elif page == "👥 Manage Users":
    st.subheader("Manage User Accounts")
    st.caption("Create login credentials for interns so they can sign in and submit tasks.")

    tab1, tab2, tab3 = st.tabs(["Create Intern Account", "🔑 Change Password (Admin)", "All Users"])

    with tab1:
        st.subheader("Create Intern Login")

        interns = db.get_all_interns()
        if not interns:
            st.warning("No interns available. Add an intern first on the 'Interns' page.")
        else:
            existing_users = db.get_all_users()
            existing_intern_ids = {u["intern_id"] for u in existing_users if u["intern_id"]}

            available_interns = [i for i in interns if i["id"] not in existing_intern_ids]

            if not available_interns:
                st.info("All interns already have user accounts.")
            else:
                intern_map = {f'{i["name"]} ({i["email"]})': i["id"] for i in available_interns}
                with st.form("create_user_form", clear_on_submit=True):
                    selected_intern = st.selectbox("Select Intern", list(intern_map.keys()))
                    new_username = st.text_input("Login Username *", placeholder="e.g. ali.raza")
                    new_password = st.text_input("Login Password *", type="password", placeholder="Min 6 characters")
                    confirm_password = st.text_input("Confirm Password *", type="password")
                    submitted = st.form_submit_button("Create Account", use_container_width=True)

                    if submitted:
                        if not new_username or not new_password:
                            st.error("Username and password are required.")
                        elif len(new_password) < 6:
                            st.error("Password must be at least 6 characters.")
                        elif new_password != confirm_password:
                            st.error("Passwords do not match.")
                        else:
                            success = db.create_intern_user(intern_map[selected_intern], new_username, new_password)
                            if success:
                                st.success(f"Account created for '{selected_intern}' with username '{new_username}'!")
                                st.rerun()
                            else:
                                st.error(f"Username '{new_username}' is already taken. Please choose another.")

    with tab2:
        st.subheader("🔑 Change Admin Password")
        st.caption("Verify your current credentials to set a new password.")

        with st.form("change_password_form", clear_on_submit=True):
            col_a, col_b = st.columns(2)
            with col_a:
                curr_user = st.text_input("Current Username *", placeholder="Enter your current username")
                curr_pass = st.text_input("Current Password *", type="password", placeholder="Enter your current password")
            with col_b:
                new_pass = st.text_input("New Password *", type="password", placeholder="Min 6 characters")
                confirm_new_pass = st.text_input("Confirm New Password *", type="password")

            submitted_pw = st.form_submit_button("Change Password", use_container_width=True)

            if submitted_pw:
                if not curr_user or not curr_pass:
                    st.error("Please enter your current username and password.")
                elif not new_pass:
                    st.error("Please enter a new password.")
                elif len(new_pass) < 6:
                    st.error("New password must be at least 6 characters.")
                elif new_pass != confirm_new_pass:
                    st.error("New passwords do not match.")
                else:
                    success, msg = db.change_admin_password(curr_user, curr_pass, new_pass)
                    if success:
                        st.success(msg)
                        st.balloons()
                    else:
                        st.error(msg)

        st.markdown("---")

    with tab3:
        st.subheader("All User Accounts")

        users = db.get_all_users()
        if not users:
            st.info("No user accounts yet.")
        else:
            df = pd.DataFrame(users)
            df.columns = ["ID", "Username", "Role", "Intern ID", "Intern Name"]
            df["Role"] = df["Role"].apply(lambda r: "👑 Admin" if r == "admin" else "👤 Intern")
            st.dataframe(df, use_container_width=True, hide_index=True)

            st.markdown("---")
            st.markdown("##### Default Credentials")
            st.info("**Admin:** username = `admin` | password = `admin` (or custom configuration)")