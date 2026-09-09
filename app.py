import os
import json
from dotenv import load_dotenv
from openai import OpenAI
from flask import Flask, render_template, request, redirect, session, jsonify
from jobs.jobs import find_matching_jobs
from resume.resume_app import resume_bp
from resume.resume_app import resume_bp
# Load environment variables securely from .env
load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)

app = Flask(__name__)
app.secret_key = "skillbridge_hackathon_2026"
app.register_blueprint(resume_bp)

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
# SKILL INTELLIGENCE KNOWLEDGE BASE
# ==================================================

SKILL_CONTEXT = {
    "python": "Core language powering modern backend services, automation scripts, and data engineering pipelines.",
    "java": "Enterprise-grade object-oriented language essential for large-scale backend systems and high-throughput microservices.",
    "sql": "Foundational query language for schema design, data manipulation, relational database management, and analytics.",
    "flask": "Lightweight Python web framework ideal for building fast RESTful APIs, microservices, and backend routing.",
    "django": "Full-featured Python web framework engineered for rapid, secure development of database-driven web platforms.",
    "git": "Industry-standard version control system crucial for team collaboration, code branching, and CI/CD pipelines.",
    "html": "Standard markup language providing structural semantics and accessibility across all web applications.",
    "css": "Essential presentation technology for responsive layouts, design systems, modern themes, and animations.",
    "javascript": "Universal client-side language enabling rich asynchronous interactions, DOM control, and modern dynamic web apps.",
    "react": "Premier component-based JavaScript library for building responsive, stateful single-page frontend applications.",
    "excel": "Fundamental spreadsheet and calculation tool for business modeling, data filtering, and tabular analysis.",
    "power bi": "Enterprise business intelligence platform for data visualization, dashboard creation, and executive reporting.",
    "statistics": "Mathematical foundation for data exploration, hypothesis testing, distributions, and predictive modeling.",
    "machine learning": "Advanced discipline for training predictive models, pattern recognition algorithms, and AI solutions.",
    "pandas": "Standard Python data science library for data cleaning, transformation, and structured series manipulation.",
    "networking": "Crucial knowledge of TCP/IP, OSI models, DNS, firewalls, and secure client-server communication.",
    "linux": "Primary server operating system for enterprise deployments, bash automation, and access permissions.",
    "security": "Core principles of encryption, authorization mechanisms, vulnerability defense, and system hardening.",
    "wireshark": "Essential network packet inspection tool for protocol troubleshooting, packet capture, and security audits.",
    "aws": "Leading cloud infrastructure provider for elastic compute, S3 storage, serverless lambdas, and cloud hosting.",
    "azure": "Enterprise cloud platform deeply integrated with Active Directory, hybrid deployments, and DevOps toolchains.",
    "docker": "Industry containerization standard for packaging dependencies and ensuring reproducible execution anywhere."
}


# ==================================================
# HELPER: DYNAMIC "WHY THIS CAREER MATCHES YOU"
# ==================================================

def generate_match_explanation(best_career, matching_skills, career_interest, assessment_score):
    points = []

    # 1. Matching Skills Rationale
    if matching_skills:
        skill_str = ", ".join(s.title() for s in matching_skills[:3])
        points.append(f"Your background in {skill_str} directly satisfies core technical prerequisites for {best_career['title']}.")
    else:
        points.append(f"Your analytical profile and foundational skills establish a direct entry path into {best_career['title']}.")

    # 2. Career Interest Alignment
    if best_career["category"].lower() == career_interest.lower():
        points.append(f"This role directly fulfills your primary career interest in {career_interest}.")
    else:
        points.append(f"This career recommendation bridges your interest in {career_interest} with high industry demand in {best_career['category']}.")

    # 3. Technical Assessment Impact
    if assessment_score >= 80:
        points.append(f"Your strong {assessment_score}% technical assessment score indicates high engineering aptitude to master advanced workflows rapidly.")
    elif assessment_score >= 50:
        points.append(f"Your {assessment_score}% technical assessment score provides a solid baseline for focused hands-on upskilling.")
    else:
        points.append("With structured practice starting from fundamental concepts, you can rapidly build competitive job readiness.")

    return " ".join(points)


# ==================================================
# HELPER: ADVANCED SKILL GAP ANALYSIS
# ==================================================

