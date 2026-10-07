import streamlit as st
import json
import os
from datetime import date, datetime

# =========================================================
# DOCTORS — PERSONALIZED MBBS STUDY APP
# =========================================================

st.set_page_config(
    page_title="DOCTORS",
    page_icon="🩺",
    layout="wide"
)

DATA_FILE = "doctors_data.json"


# =========================================================
# DATA
# =========================================================

def default_data():
    return {
        "profile": {
            "name": "",
            "mbbs_year": 1,
            "daily_target": 4.0
        },
        "subjects": {},
        "exams": [],
        "study_sessions": [],
        "schedule": []
    }


def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return default_data()

    return default_data()


def save_data():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(st.session_state.data, f, indent=4)


if "data" not in st.session_state:
    st.session_state.data = load_data()


data = st.session_state.data


# =========================================================
# HELPER FUNCTIONS
# =========================================================

def total_modules():
    total = 0

    for subject in data["subjects"].values():
        total += len(subject["modules"])

    return total


def completed_modules():
    completed = 0

    for subject in data["subjects"].values():
        for module in subject["modules"]:
            if module["completed"]:
                completed += 1

    return completed


def syllabus_percentage():
    total = total_modules()

    if total == 0:
        return 0

    return round((completed_modules() / total) * 100, 1)


def total_study_hours():
    total_minutes = sum(
        session["minutes"]
        for session in data["study_sessions"]
    )

    return total_minutes / 60


def today_study_minutes():
    today = str(date.today())

    return sum(
        session["minutes"]
        for session in data["study_sessions"]
        if session["date"] == today
    )


# =========================================================
# SIDEBAR
# =========================================================

st.sidebar.title("🩺 DOCTORS")

st.sidebar.caption("Your personalized MBBS study companion")

page = st.sidebar.radio(
    "MENU",
    [
        "🏠 Dashboard",
        "👤 My Profile",
        "📚 Syllabus Tracker",
        "📅 Study Schedule",
        "📝 Exam Tracker",
        "⏱️ Study Hours",
        "👥 Friends"
    ]
)


# =========================================================
# DASHBOARD
# =========================================================

if page == "🏠 Dashboard":

    name = data["profile"]["name"]

    if name:
        st.title(f"🩺 Welcome, {name}!")
    else:
        st.title("🩺 DOCTORS")

    st.subheader("Your personalized MBBS dashboard")

    st.write("---")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "🎓 MBBS Year",
            data["profile"]["mbbs_year"]
        )

    with col2:
        st.metric(
            "📚 Syllabus",
            f"{syllabus_percentage()}%"
        )

    with col3:
        st.metric(
            "⏱️ Study Hours",
            f"{total_study_hours():.1f}"
        )

    with col4:
        st.metric(
            "📖 Modules",
            f"{completed_modules()}/{total_modules()}"
        )

    st.write("---")

    st.header("📊 Syllabus Progress")

    progress = syllabus_percentage() / 100

    st.progress(progress)

    st.write(
        f"**{completed_modules()} of {total_modules()} modules completed**"
    )

    st.write("---")

    st.header("⏱️ Today's Study")

    today_minutes = today_study_minutes()

    target = data["profile"]["daily_target"]

    today_hours = today_minutes / 60

    st.write(
        f"**{today_hours:.1f} / {target:.1f} hours**"
    )

    st.progress(
        min(today_hours / target, 1.0)
        if target > 0 else 0
    )

    st.write("---")

    st.header("📝 Upcoming Exams")

    upcoming = []

    for exam in data["exams"]:

        exam_date = date.fromisoformat(exam["date"])

        days_left = (exam_date - date.today()).days

        if days_left >= 0:
            upcoming.append(
                (days_left, exam["name"], exam["subject"])
            )

    upcoming.sort()

    if upcoming:

        for days, name, subject in upcoming[:5]:

            if days == 0:
                countdown = "TODAY!"
            else:
                countdown = f"{days} days left"

            st.info(
                f"📝 **{name}** — {subject}\n\n"
                f"⏳ **{countdown}**"
            )

    else:
        st.write("No upcoming exams added yet.")

    st.write("---")

    st.caption(
        "DOCTORS 🩺 — Plan. Study. Track. Improve."
    )


# =========================================================
# PROFILE
# =========================================================

