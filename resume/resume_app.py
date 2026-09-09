import re

from flask import Blueprint, render_template, request, session, jsonify
from PyPDF2 import PdfReader
from docx import Document


# ==================================================
# RESUME BLUEPRINT
# ==================================================

resume_bp = Blueprint(
    "resume",
    __name__,
    url_prefix="/resume"
)


# ==================================================
# SKILL DATABASE
# ==================================================

SKILLS = [
    "python",
    "java",
    "c",
    "c++",
    "c#",
    "javascript",
    "html",
    "css",
    "react",
    "node.js",
    "flask",
    "django",
    "sql",
    "mysql",
    "mongodb",
    "excel",
    "power bi",
    "statistics",
    "machine learning",
    "deep learning",
    "pandas",
    "numpy",
    "tensorflow",
    "pytorch",
    "aws",
    "azure",
    "docker",
    "linux",
    "git",
    "github",
    "networking",
    "cybersecurity",
    "wireshark",
    "figma",
    "ui/ux"
]


# ==================================================
# PDF TEXT EXTRACTION
# ==================================================

def extract_pdf_text(file):
    """Extract text from a PDF resume."""

    text = ""

    reader = PdfReader(file)

    for page in reader.pages:
        page_text = page.extract_text()

        if page_text:
            text += page_text + "\n"

    return text


# ==================================================
# DOCX TEXT EXTRACTION
# ==================================================

def extract_docx_text(file):
    """Extract text from a DOCX resume."""

    document = Document(file)

    text = []

    for paragraph in document.paragraphs:
        text.append(paragraph.text)

    return "\n".join(text)


# ==================================================
# GENERAL RESUME TEXT EXTRACTION
# ==================================================

def extract_resume_text(file):
    """Extract resume text according to file type."""

    filename = file.filename.lower()

    if filename.endswith(".pdf"):
        return extract_pdf_text(file)

    elif filename.endswith(".docx"):
        return extract_docx_text(file)

    return ""


# ==================================================
# SKILL DETECTION
# ==================================================

def find_skills(text):
    """Find known skills mentioned in the resume."""

    text = text.lower()

    found_skills = []

    for skill in SKILLS:

        pattern = r"\b" + re.escape(skill) + r"\b"

        if re.search(pattern, text):
            found_skills.append(skill)

    return found_skills


# ==================================================
# BASIC INFORMATION EXTRACTION
# ==================================================

def extract_basic_information(text):
    """Extract basic information from the resume."""

    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]

    # Assume the first non-empty line is the name
    name = ""

    if lines:
        name = lines[0]

    # Look for education-related lines
    education = []

    education_keywords = [
        "b.tech",
        "btech",
        "b.e",
        "bachelor",
        "degree",
        "m.tech",
        "mtech",
        "master",
        "engineering",
        "university",
        "college"
    ]

    for line in lines:

        line_lower = line.lower()

        if any(keyword in line_lower for keyword in education_keywords):
            education.append(line)

    return {
        "name": name,
        "education": education[:5]
    }


# ==================================================
# RESUME ANALYZER PAGE
# ==================================================

@resume_bp.route("/", methods=["GET", "POST"])
def resume_home():

    if request.method == "POST":

        resume_file = request.files.get("resume")

        # ------------------------------------------
        # CHECK FILE
        # ------------------------------------------

        if not resume_file:
            return render_template(
                "resume.html",
                error="Please select a resume."
            )

        if resume_file.filename == "":
            return render_template(
                "resume.html",
                error="Please select a resume."
            )

        filename = resume_file.filename.lower()

        # ------------------------------------------
        # CHECK FILE TYPE
        # ------------------------------------------

        if not filename.endswith((".pdf", ".docx")):

            return render_template(
                "resume.html",
                error="Please upload a PDF or DOCX resume."
            )

        try:

            # --------------------------------------
            # EXTRACT TEXT
            # --------------------------------------

            resume_text = extract_resume_text(resume_file)

            if not resume_text.strip():

                return render_template(
                    "resume.html",
                    error="Could not extract text from this resume."
                )

            # --------------------------------------
            # FIND SKILLS
            # --------------------------------------

            skills = find_skills(resume_text)

            # --------------------------------------
            # EXTRACT BASIC INFORMATION
            # --------------------------------------

            information = extract_basic_information(resume_text)

            name = information["name"]
            education = information["education"]

            # --------------------------------------
            # SAVE DATA IN SESSION
            # --------------------------------------

            session["resume_name"] = name

            session["resume_education"] = education

            session["resume_skills"] = skills

            session["resume_text"] = resume_text

            # --------------------------------------
            # DISPLAY RESULTS
            # --------------------------------------

            return render_template(
                "resume.html",
                analyzed=True,
                name=name,
                education=education,
                skills=skills,
                resume_text=resume_text
            )

        except Exception as error:

            return render_template(
                "resume.html",
                error=f"Could not analyze the resume: {error}"
            )

    # ------------------------------------------
    # NORMAL PAGE LOAD
    # ------------------------------------------

    return render_template("resume.html")


# ==================================================
# AI DATA ENDPOINT
# ==================================================

@resume_bp.route("/data", methods=["GET"])
def resume_data():

    """
    Provides analyzed resume information
    in JSON format.

    The AI matching module can use this data.
    """

    data = {
        "name": session.get("resume_name", ""),
        "education": session.get("resume_education", []),
        "skills": session.get("resume_skills", []),
        "resume_text": session.get("resume_text", "")
    }

    return jsonify(data)