def analyze_skill_gaps(best_career, user_skills):
    matching_skills = best_career.get("matching_skills", [])
    missing_skills = best_career.get("missing_skills", [])

    # Partition missing skills into Critical (learn first) and Important (develop next)
    if len(missing_skills) <= 2:
        critical_names = missing_skills
        important_names = []
    else:
        split_idx = (len(missing_skills) + 1) // 2
        critical_names = missing_skills[:split_idx]
        important_names = missing_skills[split_idx:]

    critical = [
        {
            "name": s.title(),
            "priority": "Critical Priority",
            "reason": SKILL_CONTEXT.get(s.lower(), f"Fundamental technical requirement for competitive {best_career['title']} roles.")
        }
        for s in critical_names
    ]

    important = [
        {
            "name": s.title(),
            "priority": "Important",
            "reason": SKILL_CONTEXT.get(s.lower(), f"High-impact framework and methodology that distinguishes top {best_career['title']} candidates.")
        }
        for s in important_names
    ]

    strengths = [
        {
            "name": s.title(),
            "priority": "Demonstrated Strength",
            "reason": SKILL_CONTEXT.get(s.lower(), "Core competency already confirmed in your profile.")
        }
        for s in matching_skills
    ]

    return {
        "critical": critical,
        "important": important,
        "strengths": strengths
    }


# ==================================================
# HELPER: REAL-TIME AI CAREER MENTOR (OPENAI INTEGRATION)
# ==================================================

def get_ai_career_mentor(name, career_interest, assessment_score, best_career, matching_skills, missing_skills, user_skills):
    """
    Generates personalized real-time AI career advice using OpenAI API.
    Supports current OpenAI Responses API with Chat Completions fallback.
    If the API is unavailable, network is down, or key is missing,
    it falls back seamlessly to dynamic local intelligence.
    """
    api_key = os.getenv("OPENAI_API_KEY")

    def build_fallback(note=""):
        top_strengths = [s.title() for s in matching_skills[:3]]
        if not top_strengths and user_skills:
            top_strengths = [s.title() for s in user_skills[:3]]
        if not top_strengths:
            top_strengths = ["Technical Curiosity", "Foundational Problem Solving"]

        top_missing = [s.title() for s in missing_skills[:3]]
        if not top_missing:
            top_missing = ["Production Architecture", "System Design"]

        return {
            "source": "SkillBridge Intelligence (Offline Fallback)",
            "status_note": note,
            "career_assessment": (
                f"{name}, your technical background aligns strongly with {best_career['title']} ({best_career['match']}% match index). "
                f"With a {assessment_score}% assessment score, you have an actionable runway to accelerate into {best_career['category']}."
            ),
            "key_strengths": [
                f"Verified foundational competency in {', '.join(top_strengths)}, directly applicable to {best_career['title']}.",
                f"Demonstrated technical aptitude with {assessment_score}% on the fundamentals assessment."
            ],
            "critical_skills_to_improve": [
                f"Prioritize mastering {top_missing[0]} to unlock core job requisites.",
                f"Build practical fluency in {top_missing[1] if len(top_missing) > 1 else 'Modern Frameworks'} for production-grade reliability."
            ],
            "project_recommendation": {
                "title": f"{best_career['title']} Capstone System",
                "description": (
                    f"Develop an end-to-end service demonstrating full capability in {best_career['title']}. "
                    f"Integrate {top_missing[0]}, implement robust APIs, error handling, and deploy with clean documentation."
                ),
                "technologies": top_strengths + top_missing[:2]
            },
            "conclusion": (
                f"Dedicate 5-10 hours weekly to targeted project building. Transitioning into {best_career['title']} "
                "is a high-probability outcome with focused, practical milestones."
            )
        }

    if not api_key:
        return build_fallback("OpenAI API key not configured; fallback intelligence active.")

    try:
        client = OpenAI(api_key=api_key)

        system_prompt = (
            "You are an inspiring, authoritative AI Career Mentor for SkillBridge AI. "
            "Analyze the candidate's profile and provide structured, highly personalized career guidance. "
            "Return ONLY a valid JSON object without markdown fences with this schema:\n"
            "{\n"
            '  "career_assessment": "Detailed 2-3 sentence strategic readiness diagnosis.",\n'
            '  "key_strengths": ["Strength 1", "Strength 2"],\n'
            '  "critical_skills_to_improve": ["Priority skill 1", "Priority skill 2"],\n'
            '  "project_recommendation": {\n'
            '    "title": "Specific portfolio project name",\n'
            '    "description": "What to build and why it proves job readiness",\n'
            '    "technologies": ["tech1", "tech2", "tech3"]\n'
            "  },\n"
            '  "conclusion": "1-2 sentences of actionable career advice."\n'
            "}"
        )

        user_prompt = f"""
Candidate Name: {name}
Career Interest: {career_interest}
Technical Assessment Score: {assessment_score}%
Best Career Recommendation: {best_career['title']} ({best_career['category']})
Match Score: {best_career['match']}%
Matching Skills: {', '.join(matching_skills) if matching_skills else 'None declared'}
Missing Skills to Develop: {', '.join(missing_skills) if missing_skills else 'None'}
All Declared Skills: {', '.join(user_skills) if user_skills else 'None'}
"""

        response = client.responses.create(
            model="gpt-4o-mini",
            instructions=system_prompt,
            input=user_prompt
        )

        content_str = response.output_text
        parsed_data = json.loads(content_str)

        parsed_data["source"] = "OpenAI AI Mentor"
        parsed_data["status_note"] = "Live OpenAI guidance generated successfully."
        return parsed_data

    except Exception as e:
        print("\nOPENAI ERROR:", str(e), "\n")
        return build_fallback(
            f"OpenAI API error: {str(e)[:100]}"
        )