elif page == "👤 My Profile":

    st.title("👤 My Profile")

    st.write(
        "Your profile controls your personalized study dashboard."
    )

    name = st.text_input(
        "Your name",
        value=data["profile"]["name"]
    )

    year = st.selectbox(
        "MBBS Year",
        [1, 2, 3, 4, 5],
        index=data["profile"]["mbbs_year"] - 1
    )

    target = st.number_input(
        "Daily study target (hours)",
        min_value=0.5,
        max_value=24.0,
        value=float(data["profile"]["daily_target"]),
        step=0.5
    )

    if st.button("💾 Save Profile", use_container_width=True):

        data["profile"]["name"] = name
        data["profile"]["mbbs_year"] = year
        data["profile"]["daily_target"] = target

        save_data()

        st.success("Profile saved!")


# =========================================================
# SYLLABUS TRACKER
# =========================================================

elif page == "📚 Syllabus Tracker":

    st.title("📚 Syllabus Tracker")

    st.write(
        "Create your own subjects and up to 15 modules per subject."
    )

    st.header("➕ Add Subject")

    subject_name = st.text_input(
        "Subject name",
        placeholder="Example: Anatomy"
    )

    module_count = st.number_input(
        "Number of modules",
        min_value=1,
        max_value=15,
        value=5,
        step=1
    )

    if st.button("➕ Create Subject"):

        if subject_name.strip():

            if subject_name not in data["subjects"]:

                modules = []

                for i in range(1, module_count + 1):

                    modules.append({
                        "name": f"Module {i}",
                        "completed": False
                    })

                data["subjects"][subject_name] = {
                    "modules": modules
                }

                save_data()

                st.success(
                    f"{subject_name} added with {module_count} modules!"
                )

            else:
                st.warning("That subject already exists.")

        else:
            st.warning("Please enter a subject name.")

    st.write("---")

    st.header("📖 Your Subjects")

    if not data["subjects"]:

        st.info(
            "No subjects yet. Add your first subject above."
        )

    for subject_name, subject in data["subjects"].items():

        with st.expander(
            f"📚 {subject_name}"
        ):

            modules = subject["modules"]

            completed = sum(
                1 for module in modules
                if module["completed"]
            )

            percentage = (
                round(completed / len(modules) * 100, 1)
                if modules else 0
            )

            st.write(
                f"**Progress: {completed}/{len(modules)} "
                f"modules ({percentage}%)**"
            )

            st.progress(percentage / 100)

            for i, module in enumerate(modules):

                checked = st.checkbox(
                    module["name"],
                    value=module["completed"],
                    key=f"{subject_name}_{i}"
                )

                if checked != module["completed"]:

                    module["completed"] = checked
                    save_data()

            st.write("")

            new_module = st.text_input(
                "Add a module",
                key=f"new_{subject_name}"
            )

            if st.button(
                "➕ Add Module",
                key=f"add_{subject_name}"
            ):

                if len(modules) >= 15:

                    st.error(
                        "Maximum 15 modules per subject."
                    )

                elif new_module.strip():

                    modules.append({
                        "name": new_module,
                        "completed": False
                    })

                    save_data()

                    st.rerun()


# =========================================================
# STUDY SCHEDULE
# =========================================================

elif page == "📅 Study Schedule":

    st.title("📅 Personalized Study Schedule")

    st.write(
        "Create your own study plan based on your subjects and goals."
    )

    study_date = st.date_input(
        "Study date",
        value=date.today()
    )

    study_subject = st.text_input(
        "Subject",
        placeholder="Example: Anatomy"
    )

    study_topic = st.text_input(
        "Module / Topic",
        placeholder="Example: Thorax"
    )

    study_hours = st.number_input(
        "Planned hours",
        min_value=0.5,
        max_value=24.0,
        value=1.0,
        step=0.5
    )

    if st.button(
        "📅 Add to Schedule",
        use_container_width=True
    ):

        if study_subject and study_topic:

            data["schedule"].append({
                "date": str(study_date),
                "subject": study_subject,
                "topic": study_topic,
                "hours": study_hours,
                "done": False
            })

            save_data()

            st.success("Study session added!")

    st.write("---")

    st.header("🗓️ Your Schedule")

    schedule = sorted(
        data["schedule"],
        key=lambda x: x["date"]
    )

    if schedule:

        for i, item in enumerate(schedule):

            if item["date"] >= str(date.today()):

                done = st.checkbox(
                    f"{item['date']} — "
                    f"{item['subject']} — "
                    f"{item['topic']} "
                    f"({item['hours']}h)",
                    value=item["done"],
                    key=f"schedule_{i}"
                )

                if done != item["done"]:

                    item["done"] = done
                    save_data()

    else:

        st.info("Your schedule is empty.")


# =========================================================
# EXAM TRACKER
# =========================================================

