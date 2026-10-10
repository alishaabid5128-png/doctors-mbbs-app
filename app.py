
from __future__ import annotations

import json
from json import JSONDecodeError
from datetime import date
from pathlib import Path

import streamlit as st


# --------------------------------------------------
# APP CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="MedCore — Clinical OS",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded",
)

DATA_FILE = Path("doctors_data.json")


# --------------------------------------------------
# STYLING
# --------------------------------------------------

st.markdown(
    """
    <style>
        #MainMenu, footer, header {
            visibility: hidden;
        }

        .block-container {
            max-width: 1400px;
            padding-top: 2rem;
            padding-bottom: 3rem;
        }

        [data-testid="stMetric"] {
            border: 1px solid rgba(128, 128, 128, 0.18);
            border-radius: 14px;
            padding: 14px;
        }

        .app-subtitle {
            color: #6b7280;
            margin-top: -0.5rem;
            margin-bottom: 1.5rem;
        }

        .section-label {
            font-size: 0.78rem;
            font-weight: 700;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            color: #6b7280;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# --------------------------------------------------
# DATA MANAGEMENT
# --------------------------------------------------

def default_data() -> dict:
    return {
        "profile": {
            "name": "",
            "mbbs_year": 1,
            "daily_target": 4.0,
        },
        "subjects": {},
        "exams": [],
        "study_sessions": [],
        "schedule": [],
    }


def load_data() -> dict:
    if not DATA_FILE.exists():
        return default_data()

    try:
        with DATA_FILE.open("r", encoding="utf-8") as file:
            saved_data = json.load(file)

        if not isinstance(saved_data, dict):
            return default_data()

    except (OSError, JSONDecodeError):
        return default_data()

    base = default_data()

    for key, value in base.items():
        saved_data.setdefault(key, value)

    if not isinstance(saved_data.get("profile"), dict):
        saved_data["profile"] = {}

    for key, value in base["profile"].items():
        saved_data["profile"].setdefault(key, value)

    if not isinstance(saved_data.get("subjects"), dict):
        saved_data["subjects"] = {}

    for key in ("exams", "study_sessions", "schedule"):
        if not isinstance(saved_data.get(key), list):
            saved_data[key] = []

    # Friends are not part of this application.
    saved_data.pop("friends", None)

    return saved_data


def save_data() -> None:
    try:
        with DATA_FILE.open("w", encoding="utf-8") as file:
            json.dump(
                st.session_state.data,
                file,
                indent=4,
                ensure_ascii=False,
            )
    except OSError as exc:
        st.error(f"Unable to save your data: {exc}")


if "data" not in st.session_state:
    st.session_state.data = load_data()

data = st.session_state.data


# --------------------------------------------------
# CALCULATIONS
# --------------------------------------------------

def total_modules() -> int:
    return sum(
        len(subject.get("modules", []))
        for subject in data["subjects"].values()
    )


def completed_modules() -> int:
    return sum(
        1
        for subject in data["subjects"].values()
        for module in subject.get("modules", [])
        if module.get("completed", False)
    )


def syllabus_percentage() -> float:
    total = total_modules()
    if total == 0:
        return 0.0

    return round(completed_modules() / total * 100, 1)


def total_study_hours() -> float:
    minutes = sum(
        session.get("minutes", 0)
        for session in data["study_sessions"]
    )
    return minutes / 60


def today_study_minutes() -> int:
    today = str(date.today())

    return sum(
        session.get("minutes", 0)
        for session in data["study_sessions"]
        if session.get("date") == today
    )


# --------------------------------------------------
# SIDEBAR NAVIGATION
# --------------------------------------------------

with st.sidebar:
    st.title("🩺 MedCore")
    st.caption("Your focused MBBS study companion")
    st.divider()

    page = st.radio(
        "Workspace",
        [
            "🏠 Dashboard",
            "👤 My Profile",
            "📚 Syllabus Tracker",
            "📅 Study Schedule",
            "📝 Exam Tracker",
            "⏱️ Study Hours",
        ],
    )

    st.divider()
    st.caption("Plan • Study • Track • Improve")


# --------------------------------------------------
# DASHBOARD
# --------------------------------------------------

if page == "🏠 Dashboard":
    name = data["profile"].get("name", "").strip()
    greeting = (
        f"Welcome back, {name}"
        if name
        else "Welcome to MedCore"
    )

    st.title(f"🩺 {greeting}")
    st.markdown(
        '<div class="app-subtitle">'
        'Your personal MBBS command center.'
        '</div>',
        unsafe_allow_html=True,
    )

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "MBBS Year",
            data["profile"]["mbbs_year"],
        )

    with col2:
        st.metric(
            "Syllabus",
            f"{syllabus_percentage():.1f}%",
        )

    with col3:
        st.metric(
            "Study Hours",
            f"{total_study_hours():.1f}",
        )

    with col4:
        st.metric(
            "Modules",
            f"{completed_modules()}/{total_modules()}",
        )

    st.divider()

    left, right = st.columns([1.4, 1])

    with left:
        st.subheader("📊 Syllabus Progress")

        progress = syllabus_percentage() / 100
        st.progress(progress)

        st.caption(
            f"{completed_modules()} of "
            f"{total_modules()} modules completed"
        )

        st.subheader("⏱️ Today's Study")

        today_hours = today_study_minutes() / 60
        target = float(
            data["profile"].get("daily_target", 4.0)
        )

        target_progress = (
            min(today_hours / target, 1.0)
            if target > 0
            else 0
        )

        st.progress(target_progress)
        st.caption(
            f"{today_hours:.1f} / {target:.1f} hours"
        )

    with right:
        st.subheader("📝 Upcoming Exams")

        upcoming = []

        for exam in data["exams"]:
            try:
                exam_date = date.fromisoformat(exam["date"])
            except (KeyError, ValueError, TypeError):
                continue

            days_left = (exam_date - date.today()).days

            if days_left >= 0:
                upcoming.append(
                    (
                        days_left,
                        exam.get("name", "Untitled Exam"),
                        exam.get("subject", ""),
                    )
                )

        upcoming.sort(key=lambda item: item[0])

        if upcoming:
            for days, exam_name, subject in upcoming[:5]:
                countdown = (
                    "Today"
                    if days == 0
                    else f"{days} days left"
                )

                st.info(
                    f"**{exam_name}**\n\n"
                    f"{subject} · {countdown}"
                )
        else:
            st.info(
                "No upcoming exams. Add your next exam "
                "from Exam Tracker."
            )


# --------------------------------------------------
# MY PROFILE
# --------------------------------------------------

elif page == "👤 My Profile":
    st.title("👤 My Profile")

    st.markdown(
        '<div class="app-subtitle">'
        'Set the information used to personalize your dashboard.'
        '</div>',
        unsafe_allow_html=True,
    )

    with st.form("profile_form"):
        name = st.text_input(
            "Your name",
            value=data["profile"].get("name", ""),
            placeholder="Enter your name",
        )

        try:
            current_year = int(
                data["profile"].get("mbbs_year", 1)
            )
        except (ValueError, TypeError):
            current_year = 1

        current_year = max(1, min(5, current_year))

        year = st.selectbox(
            "MBBS Year",
            options=[1, 2, 3, 4, 5],
            index=current_year - 1,
        )

        try:
            current_target = float(
                data["profile"].get("daily_target", 4.0)
            )
        except (ValueError, TypeError):
            current_target = 4.0

        current_target = max(
            0.5,
            min(24.0, current_target),
        )

        target = st.number_input(
            "Daily study target (hours)",
            min_value=0.5,
            max_value=24.0,
            value=current_target,
            step=0.5,
        )

        submitted = st.form_submit_button(
            "Save Profile",
            use_container_width=True,
            type="primary",
        )

    if submitted:
        data["profile"].update(
            {
                "name": name.strip(),
                "mbbs_year": year,
                "daily_target": target,
            }
        )

        save_data()
        st.success("Profile updated successfully.")


# --------------------------------------------------
# SYLLABUS TRACKER
# --------------------------------------------------

elif page == "📚 Syllabus Tracker":
    st.title("📚 Syllabus Tracker")

    st.markdown(
        '<div class="app-subtitle">'
        'Organize subjects and track module completion.'
        '</div>',
        unsafe_allow_html=True,
    )

    with st.form("subject_form"):
        subject_name = st.text_input(
            "Subject name",
            placeholder="e.g. Anatomy",
        )

        module_count = st.number_input(
            "Initial modules",
            min_value=1,
            max_value=15,
            value=5,
            step=1,
        )

        create_subject = st.form_submit_button(
            "Create Subject",
            use_container_width=True,
            type="primary",
        )

    if create_subject:
        subject_name = subject_name.strip()

        if not subject_name:
            st.warning("Please enter a subject name.")

        elif subject_name in data["subjects"]:
            st.warning("That subject already exists.")

        else:
            data["subjects"][subject_name] = {
                "modules": [
                    {
                        "name": f"Module {i}",
                        "completed": False,
                    }
                    for i in range(1, int(module_count) + 1)
                ]
            }

            save_data()
            st.success(
                f"{subject_name} created successfully."
            )
            st.rerun()

    st.divider()

    if not data["subjects"]:
        st.info(
            "No subjects yet. Create your first subject above."
        )

    for subject_name, subject in data["subjects"].items():
        modules = subject.get("modules", [])

        with st.expander(
            f"📚 {subject_name}",
            expanded=True,
        ):
            completed = sum(
                1
                for module in modules
                if module.get("completed", False)
            )

            percentage = (
                round(completed / len(modules) * 100, 1)
                if modules
                else 0
            )

            st.write(
                f"**Progress: {completed}/{len(modules)} "
                f"modules ({percentage}%)**"
            )

            st.progress(percentage / 100)

            for index, module in enumerate(modules):
                checked = st.checkbox(
                    module.get(
                        "name",
                        f"Module {index + 1}",
                    ),
                    value=module.get("completed", False),
                    key=f"module_{subject_name}_{index}",
                )

                if checked != module.get("completed", False):
                    module["completed"] = checked
                    save_data()

            if len(modules) < 15:
                with st.form(f"module_form_{subject_name}"):
                    new_module = st.text_input(
                        "Add module",
                        placeholder="e.g. Thorax",
                    )

                    add_module = st.form_submit_button(
                        "Add Module"
                    )

                if add_module:
                    new_module = new_module.strip()

                    if not new_module:
                        st.warning(
                            "Please enter a module name."
                        )
                    else:
                        modules.append(
                            {
                                "name": new_module,
                                "completed": False,
                            }
                        )

                        save_data()
                        st.rerun()


# --------------------------------------------------
# STUDY SCHEDULE
# --------------------------------------------------

elif page == "📅 Study Schedule":
    st.title("📅 Study Schedule")

    st.markdown(
        '<div class="app-subtitle">'
        'Build a clear plan around your subjects and goals.'
        '</div>',
        unsafe_allow_html=True,
    )

    with st.form("schedule_form"):
        study_date = st.date_input(
            "Study date",
            value=date.today(),
        )

        study_subject = st.text_input(
            "Subject",
            placeholder="e.g. Anatomy",
        )

        study_topic = st.text_input(
            "Module / Topic",
            placeholder="e.g. Thorax",
        )

        study_hours = st.number_input(
            "Planned hours",
            min_value=0.5,
            max_value=24.0,
            value=1.0,
            step=0.5,
        )

        add_session = st.form_submit_button(
            "Add to Schedule",
            use_container_width=True,
            type="primary",
        )

    if add_session:
        if not study_subject.strip() or not study_topic.strip():
            st.warning(
                "Please enter both a subject and a topic."
            )
        else:
            data["schedule"].append(
                {
                    "date": str(study_date),
                    "subject": study_subject.strip(),
                    "topic": study_topic.strip(),
                    "hours": study_hours,
                    "done": False,
                }
            )

            save_data()
            st.success("Study session added.")
            st.rerun()

    st.divider()
    st.subheader("🗓️ Your Schedule")

    schedule = sorted(
        enumerate(data["schedule"]),
        key=lambda pair: pair[1].get("date", ""),
    )

    future_items = [
        (index, item)
        for index, item in schedule
        if item.get("date", "") >= str(date.today())
    ]

    if not future_items:
        st.info("Your schedule is empty.")

    else:
        for index, item in future_items:
            label = (
                f"{item.get('date')} — "
                f"{item.get('subject')} — "
                f"{item.get('topic')} "
                f"({item.get('hours', 0)}h)"
            )

            done = st.checkbox(
                label,
                value=item.get("done", False),
                key=f"schedule_{index}",
            )

            if done != item.get("done", False):
                item["done"] = done
                save_data()


# --------------------------------------------------
# EXAM TRACKER
# --------------------------------------------------

elif page == "📝 Exam Tracker":
    st.title("📝 Exam Tracker")

    st.markdown(
        '<div class="app-subtitle">'
        'Add exams and let MedCore calculate the countdown.'
        '</div>',
        unsafe_allow_html=True,
    )

    with st.form("exam_form"):
        exam_name = st.text_input(
            "Exam name",
            placeholder="e.g. Anatomy Final",
        )

        exam_subject = st.text_input(
            "Subject",
            placeholder="e.g. Anatomy",
        )

        exam_date = st.date_input(
            "Exam date",
            value=date.today(),
        )

        add_exam = st.form_submit_button(
            "Add Exam",
            use_container_width=True,
            type="primary",
        )

    if add_exam:
        if not exam_name.strip():
            st.warning("Please enter an exam name.")

        else:
            data["exams"].append(
                {
                    "name": exam_name.strip(),
                    "subject": exam_subject.strip(),
                    "date": str(exam_date),
                }
            )

            save_data()
            st.success("Exam added.")
            st.rerun()

    st.divider()
    st.subheader("⏳ Exam Countdown")

    exams = sorted(
        enumerate(data["exams"]),
        key=lambda pair: pair[1].get("date", ""),
    )

    if not exams:
        st.info("No exams added yet.")

    else:
        for index, exam in exams:
            try:
                exam_day = date.fromisoformat(exam["date"])
            except (KeyError, ValueError, TypeError):
                continue

            days = (exam_day - date.today()).days
            name = exam.get("name", "Untitled Exam")
            subject = exam.get("subject", "")

            if days < 0:
                st.error(f"**{name}** — Exam passed")

            elif days == 0:
                st.warning(f"**{name}** — TODAY")

            else:
                st.info(
                    f"**{name}** · {subject}\n\n"
                    f"📅 {exam['date']} · "
                    f"⏳ **{days} days left**"
                )

            if st.button(
                "Delete exam",
                key=f"delete_exam_{index}",
            ):
                data["exams"].pop(index)
                save_data()
                st.rerun()


# --------------------------------------------------
# STUDY HOURS
# --------------------------------------------------

elif page == "⏱️ Study Hours":
    st.title("⏱️ Study Hours")

    st.markdown(
        '<div class="app-subtitle">'
        'Record focused study time and review your history.'
        '</div>',
        unsafe_allow_html=True,
    )

    with st.form("study_form"):
        session_date = st.date_input(
            "Date",
            value=date.today(),
        )

        subject = st.text_input(
            "Subject studied",
            placeholder="e.g. Physiology",
        )

        hours = st.number_input(
            "Hours",
            min_value=0,
            max_value=24,
            value=1,
            step=1,
        )

        minutes = st.number_input(
            "Extra minutes",
            min_value=0,
            max_value=59,
            value=0,
            step=1,
        )

        record_study = st.form_submit_button(
            "Record Study",
            use_container_width=True,
            type="primary",
        )

    if record_study:
        total_minutes = int(hours) * 60 + int(minutes)

        if total_minutes <= 0:
            st.warning(
                "Enter at least some study time."
            )

        else:
            data["study_sessions"].append(
                {
                    "date": str(session_date),
                    "subject": subject.strip() or "General Study",
                    "minutes": total_minutes,
                }
            )

            save_data()

            st.success(
                f"Recorded {int(hours)}h "
                f"{int(minutes)}m of study."
            )
            st.rerun()

    st.divider()

    today_hours = today_study_minutes() / 60
    total_hours = total_study_hours()

    col1, col2 = st.columns(2)

    with col1:
        st.metric("Today", f"{today_hours:.1f} hours")

    with col2:
        st.metric(
            "All Recorded Study",
            f"{total_hours:.1f} hours",
        )

    st.divider()
    st.subheader("📖 Recent Study History")

    history = data["study_sessions"][-20:]

    if not history:
        st.info("No study sessions recorded yet.")

    else:
        for session in reversed(history):
            minutes = int(session.get("minutes", 0))

            st.write(
                f"📅 {session.get('date')} — "
                f"**{session.get('subject', 'General Study')}** — "
                f"{minutes // 60}h {minutes % 60}m"
            )


# --------------------------------------------------
# APPLICATION FOOTER
# --------------------------------------------------

st.divider()

st.caption(
    "MedCore — Clinical OS · Personal MBBS Study Planner"
)