# ==================================================
# HELPER FUNCTION: CREATE ENHANCED LEARNING ROADMAP
# ==================================================

def create_roadmap(missing_skills, assessment_score, best_career=None):
    career_title = best_career["title"] if best_career else "Target Career"
    roadmap = []
    step_num = 1

    # Assessment-based starting point
    if assessment_score < 40:
        roadmap.append({
            "step_num": step_num,
            "step": "Build Strong Fundamentals",
            "skill": "Core Programming & Computer Science Basics",
            "priority": "High",
            "duration": "2–3 Weeks",
            "description": (
                "Start by strengthening programming basics, syntax, database principles, "
                "and core algorithmic concepts with daily hands-on coding exercises."
            )
        })
        step_num += 1
    elif assessment_score < 70:
        roadmap.append({
            "step_num": step_num,
            "step": "Strengthen Technical Foundation",
            "skill": "Technical Problem Solving & Architecture",
            "priority": "Medium",
            "duration": "1–2 Weeks",
            "description": (
                "Reinforce your technical knowledge through structured problem solving, "
                "debugging sessions, and practical implementations."
            )
        })
        step_num += 1
    else:
        roadmap.append({
            "step_num": step_num,
            "step": "Advanced Architecture & Best Practices",
            "skill": "Design Patterns & System Optimization",
            "priority": "Medium",
            "duration": "1–2 Weeks",
            "description": (
                "Your foundation is solid. Focus on code structure, clean architecture, "
                "and performance optimization to achieve production readiness."
            )
        })
        step_num += 1

    # Add missing skills with personalized priorities and durations
    for idx, skill in enumerate(missing_skills[:3]):
        skill_name = skill.title()
        priority = "High" if idx == 0 else "Medium"
        duration = "2–3 Weeks" if idx == 0 else "1–2 Weeks"
        context_reason = SKILL_CONTEXT.get(skill.lower(), f"Core capability for {career_title}.")

        roadmap.append({
            "step_num": step_num,
            "step": f"Master {skill_name}",
            "skill": skill_name,
            "priority": priority,
            "duration": duration,
            "description": (
                f"Gain practical mastery of {skill_name}. {context_reason} "
                f"Build mini-exercises and integrate it into real-world use cases."
            )
        })
        step_num += 1

    # Always recommend a project
    roadmap.append({
        "step_num": step_num,
        "step": "Build a Full-Stack Portfolio Project",
        "skill": f"Applied {career_title} Capstone",
        "priority": "High",
        "duration": "3–4 Weeks",
        "description": (
            f"Develop a production-grade capstone project tailored for {career_title}. "
            "Combine your acquired skills, document the architecture, and deploy it live with a public GitHub repo."
        )
    })
    step_num += 1

    # Job preparation
    roadmap.append({
        "step_num": step_num,
        "step": "Career Launch & Interview Preparation",
        "skill": "Technical Interviews & Resume Refinement",
        "priority": "Medium",
        "duration": "1–2 Weeks",
        "description": (
            f"Optimize your resume and LinkedIn for {career_title} opportunities. "
            "Practice technical coding interviews, system design walkthroughs, and behavioral questions."
        )
    })

    return roadmap
# ==================================================
# AI CAREER MENTOR
# ==================================================

