import os
import json
import networkx as nx
import matplotlib.pyplot as plt
from dotenv import load_dotenv
from openai import AsyncOpenAI

load_dotenv()

class CareerPlanGraph:
    def __init__(self, user_profile):
        self.user_profile = user_profile
        self.graph = nx.DiGraph()
        self.client = AsyncOpenAI(api_key=os.environ["OPENAI_API_KEY"])

    async def generate_career_paths(self):
        """Use OpenAI to generate personalized career paths based on the user profile."""
        response = await self.client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a career guidance expert. Given the user's skills, education, desired career, and immigration status, provide a list of potential career paths, courses, and job opportunities for the next 1-5 years. The response should be in the following JSON format: {'years': [{'year': <year_number>, 'courses': [{'name': <course_name>}], 'jobs': [{'name': <job_name>}]}]}."},
                {"role": "user", "content": json.dumps(self.user_profile)}
            ],
            temperature=1.0
        )
        return response.choices[0].message.content

    async def parse_generated_plan(self, generated_plan):
        """Parse the AI-generated plan and add nodes to the graph accordingly."""
        try:
            plan = json.loads(generated_plan)
            for year in plan.get("years", []):
                year_label = f"Year {year['year']}"
                self.graph.add_node(year_label, layer=year['year'])

                for course in year.get("courses", []):
                    course_node = f"{year_label}: {course['name']}"
                    self.graph.add_node(course_node, layer=year['year'])
                    self.graph.add_edge(year_label, course_node)

                for job in year.get("jobs", []):
                    job_node = f"{year_label}: {job['name']}"
                    self.graph.add_node(job_node, layer=year['year'])
                    self.graph.add_edge(year_label, job_node)

        except json.JSONDecodeError:
            print("Error: Unable to parse the generated plan. The response was not a valid JSON.")
            print("Generated Response:", generated_plan)

    async def generate_career_plan(self):
        """Generate and create the career graph based on user profile and OpenAI suggestions."""
        generated_plan = await self.generate_career_paths()
        await self.parse_generated_plan(generated_plan)

    def draw_graph(self):
        """Visualize the generated career plan graph and save it as a PNG file."""
        pos = nx.multipartite_layout(self.graph, subset_key="layer")

        # Set up plot
        plt.figure(figsize=(15, 10))
        nx.draw(self.graph, pos, with_labels=True, node_color="skyblue", node_size=3000, font_size=10, font_color="black", edge_color="gray")
        plt.title("Career Path Graph by Year", fontsize=16)

        # Define the path for assets folder located outside of the current directory
        assets_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets")
        
        # Check if assets directory exists, create it if it doesn't
        if not os.path.exists(assets_dir):
            os.makedirs(assets_dir)

        # Save the figure as a PNG file in the assets directory
        graph_file_path = os.path.join(assets_dir, "career_plan_graph.png")
        plt.savefig(graph_file_path)
        print(f"Career path graph saved to {graph_file_path}")

        # Clear the plot after saving to avoid overlapping on the next plot
        plt.clf()

# Testing with a sample user profile
if __name__ == "__main__":
    user_profile = {
        "skills": ["Art", "Music"],
        "education": "Bachelor in Music Theory",
        "desired_career": "Music",
        "immigration_status": "Student Visa",
        "years_in_plan": 5
    }

    career_plan_graph = CareerPlanGraph(user_profile)
    import asyncio
    asyncio.run(career_plan_graph.generate_career_plan())
    career_plan_graph.draw_graph()
