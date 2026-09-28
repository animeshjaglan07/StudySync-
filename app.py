import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import math

# ==========================================
# PAGE CONFIGURATION & CUSTOM STYLING
# ==========================================
st.set_page_config(
    page_title="StudySync – AI Personalized Study Planner",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Soft Purple/Blue Theme & Clean Student-Friendly UI
st.markdown("""
    <style>
    :root {
        --primary-color: #6C5CE7;
        --secondary-color: #a29bfe;
        --bg-light: #F8F9FA;
        --card-bg: #FFFFFF;
        --text-dark: #2D3436;
    }
    
    .main {
        background-color: var(--bg-light);
    }
    
    /* Card Styles */
    .stCard {
        background-color: #FFFFFF;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 4px 12px rgba(108, 92, 231, 0.08);
        border: 1px solid #E2E8F0;
        margin-bottom: 15px;
    }
    
    /* Badges */
    .badge-high {
        background-color: #FFE5E5;
        color: #D63031;
        padding: 4px 10px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.85rem;
    }
    .badge-medium {
        background-color: #FFF4E5;
        color: #E17055;
        padding: 4px 10px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.85rem;
    }
    .badge-low {
        background-color: #E8F8F5;
        color: #00B894;
        padding: 4px 10px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.85rem;
    }
    
    /* Landing Banner */
    .hero-banner {
        background: linear-gradient(135deg, #6C5CE7 0%, #a29bfe 100%);
        color: white;
        padding: 30px;
        border-radius: 16px;
        margin-bottom: 25px;
        text-align: center;
    }
    .hero-banner h1 {
        color: white !important;
        margin-bottom: 10px;
    }
    </style>
""", unsafe_allow_html=True)


# ==========================================
# INITIALIZE SAMPLE SESSION DATA
# ==========================================
if "tasks" not in st.session_state:
    st.session_state.tasks = [
        {
            "id": 1,
            "subject": "Mathematics",
            "topic": "Differentiation & Integration",
            "due_date": date.today() + timedelta(days=2),
            "type": "Exam",
            "difficulty": 5,  # 1-5 scale
            "prep_pct": 30,
            "est_hours": 3.0,
            "remaining_hours": 2.1,
            "status": "In Progress"
        },
        {
            "id": 2,
            "subject": "Economics",
            "topic": "Theory of Demand & Supply",
            "due_date": date.today() + timedelta(days=5),
            "type": "Assignment",
            "difficulty": 3,
            "prep_pct": 60,
            "est_hours": 2.0,
            "remaining_hours": 0.8,
            "status": "In Progress"
        },
        {
            "id": 3,
            "subject": "Accounts",
            "topic": "Journal Practice & Balance Sheet",
            "due_date": date.today() + timedelta(days=8),
            "type": "Project",
            "difficulty": 2,
            "prep_pct": 10,
            "est_hours": 4.0,
            "remaining_hours": 3.6,
            "status": "Not Started"
        },
        {
            "id": 4,
            "subject": "Physics",
            "topic": "Electromagnetic Induction",
            "due_date": date.today() + timedelta(days=1),
            "type": "Exam",
            "difficulty": 4,
            "prep_pct": 20,
            "est_hours": 2.5,
            "remaining_hours": 2.0,
            "status": "Not Started"
        }
    ]

if "daily_study_hours" not in st.session_state:
    st.session_state.daily_study_hours = 3.5

if "start_time" not in st.session_state:
    st.session_state.start_time = datetime.strptime("17:00", "%H:%M").time()


# ==========================================
# AI PRIORITY ENGINE & ALGORITHMS
# ==========================================
def calculate_ai_priority(task):
    """
    Calculates a dynamic priority score based on:
    - Urgency (days until deadline)
    - Preparation Deficit (100 - current prep %)
    - Difficulty level (1-5)
    - Remaining workload
    """
    days_left = (task["due_date"] - date.today()).days
    days_left = max(days_left, 0.5)  # Avoid division by zero
    
    prep_deficit = (100 - task["prep_pct"]) / 100.0
    difficulty_weight = task["difficulty"] / 5.0
    remaining_work_weight = min(task["remaining_hours"] / 5.0, 1.0)
    
    # Priority Formula
    urgency_score = (1 / days_left) * 40
    deficit_score = prep_deficit * 30
    difficulty_score = difficulty_weight * 20
    workload_score = remaining_work_weight * 10
    
    total_score = urgency_score + deficit_score + difficulty_score + workload_score
    
    if total_score >= 45:
        category = "High Priority"
        tag = "🔴 High"
        badge_class = "badge-high"
    elif total_score >= 25:
        category = "Medium Priority"
        tag = "🟡 Medium"
        badge_class = "badge-medium"
    else:
        category = "Low Priority"
        tag = "🟢 Low"
        badge_class = "badge-low"
        
    reason = f"Due in {int(days_left) if days_left >= 1 else 'less than 1'} day(s) | {task['prep_pct']}% prepared | Diff: {task['difficulty']}/5"
    
    return total_score, tag, category, badge_class, reason


def generate_daily_schedule(tasks, available_hours, start_time):
    """
    Generates a structured daily timetable with break intervals.
    """
    active_tasks = [t for t in tasks if t["status"] != "Completed" and t["remaining_hours"] > 0]
    
    # Sort tasks by AI priority score
    for t in active_tasks:
        score, tag, cat, badge, reason = calculate_ai_priority(t)
        t["priority_score"] = score
        t["priority_tag"] = tag

    sorted_tasks = sorted(active_tasks, key=lambda x: x["priority_score"], reverse=True)
    
    schedule = []
    current_dt = datetime.combine(date.today(), start_time)
    allocated_time = 0.0
    max_minutes = available_hours * 60
    
    session_length = 45  # 45-minute study sessions
    break_length = 15    # 15-minute breaks
    
    for task in sorted_tasks:
        task_rem_minutes = task["remaining_hours"] * 60
        
        while task_rem_minutes > 0 and allocated_time < max_minutes:
            study_chunk = min(session_length, task_rem_minutes, max_minutes - allocated_time)
            if study_chunk <= 0:
                break
                
            end_dt = current_dt + timedelta(minutes=study_chunk)
            schedule.append({
                "type": "Study",
                "task_id": task["id"],
                "subject": task["subject"],
                "topic": task["topic"],
                "start": current_dt.strftime("%I:%M %p"),
                "end": end_dt.strftime("%I:%M %p"),
                "duration_mins": int(study_chunk),
                "priority": task["priority_tag"]
            })
            
            allocated_time += study_chunk
            current_dt = end_dt
            task_rem_minutes -= study_chunk
            
            # Add break if time permits
            if allocated_time + 10 <= max_minutes:
                break_duration = min(break_length, max_minutes - allocated_time)
                break_end = current_dt + timedelta(minutes=break_duration)
                schedule.append({
                    "type": "Break",
                    "subject": "☕ Break Time",
                    "topic": "Rest & Refresh",
                    "start": current_dt.strftime("%I:%M %p"),
                    "end": break_end.strftime("%I:%M %p"),
                    "duration_mins": int(break_duration),
                    "priority": ""
                })
                allocated_time += break_duration
                current_dt = break_end
                
    return schedule


# ==========================================
# SIDEBAR NAVIGATION
# ==========================================
st.sidebar.title("📚 StudySync")
st.sidebar.caption("AI Personalized Study Planner")

page = st.sidebar.radio(
    "Navigation",
    ["Home", "Dashboard", "Add Task", "My Study Plan", "Progress", "Upcoming Deadlines", "Settings"]
)

st.sidebar.markdown("---")
st.sidebar.subheader("⚙️ Quick Config")
st.session_state.daily_study_hours = st.sidebar.number_input(
    "Available Hours Today:", min_value=0.5, max_value=12.0, value=st.session_state.daily_study_hours, step=0.5
)


# ==========================================
# PAGE 1: HOME / LANDING
# ==========================================
if page == "Home":
    st.markdown("""
        <div class="hero-banner">
            <h1>Welcome to StudySync</h1>
            <p style="font-size: 1.2rem;">
                StudySync turns your deadlines, workload and available time into a personalized study plan — and adapts when your plans change.
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.subheader("🎯 Smart Prioritization")
        st.write("Calculates study priorities using deadlines, difficulty level, and current preparation deficit.")
    with col2:
        st.subheader("📅 Adaptive Timetable")
        st.write("Generates realistic, break-included study schedules tailored to your available hours for the day.")
    with col3:
        st.subheader("🔄 Dynamic Rescheduling")
        st.write("Fell behind today? One click automatically redistributes unfinished tasks into your future schedule.")

    st.markdown("---")
    st.info("👈 Select **Dashboard** or **My Study Plan** from the sidebar to start organizing your study session!")


# ==========================================
# PAGE 2: DASHBOARD
# ==========================================
elif page == "Dashboard":
    st.title("📌 Student Dashboard")
    st.caption(f"Today's Overview | Available Study Time: {st.session_state.daily_study_hours} Hours")
    
    # Core Metrics Top Row
    active_tasks = [t for t in st.session_state.tasks if t["status"] != "Completed"]
    completed_tasks = [t for t in st.session_state.tasks if t["status"] == "Completed"]
    high_priority_count = sum(1 for t in active_tasks if calculate_ai_priority(t)[2] == "High Priority")
    
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Active Tasks", len(active_tasks))
    m2.metric("High Priority Tasks", high_priority_count)
    m3.metric("Completed Tasks", len(completed_tasks))
    m4.metric("Study Time Available", f"{st.session_state.daily_study_hours} hrs")

    st.markdown("---")
    
    col_left, col_right = st.columns([2, 1])
    
    with col_left:
        st.subheader("🎯 Today's AI Priority Workload")
        if not active_tasks:
            st.success("🎉 Great job! You have no active tasks remaining.")
        else:
            for task in sorted(active_tasks, key=lambda x: calculate_ai_priority(x)[0], reverse=True):
                score, tag, cat, badge_cls, reason = calculate_ai_priority(task)
                with st.container():
                    st.markdown(f"""
                        <div class="stCard">
                            <span class="{badge_cls}">{tag}</span>
                            <h3 style="margin: 5px 0;">{task['subject']}: {task['topic']}</h3>
                            <p style="color: #636E72; margin-bottom: 5px;"><b>Reason:</b> {reason}</p>
                            <p><b>Type:</b> {task['type']} | <b>Deadline:</b> {task['due_date']} | <b>Prep Level:</b> {task['prep_pct']}%</p>
                        </div>
                    """, unsafe_allow_html=True)

    with col_right:
        st.subheader("💡 AI Study Insights")
        # Generate Smart Suggestions
        suggestions = []
        for t in active_tasks:
            days = (t["due_date"] - date.today()).days
            if days <= 2 and t["prep_pct"] < 40:
                suggestions.append(f"⚠️ **{t['subject']}** exam/deadline is approaching ({days} days) and preparation is low ({t['prep_pct']}%). Prioritize this today.")
            if t["remaining_hours"] > 3.0:
                suggestions.append(f"📌 **{t['subject']} - {t['topic']}** has a large remaining workload ({t['remaining_hours']} hrs). Split it into smaller 45-min sessions.")
                
        if not suggestions:
            suggestions.append("✅ Your workload is balanced! Follow your generated schedule for optimal steady progress.")
            
        for sugg in suggestions:
            st.warning(sugg)


# ==========================================
# PAGE 3: ADD ACADEMIC TASKS
# ==========================================
elif page == "Add Task":
    st.title("➕ Add Academic Task")
    st.caption("Enter task details to let the AI evaluate its priority and fit it into your plan.")
    
    with st.form("add_task_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            subject = st.text_input("Subject Name", placeholder="e.g., Mathematics, History")
            topic = st.text_input("Chapter / Topic", placeholder="e.g., Integration, French Revolution")
            task_type = st.selectbox("Task Type", ["Exam", "Assignment", "Project", "General Study"])
            difficulty = st.slider("Difficulty Level (1 = Easy, 5 = Very Hard)", 1, 5, 3)
            
        with col2:
            due_date = st.date_input("Exam Date / Deadline", value=date.today() + timedelta(days=3))
            prep_pct = st.slider("Current Preparation (%)", 0, 100, 20)
            est_hours = st.number_input("Estimated Total Hours Required", min_value=0.5, max_value=20.0, value=2.0, step=0.5)

        submit = st.form_submit_button("Save Task to StudySync")
        
        if submit:
            if not subject or not topic:
                st.error("Please fill in both the Subject and Topic fields.")
            else:
                new_id = max([t["id"] for t in st.session_state.tasks], default=0) + 1
                rem_hours = round(est_hours * (1 - prep_pct / 100.0), 1)
                new_task = {
                    "id": new_id,
                    "subject": subject,
                    "topic": topic,
                    "due_date": due_date,
                    "type": task_type,
                    "difficulty": difficulty,
                    "prep_pct": prep_pct,
                    "est_hours": est_hours,
                    "remaining_hours": rem_hours,
                    "status": "Not Started"
                }
                st.session_state.tasks.append(new_task)
                st.success(f"Successfully added task: **{subject} - {topic}**!")


# ==========================================
# PAGE 4: MY STUDY PLAN & ADAPTIVE PLANNING
# ==========================================
elif page == "My Study Plan":
    st.title("📅 Personalized Daily Schedule")
    st.caption(f"Schedule calculated from your available time ({st.session_state.daily_study_hours} hrs) starting at 5:00 PM.")
    
    # Adaptive Trigger Section
    with st.expander("🔄 Adaptive Rescheduler (Fell behind or missed a task?)", expanded=False):
        st.write("Select a task you couldn't finish today. The AI will adjust its workload and push remaining hours forward.")
        active_task_options = {f"{t['subject']} - {t['topic']}": t["id"] for t in st.session_state.tasks if t["status"] != "Completed"}
        
        if active_task_options:
            selected_task_label = st.selectbox("Select Unfinished Task:", list(active_task_options.keys()))
            if st.button("Adapt My Schedule"):
                selected_id = active_task_options[selected_task_label]
                for t in st.session_state.tasks:
                    if t["id"] == selected_id:
                        # Extend remaining hours slightly & defer deadline if too urgent
                        t["remaining_hours"] += 1.0
                        t["prep_pct"] = max(0, t["prep_pct"] - 10)
                        st.warning(f"Rescheduled **{t['subject']}**. Added remaining buffer and recalculated priorities.")
                st.rerun()
        else:
            st.info("No active tasks to reschedule.")

    st.markdown("---")
    
    # Generate Daily Schedule
    schedule = generate_daily_schedule(
        st.session_state.tasks,
        st.session_state.daily_study_hours,
        st.session_state.start_time
    )
    
    if not schedule:
        st.info("No study sessions scheduled for today. Either all tasks are completed or available study time is set to 0.")
    else:
        for item in schedule:
            if item["type"] == "Break":
                st.markdown(f"**⏳ {item['start']} – {item['end']}** &nbsp;|&nbsp; ☕ *{item['subject']}* ({item['duration_mins']} mins)")
            else:
                st.markdown(f"""
                <div style="background-color: white; border-left: 5px solid #6C5CE7; padding: 12px 20px; border-radius: 8px; margin-bottom: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
                    <b>🕒 {item['start']} – {item['end']}</b> ({item['duration_mins']} mins) <br>
                    <span style="font-size: 1.1rem; color: #2D3436;"><b>{item['subject']}</b>: {item['topic']}</span>
                    <span style="float: right;">{item['priority']}</span>
                </div>
                """, unsafe_allow_html=True)


# ==========================================
# PAGE 5: PROGRESS TRACKING
# ==========================================
elif page == "Progress":
    st.title("📊 Progress Tracking")
    st.caption("Update your progress or mark tasks as completed.")
    
    for task in st.session_state.tasks:
        with st.container():
            col1, col2, col3 = st.columns([3, 2, 2])
            with col1:
                st.markdown(f"### {task['subject']}: {task['topic']}")
                st.caption(f"Deadline: {task['due_date']} | Status: **{task['status']}**")
            with col2:
                new_prep = st.slider(
                    f"Prep Level (%)",
                    0, 100, int(task["prep_pct"]),
                    key=f"prep_{task['id']}"
                )
                if new_prep != task["prep_pct"]:
                    task["prep_pct"] = new_prep
                    task["remaining_hours"] = round(task["est_hours"] * (1 - new_prep / 100.0), 1)
                    if new_prep == 100:
                        task["status"] = "Completed"
                        task["remaining_hours"] = 0.0
                    elif new_prep > 0:
                        task["status"] = "In Progress"
                    st.rerun()
            with col3:
                new_status = st.selectbox(
                    "Update Status",
                    ["Not Started", "In Progress", "Completed"],
                    index=["Not Started", "In Progress", "Completed"].index(task["status"]),
                    key=f"status_{task['id']}"
                )
                if new_status != task["status"]:
                    task["status"] = new_status
                    if new_status == "Completed":
                        task["prep_pct"] = 100
                        task["remaining_hours"] = 0.0
                    st.rerun()
        st.markdown("---")


# ==========================================
# PAGE 6: UPCOMING DEADLINES
# ==========================================
elif page == "Upcoming Deadlines":
    st.title("⏰ Upcoming Tests & Deadlines")
    st.caption("Tasks sorted by upcoming target dates.")
    
    sorted_deadlines = sorted(st.session_state.tasks, key=lambda x: x["due_date"])
    
    data = []
    for t in sorted_deadlines:
        days_remaining = (t["due_date"] - date.today()).days
        data.append({
            "Deadline Date": t["due_date"].strftime("%Y-%m-%d"),
            "Days Remaining": f"{days_remaining} days" if days_remaining >= 0 else "Overdue",
            "Subject": t["subject"],
            "Topic / Chapter": t["topic"],
            "Type": t["type"],
            "Status": t["status"]
        })
        
    df = pd.DataFrame(data)
    st.dataframe(df, use_container_width=True)


# ==========================================
# PAGE 7: SETTINGS
# ==========================================
elif page == "Settings":
    st.title("⚙️ Planner Settings")
    
    st.subheader("Daily Preferences")
    start_time_input = st.time_input("Preferred Daily Study Start Time", value=st.session_state.start_time)
    if start_time_input != st.session_state.start_time:
        st.session_state.start_time = start_time_input
        st.success("Start time updated!")
        
    st.markdown("---")
    st.subheader("Reset Sample Data")
    if st.button("Reset All Data to Sample Default"):
        st.session_state.clear()
        st.rerun()