def get_ai_career_advice(
    name,
    skills,
    career_interest,
    assessment_score,
    best_career
):

    prompt = f"""
You are an AI Career Mentor for SkillBridge AI.

Analyze this student's profile:

Name: {name}
Declared Skills: {', '.join(skills)}
Career Interest: {career_interest}
Technical Assessment Score: {assessment_score}%

Best Career Match: {best_career['title']}

Matching Skills:
{', '.join(best_career['matching_skills'])}

Skills to Develop:
{', '.join(best_career['missing_skills'])}

Give personalized career guidance with these sections:

1. Career Assessment
2. Main Strengths
3. Skills to Learn Next
4. Project Recommendation
5. Motivation

Keep the response concise, practical, and beginner-friendly.
"""

    try:
        response = client.responses.create(
            model="gpt-5.5",
            input=prompt
        )

        return response.output_text

    except Exception as e:

        print("AI Error:", e)

        # FALLBACK RESPONSE
        matching_skills = ", ".join(
            best_career.get("matching_skills", [])
        )

        missing_skills = ", ".join(
            best_career.get("missing_skills", [])
        )

        return f"""
1. Career Assessment

{name}, your profile shows strong potential for a career as a
{best_career['title']}. Your assessment score is {assessment_score}%,
and your interest in {career_interest} aligns with this career path.

2. Main Strengths

Your current strengths include: {matching_skills if matching_skills else "your existing technical foundation"}.

3. Skills to Learn Next

Focus on learning: {missing_skills if missing_skills else "advanced skills related to your career path"}.

4. Project Recommendation

Build a practical project related to {best_career['title']} and upload
it to GitHub. This will strengthen your portfolio.

5. Motivation

Keep learning consistently, {name}. You already have a foundation—focus
on improving one skill at a time and building real projects.
"""
def get_ai_chat_response(question):

    name = session.get("name", "User")
    skills = session.get("skills", [])
    career_interest = session.get("career_interest", "Technology")

    prompt = f"""
You are SkillBridge AI Career Mentor.

You are helping this student:

Name: {name}
Skills: {', '.join(skills)}
Career Interest: {career_interest}

The student asks:

{question}

Give a helpful, practical, beginner-friendly answer.
Keep the answer concise and related to career guidance,
skills, learning, projects, jobs, or technology.
"""

    try:

        response = client.responses.create(
            model="gpt-5.6-luna",
            input=prompt
        )

        return response.output_text

    except Exception as e:

        print("AI CHAT ERROR:", e)

        return (
            "I'm currently unable to connect to the AI service. "
            "Please check the API credits and try again."
        )
    # ============================================================
# AI CHAT API
# ============================================================

@app.route("/ai-chat", methods=["POST"])
def ai_chat():

    data = request.get_json()

    question = data.get("question", "").strip()

    if not question:
        return {
            "answer": "Please enter a question."
        }

    answer = get_ai_chat_response(question)

    return {
        "answer": answer
    }
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
# ==================================================
# CAREER-SPECIFIC ASSESSMENT QUESTIONS
# ==================================================