elif page == "📝 Exam Tracker":

    st.title("📝 Exam Tracker")

    st.write(
        "Add your own exams. DOCTORS calculates the countdown automatically."
    )

    exam_name = st.text_input(
        "Exam name",
        placeholder="Example: Anatomy Final"
    )

    exam_subject = st.text_input(
        "Subject",
        placeholder="Example: Anatomy"
    )

    exam_date = st.date_input(
        "Exam date",
        value=date.today()
    )

    if st.button(
        "➕ Add Exam",
        use_container_width=True
    ):

        if exam_name:

            data["exams"].append({
                "name": exam_name,
                "subject": exam_subject,
                "date": str(exam_date)
            })

            save_data()

            st.success("Exam added!")

    st.write("---")

    st.header("⏳ Exam Countdown")

    exams = sorted(
        data["exams"],
        key=lambda x: x["date"]
    )

    if exams:

        for exam in exams:

            exam_day = date.fromisoformat(
                exam["date"]
            )

            days = (
                exam_day - date.today()
            ).days

            if days < 0:

                st.error(
                    f"❌ {exam['name']} — Exam passed"
                )

            elif days == 0:

                st.warning(
                    f"🚨 {exam['name']} — TODAY!"
                )

            else:

                st.info(
                    f"📝 **{exam['name']}** "
                    f"({exam['subject']})\n\n"
                    f"📅 {exam['date']} — "
                    f"⏳ **{days} days left**"
                )

    else:

        st.info("No exams added yet.")


# =========================================================
# STUDY HOURS
# =========================================================

elif page == "⏱️ Study Hours":

    st.title("⏱️ Study Hours")

    st.write(
        "Record how much you study each day."
    )

    session_date = st.date_input(
        "Date",
        value=date.today()
    )

    subject = st.text_input(
        "Subject studied",
        placeholder="Example: Physiology"
    )

    hours = st.number_input(
        "Hours",
        min_value=0,
        max_value=24,
        value=1
    )

    minutes = st.number_input(
        "Extra minutes",
        min_value=0,
        max_value=59,
        value=0
    )

    if st.button(
        "⏱️ Record Study",
        use_container_width=True
    ):

        total_minutes = hours * 60 + minutes

        if total_minutes > 0:

            data["study_sessions"].append({
                "date": str(session_date),
                "subject": subject,
                "minutes": total_minutes
            })

            save_data()

            st.success(
                f"Recorded {hours}h {minutes}m of study!"
            )

    st.write("---")

    st.header("📊 Study Statistics")

    total = total_study_hours()

    today = today_study_minutes() / 60

    st.metric(
        "Today",
        f"{today:.1f} hours"
    )

    st.metric(
        "All recorded study",
        f"{total:.1f} hours"
    )

    st.write("---")

    st.subheader("📖 Study History")

    for session in reversed(
        data["study_sessions"][-20:]
    ):

        st.write(
            f"📅 {session['date']} — "
            f"**{session['subject']}** — "
            f"{session['minutes'] // 60}h "
            f"{session['minutes'] % 60}m"
        )


# =========================================================
# FRIENDS
# =========================================================

elif page == "👥 Friends":

    st.title("👥 Study Friends")

    st.write(
        "This first version lets you keep a simple private comparison "
        "list. We can build online friend accounts later."
    )

    st.info(
        "For privacy, friend information is stored only on your computer "
        "in this version."
    )

    friend_name = st.text_input(
        "Friend name"
    )

    friend_hours = st.number_input(
        "Friend's study hours",
        min_value=0.0,
        max_value=5000.0,
        value=0.0,
        step=0.5
    )

    if "friends" not in data:
        data["friends"] = []

    if st.button(
        "➕ Add Friend",
        use_container_width=True
    ):

        if friend_name:

            data["friends"].append({
                "name": friend_name,
                "hours": friend_hours
            })

            save_data()

            st.success("Friend added!")

    st.write("---")

    st.header("🏆 Study Comparison")

    leaderboard = []

    if data["profile"]["name"]:

        leaderboard.append({
            "name": data["profile"]["name"],
            "hours": total_study_hours()
        })

    for friend in data.get("friends", []):

        leaderboard.append(friend)

    leaderboard.sort(
        key=lambda x: x["hours"],
        reverse=True
    )

    if leaderboard:

        for position, person in enumerate(
            leaderboard,
            start=1
        ):

            if position == 1:
                medal = "🥇"
            elif position == 2:
                medal = "🥈"
            elif position == 3:
                medal = "🥉"
            else:
                medal = "👤"

            st.write(
                f"{medal} **{position}. "
                f"{person['name']}** — "
                f"{person['hours']:.1f} hours"
            )

    else:

        st.info("Add yourself and your friends to compare study hours.")


# =========================================================
# FOOTER
# =========================================================

st.write("---")

st.caption(
    "DOCTORS 🩺 — Personalized MBBS Study Companion"
)