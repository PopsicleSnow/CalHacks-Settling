import firebase_admin
from firebase_admin import credentials, firestore
import google.generativeai as genai
import os
import career_resources
from dotenv import load_dotenv
import re
import reflex as rx

# Loading the environment variables
load_dotenv()

class State(rx.state):

    # Initialize Firebase if it hasn't been done yet
    if not firebase_admin._apps:
        # Load Firebase credentials
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # Construct the path to the credentials file
        cred_path = os.path.join(current_dir, "..", "firebase-credentials.json")
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)

    # Initialize Firestore client
    db = firestore.client()

    # Configuring the Gemini API
    genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

    # Load User Profile from Firebase
    def load_user_profile(user_id):
        """Load user data from Firebase Firestore"""
        try:
            doc_ref = db.collection('users').document(user_id)
            doc = doc_ref.get()
            if doc.exists:
                print(f"User profile found for '{user_id}'.")
                return doc.to_dict()
            else:
                print(f"User profile not found for '{user_id}'.")
        except Exception as e:
            print(f"Error loading user profile: {e}")
        return None

    # Save Career Growth Plan to Firebase
    def save_career_growth_plan(user_id, career_growth_plan):
        """Save career growth plan for the current user to Firebase Firestore"""
        db.collection('career_growth_plans').document(user_id).set(career_growth_plan)

    # Load Career Growth Plan from Firebase
    def load_career_growth_plan(user_id):
        """Load the user's career growth plan from Firebase Firestore"""
        doc_ref = db.collection('career_growth_plans').document(user_id)
        doc = doc_ref.get()
        if doc.exists:
            return doc.to_dict()
        return {}

    # Generate Career Recommendations using Logic and AI
    def recommend_career_path(user_data):
        career_paths = []
        skills = user_data.get('skills', [])
        education = user_data.get('education', [])
        desired_industry = user_data.get('desired_industry', '')
        immigration_status = user_data.get('immigration_status', '')

        # Logic-based recommendations
        if "Computer Science" in education:
            if "Data Analysis" in skills:
                career_paths.append("Data Scientist")
                career_paths.append("Business Analyst")
            if "Web Development" in skills:
                career_paths.append("Front-End Developer")

        if desired_industry == "AI":
            career_paths.append("Machine Learning Engineer")

        # Using AI model for personalized recommendations
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
            f"{desired_industry}, and immigration status: {immigration_status}, suggest potential career paths."
        )
        response = model.generate_content(prompt)

        # Extracting generated content from response
        if response and hasattr(response, '_result') and response._result.candidates:
            for candidate in response._result.candidates:
                generated_text = candidate.content.parts[0].text

                # Use regex or text processing to extract only valid career paths
                lines = generated_text.splitlines()
                for line in lines:
                    if re.match(r"^\*\s+\*\*(.+?)\*\*:", line):
                        career_name = re.search(r"\*\*(.+?)\*\*", line)
                        if career_name:
                            career_paths.append(career_name.group(1).strip())

        # Remove duplicates and clean the list of career paths
        career_paths = list(set(career_paths))

        return career_paths

    # Generate Short and Long-Term Career Growth Plans
    def generate_career_growth_plan(user_data, career_paths):
        """Generate short and long-term career growth plans"""
        career_growth_plan = {}
        skills = user_data.get('skills', [])

        for career in career_paths:
            # Fetching the missing career skills for each career
            required_skills = get_required_skills_for_career(career)
            missing_skills = [skill for skill in required_skills if skill not in skills]

            # Suggesting courses to bridge skill gaps (limit to top 5 courses)
            suggested_courses = []
            for skill in missing_skills:
                fetched_courses = career_resources.fetch_courses(skill)
                suggested_courses.extend(fetched_courses[:5])

            # Creating the action plan
            action_plan = {
                'short_term_goals': [f"Take course: {course['name']}" for course in suggested_courses],
                'long_term_goals': [f"Get an entry-level job in {career}"]
            }
            career_growth_plan[career] = action_plan

        return career_growth_plan

    # Placeholder Function for Career Skills Requirements
    def get_required_skills_for_career(career):
        """Placeholder function to get required skills for a given career"""
        career_skill_mapping = {
            "Data Scientist": ["Python", "Data Analysis", "Machine Learning"],
            "Business Analyst": ["Excel", "Data Analysis", "Business Modeling"],
            "Front-End Developer": ["HTML", "CSS", "JavaScript"],
            "Machine Learning Engineer": ["Python", "TensorFlow", "Deep Learning"]
        }
        return career_skill_mapping.get(career, [])

    def add_test_user_profile():
        """Add a test user profile to Firestore for testing purposes"""
        user_id = "random_user_id"
        user_data = {
            "skills": ["Python", "Data Analysis"],
            "education": ["Computer Science"],
            "desired_industry": "AI",
            "immigration_status": "Permanent Resident"
        }
        db.collection('users').document(user_id).set(user_data)
        print(f"Test user profile for '{user_id}' added to Firestore.")

    def delete_user_profile(user_id):
        """Delete user profile from Firebase Firestore"""
        try:
            db.collection('users').document(user_id).delete()
            print(f"User profile for '{user_id}' deleted successfully.")
        except Exception as e:
            print(f"Error deleting user profile: {e}")

    # Add the test user profile before attempting to load it
    #add_test_user_profile()

    # Main Execution
    user_id = "random_user_id"
    user_data = load_user_profile(user_id)

    if user_data:
        # Load existing growth plan if available
        career_growth_plan = load_career_growth_plan(user_id)
        if not career_growth_plan:
            # If no existing plan, generate new ones
            career_paths = recommend_career_path(user_data)
            career_growth_plan = generate_career_growth_plan(user_data, career_paths)
            # Save the generated career growth plan to Firebase
            save_career_growth_plan(user_id, career_growth_plan)

        # Displaying the results
        print("\nCareer Recommendations:\n")
        for career in career_growth_plan.keys():
            print(f"- {career}")

        print("\nCareer Growth Plan:\n")
        for career, plan in career_growth_plan.items():
            print(f"\nCareer: {career}")
            print("Short-Term Goals:")
            for goal in plan['short_term_goals']:
                print(f"  - {goal}")
            print("Long-Term Goals:")
            for goal in plan['long_term_goals']:
                print(f"  - {goal}")
        delete_user_profile(user_id)

    else:
        print("User profile not found")
