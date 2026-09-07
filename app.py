from flask import Flask, render_template, request, redirect, session

app = Flask(__name__)
app.secret_key = "skillbridge_hackathon_2026"


# ==================================================
# CAREER DATABASE
# ==================================================

CAREERS = [
    {
        "title": "Backend Developer",
        "category": "Software Development",
        "description": "Build server-side applications, APIs, databases, and business logic.",
        "skills": ["python", "java", "sql", "flask", "django", "git"]
    },
    {
        "title": "Frontend Developer",
        "category": "Web Development",
        "description": "Build responsive, interactive, and user-friendly web interfaces.",
        "skills": ["html", "css", "javascript", "react", "git"]
    },
    {
        "title": "Full Stack Developer",
        "category": "Software Development",
        "description": "Build complete applications across both frontend and backend technologies.",
        "skills": ["html", "css", "javascript", "python", "sql", "git"]
    },
    {
        "title": "Data Analyst",
        "category": "Data Science",
        "description": "Analyze data and transform information into useful business insights.",
        "skills": ["python", "sql", "excel", "power bi", "statistics"]
    },
    {
        "title": "Data Scientist",
        "category": "Data Science",
        "description": "Use programming, statistics, and machine learning to solve data problems.",
        "skills": ["python", "sql", "statistics", "machine learning", "pandas"]
    },
    {
        "title": "Cybersecurity Analyst",
        "category": "Cybersecurity",
        "description": "Protect systems, networks, applications, and digital information.",
        "skills": ["networking", "linux", "python", "security", "wireshark"]
    },
    {
        "title": "Cloud Engineer",
        "category": "Cloud Computing",
        "description": "Build, deploy, and manage cloud infrastructure and services.",
        "skills": ["aws", "azure", "linux", "networking", "docker"]
    }
]


# ==================================================
# HELPER FUNCTION: CREATE LEARNING ROADMAP
# ==================================================

def create_roadmap(missing_skills, assessment_score):

    roadmap = []

    # Assessment-based starting point
    if assessment_score < 40:

        roadmap.append({
            "step": "Build Strong Fundamentals",
            "description": (
                "Start by strengthening programming basics, databases, "
                "and core software development concepts."
            )
        })

    elif assessment_score < 70:

        roadmap.append({
            "step": "Strengthen Your Technical Foundation",
            "description": (
                "Improve your understanding through consistent practice "
                "and small hands-on exercises."
            )
        })

    else:

        roadmap.append({
            "step": "Move Towards Advanced Practice",
            "description": (
                "Your foundation is strong. Focus on real-world projects, "
                "advanced concepts, and job-ready skills."
            )
        })


    # Add missing skills
    for skill in missing_skills[:3]:

        roadmap.append({
            "step": f"Learn {skill.title()}",
            "description": (
                f"Learn the fundamentals of {skill.title()} and build "
                f"a small practical project using it."
            )
        })


    # Always recommend a project
    roadmap.append({
        "step": "Build a Portfolio Project",
        "description": (
            "Create a real-world project that combines your skills and "
            "showcase it on GitHub."
        )
    })


    # Job preparation
    roadmap.append({
        "step": "Prepare for Opportunities",
        "description": (
            "Improve your resume, GitHub profile, and interview preparation "
            "before applying for relevant opportunities."
        )
    })

    return roadmap


# ==================================================
# HOME
# ==================================================

@app.route("/")
def home():

    return render_template("index.html")


# ==================================================
# PROFILE
# ==================================================

@app.route("/profile", methods=["GET", "POST"])
def profile():

    if request.method == "POST":

        name = request.form.get("name", "").strip()
        education = request.form.get("education", "")
        experience = request.form.get("experience", "")
        skills_input = request.form.get("skills", "")
        career_interest = request.form.get("career_interest", "")

        # Convert comma-separated skills into a clean list
        skills_list = [
            skill.strip().lower()
            for skill in skills_input.split(",")
            if skill.strip()
        ]

        # Store profile information
        session["name"] = name
        session["education"] = education
        session["experience"] = experience
        session["skills"] = skills_list
        session["career_interest"] = career_interest

        # Clear old assessment results
        session.pop("assessment_score", None)
        session.pop("assessment_correct", None)

        return redirect("/assessment")

    return render_template("profile.html")


# ==================================================
# ASSESSMENT
# ==================================================

@app.route("/assessment")
def assessment():

    return render_template("assessment.html")


# ==================================================
# RESULTS + CAREER MATCHING ENGINE
# ==================================================