def get_assessment_questions(career):

    questions_by_career = {

        # ==================================================
        # SOFTWARE DEVELOPMENT
        # ==================================================

        "Software Development": [

            {
                "question": "Which programming language is commonly used for backend development?",
                "options": ["Python", "HTML", "CSS"],
                "answer": "Python"
            },
            {
                "question": "What does API stand for?",
                "options": [
                    "Application Programming Interface",
                    "Advanced Program Internet",
                    "Automatic Programming Integration"
                ],
                "answer": "Application Programming Interface"
            },
            {
                "question": "What is SQL mainly used for?",
                "options": [
                    "Managing databases",
                    "Styling websites",
                    "Creating images"
                ],
                "answer": "Managing databases"
            },
            {
                "question": "Which HTTP method is commonly used to retrieve data?",
                "options": ["GET", "POST", "DELETE"],
                "answer": "GET"
            },
            {
                "question": "Which HTTP method is commonly used to send new data?",
                "options": ["POST", "GET", "OPTIONS"],
                "answer": "POST"
            },
            {
                "question": "What does CRUD stand for?",
                "options": [
                    "Create, Read, Update, Delete",
                    "Code, Run, Upload, Download",
                    "Create, Remove, Update, Design"
                ],
                "answer": "Create, Read, Update, Delete"
            },
            {
                "question": "Which tool is commonly used for version control?",
                "options": ["Git", "Excel", "Photoshop"],
                "answer": "Git"
            },
            {
                "question": "What is JSON commonly used for?",
                "options": [
                    "Exchanging structured data",
                    "Styling web pages",
                    "Creating images"
                ],
                "answer": "Exchanging structured data"
            },
            {
                "question": "What is authentication used for?",
                "options": [
                    "Verifying user identity",
                    "Changing website colors",
                    "Deleting databases"
                ],
                "answer": "Verifying user identity"
            },
            {
                "question": "Which framework is commonly used for Python web development?",
                "options": ["Flask", "Pandas", "NumPy"],
                "answer": "Flask"
            },
            {
                "question": "What is a database?",
                "options": [
                    "An organized collection of data",
                    "A programming language",
                    "A web browser"
                ],
                "answer": "An organized collection of data"
            },
            {
                "question": "What is debugging?",
                "options": [
                    "Finding and fixing errors in code",
                    "Deleting all code",
                    "Designing a logo"
                ],
                "answer": "Finding and fixing errors in code"
            },
            {
                "question": "What does HTTP stand for?",
                "options": [
                    "HyperText Transfer Protocol",
                    "High Text Transfer Program",
                    "Hyper Tool Text Process"
                ],
                "answer": "HyperText Transfer Protocol"
            },
            {
                "question": "What is server-side code responsible for?",
                "options": [
                    "Application logic and data processing",
                    "Only webpage styling",
                    "Creating computer hardware"
                ],
                "answer": "Application logic and data processing"
            },
            {
                "question": "Why is error handling important?",
                "options": [
                    "To handle unexpected problems safely",
                    "To increase screen brightness",
                    "To change HTML colors"
                ],
                "answer": "To handle unexpected problems safely"
            }

        ],


        # ==================================================
        # WEB DEVELOPMENT
        # ==================================================

        "Web Development": [

            {
                "question": "Which language is used to structure web pages?",
                "options": ["HTML", "Python", "SQL"],
                "answer": "HTML"
            },
            {
                "question": "What is CSS mainly used for?",
                "options": [
                    "Styling web pages",
                    "Managing databases",
                    "Backend programming"
                ],
                "answer": "Styling web pages"
            },
            {
                "question": "Which language adds interactivity to websites?",
                "options": ["JavaScript", "HTML", "SQL"],
                "answer": "JavaScript"
            },
            {
                "question": "What does HTML stand for?",
                "options": [
                    "HyperText Markup Language",
                    "HighText Machine Language",
                    "Hyper Tool Markup Logic"
                ],
                "answer": "HyperText Markup Language"
            },
            {
                "question": "What is responsive web design?",
                "options": [
                    "Design that adapts to different screen sizes",
                    "A database system",
                    "A backend framework"
                ],
                "answer": "Design that adapts to different screen sizes"
            },
            {
                "question": "Which HTML tag is used to create a hyperlink?",
                "options": ["<a>", "<img>", "<div>"],
                "answer": "<a>"
            },
            {
                "question": "Which HTML tag is used to display an image?",
                "options": ["<img>", "<a>", "<p>"],
                "answer": "<img>"
            },
            {
                "question": "Which CSS property changes text color?",
                "options": ["color", "margin", "padding"],
                "answer": "color"
            },
            {
                "question": "What is JavaScript mainly used for?",
                "options": [
                    "Adding dynamic behavior",
                    "Managing only databases",
                    "Creating hardware"
                ],
                "answer": "Adding dynamic behavior"
            },
            {
                "question": "Which library is popular for frontend development?",
                "options": ["React", "Flask", "Django"],
                "answer": "React"
            },
            {
                "question": "What does UI stand for?",
                "options": [
                    "User Interface",
                    "Universal Internet",
                    "User Integration"
                ],
                "answer": "User Interface"
            },
            {
                "question": "What does UX focus on?",
                "options": [
                    "User experience",
                    "Database management",
                    "Server configuration"
                ],
                "answer": "User experience"
            },
            {
                "question": "Why are media queries used?",
                "options": [
                    "Creating responsive designs",
                    "Connecting databases",
                    "Creating APIs"
                ],
                "answer": "Creating responsive designs"
            },
            {
                "question": "What is a navigation bar used for?",
                "options": [
                    "Helping users navigate a website",
                    "Storing database records",
                    "Running Python code"
                ],
                "answer": "Helping users navigate a website"
            },
            {
                "question": "What is the purpose of CSS classes?",
                "options": [
                    "Applying styles to multiple elements",
                    "Creating databases",
                    "Sending emails"
                ],
                "answer": "Applying styles to multiple elements"
            }

        ],


        # ==================================================
        # DATA SCIENCE
        # ==================================================

        "Data Science": [

            {
                "question": "Which programming language is widely used in Data Science?",
                "options": ["Python", "HTML", "CSS"],
                "answer": "Python"
            },
            {
                "question": "Which Python library is commonly used for data analysis?",
                "options": ["Pandas", "Flask", "Bootstrap"],
                "answer": "Pandas"
            },
            {
                "question": "Which library is commonly used for numerical computing?",
                "options": ["NumPy", "React", "Django"],
                "answer": "NumPy"
            },
            {
                "question": "What is SQL mainly used for?",
                "options": [
                    "Working with databases",
                    "Styling websites",
                    "Creating animations"
                ],
                "answer": "Working with databases"
            },
            {
                "question": "What is a dataset?",
                "options": [
                    "A collection of related data",
                    "A programming language",
                    "A web browser"
                ],
                "answer": "A collection of related data"
            },
            {
                "question": "What is data visualization used for?",
                "options": [
                    "Understanding and presenting data",
                    "Creating backend servers",
                    "Designing computer hardware"
                ],
                "answer": "Understanding and presenting data"
            },
            {
                "question": "Which chart is useful for comparing categories?",
                "options": ["Bar chart", "Flowchart", "Text editor"],
                "answer": "Bar chart"
            },
            {
                "question": "Which chart is useful for showing trends over time?",
                "options": ["Line chart", "Pie chart", "Table"],
                "answer": "Line chart"
            },
            {
                "question": "What is data cleaning?",
                "options": [
                    "Correcting or removing inaccurate data",
                    "Deleting all data",
                    "Creating a website"
                ],
                "answer": "Correcting or removing inaccurate data"
            },
            {
                "question": "What does CSV stand for?",
                "options": [
                    "Comma-Separated Values",
                    "Computer System Variable",
                    "Code Style Version"
                ],
                "answer": "Comma-Separated Values"
            },
            {
                "question": "What is a missing value?",
                "options": [
                    "Data that is not available",
                    "A duplicate chart",
                    "A programming language"
                ],
                "answer": "Data that is not available"
            },
            {
                "question": "What is filtering data used for?",
                "options": [
                    "Selecting relevant data",
                    "Deleting databases",
                    "Changing programming languages"
                ],
                "answer": "Selecting relevant data"
            },
            {
                "question": "What is the purpose of data analysis?",
                "options": [
                    "Finding useful insights",
                    "Building computer hardware",
                    "Creating only websites"
                ],
                "answer": "Finding useful insights"
            },
            {
                "question": "Which skill is important for Data Science?",
                "options": ["Statistics", "Only HTML", "Only CSS"],
                "answer": "Statistics"
            },
            {
                "question": "What should be done before analyzing data?",
                "options": [
                    "Understand and prepare the data",
                    "Immediately delete the data",
                    "Create a website first"
                ],
                "answer": "Understand and prepare the data"
            }

        ],


        # ==================================================
        # CYBERSECURITY
        # ==================================================

        "Cybersecurity": [

            {
                "question": "What is cybersecurity mainly concerned with?",
                "options": [
                    "Protecting systems and data",
                    "Designing websites",
                    "Creating spreadsheets"
                ],
                "answer": "Protecting systems and data"
            },
            {
                "question": "What is phishing?",
                "options": [
                    "A fraudulent attempt to steal information",
                    "A programming language",
                    "A database"
                ],
                "answer": "A fraudulent attempt to steal information"
            },
            {
                "question": "What is malware?",
                "options": [
                    "Malicious software",
                    "A web browser",
                    "A programming framework"
                ],
                "answer": "Malicious software"
            },
            {
                "question": "What does a firewall help do?",
                "options": [
                    "Monitor and control network traffic",
                    "Create websites",
                    "Write documents"
                ],
                "answer": "Monitor and control network traffic"
            },
            {
                "question": "Why are strong passwords important?",
                "options": [
                    "They improve account security",
                    "They increase internet speed",
                    "They improve screen quality"
                ],
                "answer": "They improve account security"
            },
            {
                "question": "What is two-factor authentication?",
                "options": [
                    "An additional layer of account security",
                    "A programming language",
                    "A database system"
                ],
                "answer": "An additional layer of account security"
            },
            {
                "question": "Which operating system is commonly used in cybersecurity?",
                "options": ["Linux", "HTML", "CSS"],
                "answer": "Linux"
            },
            {
                "question": "What is network security?",
                "options": [
                    "Protecting networks from threats",
                    "Designing websites",
                    "Creating databases"
                ],
                "answer": "Protecting networks from threats"
            },
            {
                "question": "What is encryption used for?",
                "options": [
                    "Protecting data by converting it into a secure form",
                    "Deleting data",
                    "Styling a website"
                ],
                "answer": "Protecting data by converting it into a secure form"
            },
            {
                "question": "What is Wireshark mainly used for?",
                "options": [
                    "Analyzing network traffic",
                    "Creating websites",
                    "Managing spreadsheets"
                ],
                "answer": "Analyzing network traffic"
            },
            {
                "question": "What is a vulnerability?",
                "options": [
                    "A weakness that can be exploited",
                    "A secure password",
                    "A programming language"
                ],
                "answer": "A weakness that can be exploited"
            },
            {
                "question": "What is a cyber attack?",
                "options": [
                    "An attempt to compromise systems or data",
                    "A software update",
                    "A web design technique"
                ],
                "answer": "An attempt to compromise systems or data"
            },
            {
                "question": "Why should software be updated regularly?",
                "options": [
                    "To fix security vulnerabilities",
                    "To change the keyboard",
                    "To reduce monitor size"
                ],
                "answer": "To fix security vulnerabilities"
            },
            {
                "question": "What is social engineering?",
                "options": [
                    "Manipulating people to gain information",
                    "Building social media websites",
                    "Writing database queries"
                ],
                "answer": "Manipulating people to gain information"
            },
            {
                "question": "What is the goal of cybersecurity?",
                "options": [
                    "Protect confidentiality, integrity, and availability",
                    "Only design websites",
                    "Only create applications"
                ],
                "answer": "Protect confidentiality, integrity, and availability"
            }

        ],


        # ==================================================
        # CLOUD COMPUTING
        # ==================================================

        "Cloud Computing": [

            {
                "question": "What is cloud computing?",
                "options": [
                    "Delivering computing services over the internet",
                    "Building only physical computers",
                    "Creating websites without servers"
                ],
                "answer": "Delivering computing services over the internet"
            },
            {
                "question": "Which company provides AWS?",
                "options": ["Amazon", "Google", "Netflix"],
                "answer": "Amazon"
            },
            {
                "question": "What is Microsoft Azure?",
                "options": [
                    "A cloud computing platform",
                    "A programming language",
                    "A database table"
                ],
                "answer": "A cloud computing platform"
            },
            {
                "question": "What is Docker mainly used for?",
                "options": [
                    "Containerizing applications",
                    "Creating spreadsheets",
                    "Designing logos"
                ],
                "answer": "Containerizing applications"
            },
            {
                "question": "Which operating system is commonly used in cloud environments?",
                "options": ["Linux", "HTML", "CSS"],
                "answer": "Linux"
            },
            {
                "question": "What is cloud storage?",
                "options": [
                    "Storing data on remote servers",
                    "Saving data only on paper",
                    "Deleting all files"
                ],
                "answer": "Storing data on remote servers"
            },
            {
                "question": "What does scalability mean in cloud computing?",
                "options": [
                    "Increasing or decreasing resources based on demand",
                    "Changing website colors",
                    "Deleting applications"
                ],
                "answer": "Increasing or decreasing resources based on demand"
            },
            {
                "question": "What is virtualization?",
                "options": [
                    "Creating virtual versions of computing resources",
                    "Creating only physical hardware",
                    "Writing HTML code"
                ],
                "answer": "Creating virtual versions of computing resources"
            },
            {
                "question": "What is a cloud server?",
                "options": [
                    "A server hosted in a cloud environment",
                    "A web browser",
                    "A programming language"
                ],
                "answer": "A server hosted in a cloud environment"
            },
            {
                "question": "What is networking important for in cloud computing?",
                "options": [
                    "Connecting cloud resources and services",
                    "Changing application colors",
                    "Writing documents"
                ],
                "answer": "Connecting cloud resources and services"
            },
            {
                "question": "What is Infrastructure as a Service (IaaS)?",
                "options": [
                    "Cloud-based computing infrastructure",
                    "A website design method",
                    "A programming language"
                ],
                "answer": "Cloud-based computing infrastructure"
            },
            {
                "question": "What is Platform as a Service (PaaS)?",
                "options": [
                    "A platform for developing and deploying applications",
                    "A physical computer",
                    "A text editor"
                ],
                "answer": "A platform for developing and deploying applications"
            },
            {
                "question": "What is Software as a Service (SaaS)?",
                "options": [
                    "Software delivered over the internet",
                    "A type of computer hardware",
                    "A programming language"
                ],
                "answer": "Software delivered over the internet"
            },
            {
                "question": "Why is cloud security important?",
                "options": [
                    "To protect cloud data and resources",
                    "To change screen colors",
                    "To create HTML pages"
                ],
                "answer": "To protect cloud data and resources"
            },
            {
                "question": "What is one advantage of cloud computing?",
                "options": [
                    "Flexible access to computing resources",
                    "It eliminates the need for all programming",
                    "It removes the need for internet connections"
                ],
                "answer": "Flexible access to computing resources"
            }

        ]

    }


    return questions_by_career.get(
        career,
        questions_by_career["Software Development"]
    )


