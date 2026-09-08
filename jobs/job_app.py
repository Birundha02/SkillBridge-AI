from flask import Flask, render_template
from jobs import find_matching_jobs

app = Flask(
    __name__,
    template_folder="."
)


# Temporary user skills
# Later, these will come from the user's SkillSync profile.
USER_SKILLS = [
    "Python",
    "SQL",
    "Git"
]


@app.route("/")
def jobs_page():

    matching_jobs = find_matching_jobs(
        USER_SKILLS
    )

    return render_template(
        "jobs.html",
        jobs=matching_jobs
    )


@app.route("/job/<int:job_id>")
def job_details(job_id):

    matching_jobs = find_matching_jobs(
        USER_SKILLS,
        minimum_match=0
    )

    selected_job = None

    for job in matching_jobs:

        if job["id"] == job_id:
            selected_job = job
            break

    if selected_job is None:
        return "Job not found", 404

    return render_template(
        "job_details.html",
        job=selected_job
    )


if __name__ == "__main__":
    app.run(
        debug=True,
        port=5001
    )