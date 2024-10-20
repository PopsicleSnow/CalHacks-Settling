import requests

def fetch_courses(query):
    """Fetch training courses based on interests using external APIs"""
    coursera_api_url = "https://api.coursera.org/api/courses.v1?q=search&query={}"
    response = requests.get(coursera_api_url.format(query))
    courses = []

    if response.status_code == 200:
        elements = response.json().get('elements', [])
        for course in elements:
            courses.append({
                'name': course.get('name'),
                'link': f"https://www.coursera.org/learn/{course.get('slug')}",
                'duration': course.get('workload', 'Unknown')
            })
    return courses

def fetch_local_training_centers(location, interest):
    """Fetch local training centers using Google Maps API"""
    google_maps_api_url = "https://maps.googleapis.com/maps/api/place/textsearch/json?query={}+in+{}&key=YOUR_GOOGLE_MAPS_API_KEY"
    response = requests.get(google_maps_api_url.format(interest, location))
    centers = []

    if response.status_code == 200:
        results = response.json().get('results', [])
        for result in results:
             centers.append({
                'name': result.get('name'),
                'address': result.get('formatted_address')
            })
    return centers

def fetch_job_growth_data(career_path):
    """Fetch job market growth data using Bureau of Labor Statistics or similar API"""
    bls_api_url = "https://api.bls.gov/publicAPI/v2/timeseries/data/{}"
    # Example placeholder for BLS series id related to the career path
    response = requests.get(bls_api_url.format(career_path))
    growth_data = {}

    if response.status_code == 200:
        growth_data = response.json().get('Results', {}).get('series', [{}])[0]
    return growth_data