# ==================================================
# ASSESSMENT PAGE
# ==================================================

@app.route("/assessment")
def assessment():

    career_interest = session.get(
        "career_interest",
        "Backend Developer"
    )

    questions = get_assessment_questions(
        career_interest
    )

    return render_template(
        "assessment.html",
        questions=questions,
        career_interest=career_interest
    )

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
    # CALCULATE METRICS FOR READINESS DASHBOARD
    # ----------------------------------------------

    total_required = len(best_career["matching_skills"]) + len(best_career["missing_skills"])
    if total_required > 0:
        skill_coverage = round((len(best_career["matching_skills"]) / total_required) * 100)
    else:
        skill_coverage = 0

    # Overall Career Readiness Score (weighted: 40% best match + 35% assessment score + 25% skill coverage)
    overall_readiness = round(
        (0.40 * best_career["match"]) +
        (0.35 * percentage) +
        (0.25 * skill_coverage)
    )
    overall_readiness = max(0, min(100, overall_readiness))

    if overall_readiness >= 75:
        readiness_badge = "High Readiness"
    elif overall_readiness >= 50:
        readiness_badge = "Job Developing"
    else:
        readiness_badge = "Foundational"


    # ----------------------------------------------
    # DYNAMIC "WHY THIS CAREER MATCHES YOU" EXPLANATION
    # ----------------------------------------------

    match_explanation = generate_match_explanation(
        best_career,
        best_career["matching_skills"],
        career_interest,
        percentage
    )


    # ----------------------------------------------
    # ADVANCED SKILL GAP ANALYSIS
    # ----------------------------------------------

    skill_gaps = analyze_skill_gaps(best_career, user_skills)


    # ----------------------------------------------
    # CREATE ENHANCED PERSONALIZED ROADMAP
    # ----------------------------------------------

    roadmap = create_roadmap(
        best_career["missing_skills"],
        percentage,
        best_career
    )
    
    # ----------------------------------------------
    # CAREER READINESS SUMMARY
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
    # AI CAREER MENTOR (OPENAI INTEGRATION)
    # ----------------------------------------------

    ai_mentor = get_ai_career_mentor(
        name=user_name,
        career_interest=career_interest,
        assessment_score=percentage,
        best_career=best_career,
        matching_skills=best_career["matching_skills"],
        missing_skills=best_career["missing_skills"],
        user_skills=user_skills
    )
