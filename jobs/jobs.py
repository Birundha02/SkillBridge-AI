import json
from pathlib import Path


def load_jobs():
    file_path = Path(__file__).parent / "jobs.json"

    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)


def calculate_match(user_skills, job_skills):
    user_skills = {
        skill.strip().lower()
        for skill in user_skills
    }

    job_skills = {
        skill.strip().lower()
        for skill in job_skills
    }

    if not job_skills:
        return 0

    matched_skills = user_skills.intersection(job_skills)

    match_percentage = (
        len(matched_skills) / len(job_skills)
    ) * 100

    return round(match_percentage)


def get_skill_details(user_skills, job_skills):
    user_skills_clean = {
        skill.strip().lower()
        for skill in user_skills
    }

    matched_skills = []
    missing_skills = []

    for skill in job_skills:

        if skill.strip().lower() in user_skills_clean:
            matched_skills.append(skill)
        else:
            missing_skills.append(skill)

    return matched_skills, missing_skills


def find_matching_jobs(user_skills, minimum_match=40):

    jobs = load_jobs()

    matching_jobs = []

    for job in jobs:

        match_percentage = calculate_match(
            user_skills,
            job["skills"]
        )

        if match_percentage >= minimum_match:

            matched_skills, missing_skills = get_skill_details(
                user_skills,
                job["skills"]
            )

            matching_jobs.append({
                "id": job["id"],
                "title": job["title"],
                "company": job["company"],
                "location": job["location"],
                "type": job["type"],
                "experience": job.get("experience", ""),
                "skills": job["skills"],
                "matched_skills": matched_skills,
                "missing_skills": missing_skills,
                "match_percentage": match_percentage
            })

    matching_jobs.sort(
        key=lambda job: job["match_percentage"],
        reverse=True
    )

    return matching_jobs


if __name__ == "__main__":

    test_skills = [
        "Python",
        "SQL",
        "Git"
    ]

    results = find_matching_jobs(test_skills)

    for job in results:

        print(
            f'{job["title"]} - '
            f'{job["company"]} - '
            f'{job["match_percentage"]}% match'
        )

        print(
            f'Matched skills: {job["matched_skills"]}'
        )

        print(
            f'Missing skills: {job["missing_skills"]}'
        )

        print()