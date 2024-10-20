import google.generativeai as genai
import os
import career_resources
from dotenv import load_dotenv
import re
import random
import requests

# Loading the environment variables
load_dotenv()

# Configuring the Gemini API
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

# Dummy user data for testing purposes
user_profiles = {
    "dummy_user": {
        "skills": ["Python", "Data Analysis"],
        "education": ["Computer Science"],
        "desired_industry": "AI",
        "immigration_status": "Permanent Resident",
        "career_goals": "Data Science"
    }
}

def load_user_profile(user_id):
    """Load user data (dummy implementation for testing)"""
    return user_profiles.get(user_id, None)

def recommend_career_path(user_data):
    skills = user_data.get('skills', [])
    education = user_data.get('education', [])
    desired_industry = user_data.get('desired_industry', '')
    immigration_status = user_data.get('immigration_status', '')
    career_goals = user_data.get('career_goals', '')

    # AI model for personalized career recommendations
    generation_config = {
        "temperature": 1,
        "top_p": 0.95,
        "top_k": 40,
        "max_output_tokens": 8192,
        "response_mime_type": "text/plain",
    }

    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash-002",
        generation_config=generation_config,
    )

    prompt = (
        f"Given the user's skills: {skills}, education: {education}, desired industry: "
        f"{desired_industry}, immigration status: {immigration_status}, and career goals: {career_goals}, "
        f"please suggest potential career paths. Provide as many possible career options as are reasonable."
    )
    response = model.generate_content(prompt)

    # Extracting career paths from the response using regex or text processing
    career_paths = set()
    if response and hasattr(response, '_result') and response._result.candidates:
        for candidate in response._result.candidates:
            generated_text = candidate.content.parts[0].text

            # Extracting career paths from generated text
            lines = generated_text.splitlines()
            for line in lines:
                # Assuming valid career paths are listed as bullet points
                if re.match(r"^\s*[\*\-\•]\s*(.+)", line):
                    career_name = re.search(r"^\s*[\*\-\•]\s*(.+)", line)
                    if career_name:
                        career_paths.add(career_name.group(1).strip())

    return list(career_paths)

def generate_career_growth_plan(user_data, career_paths, plan_years=5):
    """Generate a detailed career growth plan for the user"""
    career_growth_plan = {}
    skills = user_data.get('skills', [])
    weekly_hours_available = user_data.get('weekly_hours_available', 10)

    for career in career_paths:
        # Fetching the missing career skills for each career
        required_skills = get_required_skills_for_career(career)
        missing_skills = [skill for skill in required_skills if skill not in skills]

        # Suggesting courses to bridge skill gaps (limit to top 5 courses)
        suggested_courses = []
        for skill in missing_skills:
            fetched_courses = career_resources.fetch_courses(skill)
            suggested_courses.extend(fetched_courses[:5])

        # Dividing growth plan into years
        growth_plan = {}
        for year in range(1, plan_years + 1):
            if year == 1:
                # Short-term goals for year 1: take courses and acquire foundational skills
                growth_plan[f'Year {year}'] = {
                    'courses': [f"Take course: {course['name']}" for course in suggested_courses[:min(3, len(suggested_courses))]],
                    'jobs': [f"Apply for internship or entry-level positions in {career}"],
                    'hours_per_week': weekly_hours_available
                }
            else:
                # Long-term goals for subsequent years
                growth_plan[f'Year {year}'] = {
                    'courses': [f"Take advanced course: {course['name']}" for course in suggested_courses[min(3, len(suggested_courses)):]],
                    'jobs': [f"Apply for mid-level positions in {career}", f"Work on projects related to {career}"],
                    'hours_per_week': weekly_hours_available
                }
        
        # Adding fallback plans based on hypothetical changes in immigration status
        fallback_plans = generate_fallback_plans(user_data, career)

        # Adding the career plan with fallback plans
        career_growth_plan[career] = {
            'growth_plan': growth_plan,
            'fallback_plans': fallback_plans
        }

    return career_growth_plan

def get_required_skills_for_career(career):
    """Placeholder function to fetch required skills using an external AI"""
    generation_config = {
        "temperature": 0.8,
        "top_p": 0.9,
        "max_output_tokens": 1000,
    }

    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash-002",
        generation_config=generation_config,
    )

    prompt = f"List all skills required to be successful in a career as a {career}."
    response = model.generate_content(prompt)

    skills = []
    if response and hasattr(response, '_result') and response._result.candidates:
        generated_text = response._result.candidates[0].content.parts[0].text
        skills = [skill.strip() for skill in generated_text.splitlines() if skill.strip()]

    return skills

def generate_fallback_plans(user_data, career):
    """Generate fallback plans in case of major changes in user's situation"""
    immigration_status = user_data.get('immigration_status', '')

    fallback_plans = {
        'if_visa_rejected': f"Consider remote jobs in {career} that allow working from home or from a home country.",
        'if_course_incomplete': f"Take alternative online courses for {career}, focusing on free resources to catch up.",
        'if_financial_issues': f"Consider part-time freelance projects in {career} to continue progressing."
    }

    return fallback_plans

# Testing the code
user_id = "dummy_user"
user_data = load_user_profile(user_id)

if user_data:
    career_paths = recommend_career_path(user_data)
    career_growth_plan = generate_career_growth_plan(user_data, career_paths)

    # Displaying the results
    print("\nCareer Recommendations:\n")
    for career in career_paths:
        print(f"- {career}")

    print("\nCareer Growth Plan:\n")
    for career, plan in career_growth_plan.items():
        print(f"\nCareer: {career}")
        for year, details in plan['growth_plan'].items():
            print(f"  {year}:")
            print("    Courses:")
            for course in details['courses']:
                print(f"      - {course}")
            print("    Jobs:")
            for job in details['jobs']:
                print(f"      - {job}")
            print(f"    Hours per week: {details['hours_per_week']}")
        print("  Fallback Plans:")
        for key, fallback in plan['fallback_plans'].items():
            print(f"    - {key}: {fallback}")
else:
    print("User profile not found")
