import time

class JobDescription:
    def __init__(self, title, skills, experience_required):
        self.title = title
        self.skills = set(skills)
        self.experience_required = experience_required

class ConsultantProfile:
    def __init__(self, id, name, skills, experience):
        self.id = id
        self.name = name
        self.skills = set(skills)
        self.experience = experience

    def calculate_match_score(self, job: JobDescription):
        skill_overlap = len(self.skills.intersection(job.skills))
        experience_score = min(self.experience, job.experience_required)
        return round(skill_overlap * 0.7 + experience_score * 0.3, 2)

def rank_consultants(job_description, consultants):
    scored = [
        {
            "profile": c,
            "score": c.calculate_match_score(job_description)
        }
        for c in consultants
    ]
    return sorted(scored, key=lambda x: x["score"], reverse=True)

def print_results(job_description, ranked_consultants):
    print("\nMatching Job Description: {}\n".format(job_description.title))
    print("Top 3 Consultant Matches:\n")
    
    for i, entry in enumerate(ranked_consultants[:3], start=1):
        profile = entry["profile"]
        score = entry["score"]
        print(f"{i}. {profile.name} (ID: {profile.id})")
        print(f"   Skills: {', '.join(profile.skills)}")
        print(f"   Experience: {profile.experience} years")
        print(f"   Match Score: {score}\n")
        time.sleep(0.5)

def send_email_simulation():
    print("Sending email to AR requestor with top 3 matches...")
    time.sleep(1.5)
    print("Email sent successfully.\n")

def main():
    jd = JobDescription(
        title="Senior Python Developer",
        skills=["python", "fastapi", "docker", "postgresql", "git"],
        experience_required=4
    )

    consultants = [
        ConsultantProfile("C101", "Alice", ["python", "flask", "docker"], 5),
        ConsultantProfile("C102", "Bob", ["java", "spring"], 3),
        ConsultantProfile("C103", "Charlie", ["python", "fastapi", "docker", "git"], 4),
        ConsultantProfile("C104", "David", ["python", "fastapi"], 2),
        ConsultantProfile("C105", "Eva", ["python", "fastapi", "docker", "postgresql", "git"], 6)
    ]

    ranked = rank_consultants(jd, consultants)
    print_results(jd, ranked)
    send_email_simulation()

if __name__ == "__main__":
    main()