@app.route("/results", methods=["GET", "POST"])
def results():

    # ----------------------------------------------
    # CALCULATE ASSESSMENT SCORE
    # ----------------------------------------------

    if request.method == "POST":

        answers = [
            request.form.get("q1"),
            request.form.get("q2"),
            request.form.get("q3")
        ]

        score = sum(
            1
            for answer in answers
            if answer == "correct"
        )

        percentage = round((score / 3) * 100)

        session["assessment_score"] = percentage
        session["assessment_correct"] = score

    else:

        percentage = session.get("assessment_score", 0)
        score = session.get("assessment_correct", 0)


    # ----------------------------------------------
    # GET USER PROFILE DATA
    # ----------------------------------------------

    user_skills = session.get("skills", [])
    career_interest = session.get("career_interest", "")
    user_name = session.get("name", "User")


    # Prevent direct access without profile
    if not user_skills and not user_name:

        return redirect("/profile")


    # ----------------------------------------------
    # CAREER MATCHING ENGINE
    # ----------------------------------------------

    matched_careers = []

    for career in CAREERS:

        required_skills = career["skills"]


        # Find skills the user already has
        matching_skills = [
            skill
            for skill in required_skills
            if skill in user_skills
        ]


        # Find skills the user needs to develop
        missing_skills = [
            skill
            for skill in required_skills
            if skill not in user_skills
        ]


        # ------------------------------------------
        # 1. SKILL MATCH SCORE (0–60)
        # ------------------------------------------

        skill_ratio = (
            len(matching_skills) / len(required_skills)
        )

        skill_score = skill_ratio * 60


        # ------------------------------------------
        # 2. CAREER INTEREST SCORE (0–25)
        # ------------------------------------------

        interest_score = 0

        if career["category"].lower() == career_interest.lower():

            interest_score = 25


        # ------------------------------------------
        # 3. ASSESSMENT PERFORMANCE (0–15)
        # ------------------------------------------

        assessment_score = (
            percentage / 100
        ) * 15


        # ------------------------------------------
        # FINAL MATCH SCORE
        # ------------------------------------------

        final_match = round(
            skill_score
            + interest_score
            + assessment_score
        )


        # Keep score realistic and between 0–100
        final_match = max(0, min(final_match, 100))


        # ------------------------------------------
        # EXPERIENCE BONUS
        # ------------------------------------------

        experience = session.get("experience", "")

        if experience == "1–3 Years":
            final_match += 3

        elif experience == "3+ Years":
            final_match += 5


        final_match = min(final_match, 100)


        # Save career result
        matched_careers.append({

            "title": career["title"],

            "category": career["category"],

            "description": career["description"],

            "match": final_match,

            "matching_skills": matching_skills,

            "missing_skills": missing_skills

        })


    # ----------------------------------------------
    # SORT CAREERS
    # ----------------------------------------------

    matched_careers.sort(

        key=lambda career: career["match"],

        reverse=True

    )


    # ----------------------------------------------
    # BEST CAREER
    # ----------------------------------------------

    best_career = matched_careers[0]


    # ----------------------------------------------
    # CREATE PERSONALIZED ROADMAP
    # ----------------------------------------------

    roadmap = create_roadmap(

        best_career["missing_skills"],

        percentage

    )


    # ----------------------------------------------
    # CAREER READINESS
    # ----------------------------------------------

    if percentage >= 80:

        readiness = "High"

        readiness_message = (
            "You have a strong technical foundation. Focus on building "
            "real-world projects, improving your portfolio, and preparing "
            "for job opportunities."
        )


    elif percentage >= 50:

        readiness = "Developing"

        readiness_message = (
            "You have a good starting foundation. Focused learning and "
            "practical projects can significantly improve your job readiness."
        )


    else:

        readiness = "Beginner"

        readiness_message = (
            "You are at the beginning of your technical learning journey. "
            "Build strong fundamentals step by step and focus on consistent practice."
        )


    # ----------------------------------------------
    # RENDER RESULTS PAGE
    # ----------------------------------------------

    return render_template(

        "results.html",

        name=user_name,

        score=score,

        percentage=percentage,

        skills=user_skills,

        career_interest=career_interest,

        careers=matched_careers[:3],

        best_career=best_career,

        roadmap=roadmap,

        readiness=readiness,

        readiness_message=readiness_message

    )


# ==================================================
# RUN APPLICATION
# ==================================================

if __name__ == "__main__":

    app.run(debug=True)