import os
import reflex as rx
import google.generativeai as genai
from apify_client import ApifyClient
import warnings
warnings.filterwarnings("ignore")
import json
from dotenv import load_dotenv
load_dotenv()

# Initialize the ApifyClient with your API token
client = ApifyClient(os.environ["APIFY_API_KEY"])

# Configure Gemini
genai.configure(api_key=os.environ["GEMINI_API_KEY"])


class State(rx.State):
    job_results: str = ""
    def run_indeed_scraper(self, skills, zipcode):
        # Join skills into a query string for the position
        skill_query = " OR ".join(skills)
        # Prepare the run input
        run_input = {
            "country": "US",
            "location": zipcode,
            "position": skill_query,
            "maxItems": 20,
            "includeUnfilteredResults": True
        }
        
        # Run the Indeed scraper
        print(run_input)
        run = client.actor("misceres/indeed-scraper").call(run_input=run_input)
        # Fetch job postings from the default dataset
        recommended_jobs = []
        for item in client.dataset(run["defaultDatasetId"]).iterate_items():
            recommended_jobs.append(item)
        print(recommended_jobs)
        
        return recommended_jobs

    def format_jobs_for_gemini(self, recommended_jobs):
        job_strings = []
        for job in recommended_jobs:
            job_string = json.dumps({
                'positionName': job.get('positionName', 'N/A'),
                'salary': job.get('salary', 'N/A'),
                'description': job.get('description', 'N/A'),
                'company': job.get('company', 'N/A'),
                'location': job.get('location', 'N/A'),
                'url': job.get('url', 'N/A')
            })
            job_strings.append(job_string)
        return '#######'.join(job_strings)

    def get_gemini_recommendations(self, formatted_job_string, education, immigration_status):
        # Create the model
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

        chat_session = model.start_chat(history=[])

        prompt = f"""The following is an aggregation JSON file of all potential jobs for an applicant. Each job is sepaarated by '#######'.
        The applicant's education is {education} and their current immigration status is {immigration_status}. 
        Out of these jobs find the top 10 jobs that are the most preferable for the given candidate given the education level and immigration status above. 
        For each chosen job, make sure the jobs are outputted in a nice bulleted paragraph, not bolded format with the following job title ('Job Title'), the salary ('Salary'), the company ('Company'), the location ('Location'), and the job URL ('URL'). 
        Put two '\n' after every job to create two new lines for every job recommendation and remove any '*' from response (right after the job url). Don't include any other extra information in the output. 

        Jobs: {formatted_job_string}"""

        response = chat_session.send_message(prompt)
        return response.text

    def get_job_postings(self, skills, zipcode, education, immigration_status):
        if self.job_results != "":
            return
        print("Skills", skills)
        print("Zipcode", zipcode)
        print("Education", education)
        print("Immigration", immigration_status)
        scraped_jobs = self.run_indeed_scraper(skills, zipcode)
        formatted_job_string = self.format_jobs_for_gemini(scraped_jobs)
        recommended_jobs = self.get_gemini_recommendations(formatted_job_string, education, immigration_status)
        # return recommended_jobs
        print("Recommended jobs:", recommended_jobs)
        new_recommended_jobs = []
        for job in recommended_jobs.split("\n"):
            if job:
                new_recommended_jobs.append(job)
        self.job_results = new_recommended_jobs
        