# ===============================================
# GET AI CAREER ADVICE
# ===============================================

    ai_advice = get_ai_career_advice(
        user_name,
        user_skills,
        career_interest,
        percentage,
        best_career
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

        readiness_message=readiness_message,
        ai_advice=ai_advice,

        # Dynamic Dashboard & Analytics Data
        skill_coverage=skill_coverage,

        overall_readiness=overall_readiness,

        readiness_badge=readiness_badge,

        match_explanation=match_explanation,

        skill_gaps=skill_gaps,

        total_required_skills=total_required,

        matching_count=len(best_career["matching_skills"]),

        missing_count=len(best_career["missing_skills"]),

        # AI Career Mentor Data
        ai_mentor=ai_mentor

    )
# ============================================================
# JOB OPPORTUNITIES
# ============================================================

@app.route("/jobs")
def jobs_page():

    user_skills = session.get("skills", [])

    matching_jobs = find_matching_jobs(
        user_skills,
        minimum_match=0
    )

    return render_template(
        "jobs.html",
        jobs=matching_jobs
    )


@app.route("/job/<int:job_id>")
def job_details(job_id):

    user_skills = session.get("skills", [])

    matching_jobs = find_matching_jobs(
        user_skills,
        minimum_match=0
    )

    selected_job = next(
        (
            job for job in matching_jobs
            if job["id"] == job_id
        ),
        None
    )

    if selected_job is None:
        return "Job not found", 404

    return render_template(
        "job_details.html",
        job=selected_job
    )

# ==================================================
# RUN APPLICATION
# ==================================================

if __name__ == "__main__":

    app.run(debug=True)