import reflex as rx
import os
import json
import google.generativeai as genai
from dotenv import load_dotenv
import PyPDF2
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import re

load_dotenv()


class State(rx.State):
    immigration_status: str = ""
    immigration_info: str = ""
    current_status: str = ""
    next_steps: list = []
    required_documents: list = []
    additional_info: str = ""
    form_code: str = ""
    chat_history: list[tuple[str, str]] = [("", "Please enter a form code for your immigration document to get started.")]

    def get_formatted_immigration_info(self, immigration_info_json):
        if not immigration_info_json:
            return "No immigration information available."
        
        info = immigration_info_json
        self.current_status = f"Current Status: {info['current_status']}\n\n"
        print(info["required_documents_to_fill"])
        for step in info['next_steps']:
            self.next_steps.append(f"- {step['step']}: {step['description']}\n")
        try:
            for key in info['required_documents_to_fill']:
                self.required_documents.append(f"- {key}: {info['required_documents_to_fill'][key]}\n")
        except:
            self.required_documents = ["No required documents found."]

        self.additional_info += f"\nAdditional Information: {info['additional_info']}"

    def get_immigration_info(self, status):
        # Configure Gemini
        print("Immigration for Documentation", status)
        genai.configure(api_key=os.environ["GEMINI_API_KEY"])

        # Create the model
        generation_config = {
            "temperature": 0.7,
            "top_p": 0.95,
            "top_k": 40,
            "max_output_tokens": 8192,
        }

        model = genai.GenerativeModel(
            model_name="gemini-1.5-pro-002",
            generation_config=generation_config,
        )

        prompt = f"""
            Given the immigration status {status}, provide a detailed, step-by-step guide on the next steps in the immigration process or the required documentation.
        Format the response as a JSON string (without comments) with the following structure:
        {{
        "current_status": "Description of the current status",
        "next_steps": [
        {{
        "step": "Step 1",
        "description": "Detailed description of step 1"
        }},
        {{
        "step": "Step 2",
        "description": "Detailed description of step 2"
        }},
        ...
        ],
        "required_documents_to_fill": [
        "Document 1 needed to maintain immigration status or continue through a permanent residency/citizenship": "Description of Document 1 and detailed instructions on how to access this document",
        "Document 2 needed to maintain immigration status or continue through a permanent residency/citizenship ": "Description of Document 2 and detailed instructions on how to access this document",
        ...
        ],
        "required_documents_download_link": [
        "Document 1": "Download Blank Document Link or Example Document Download Link",
        "Document 2": "Download Blank Document Link or Example Document Download Link",
        ...
        ],
        "additional_info": "Any additional relevant information"
        }}
        """

        response = model.generate_content(prompt)
        self.immigration_info = response.text[7:-4]
        self.get_formatted_immigration_info(json.loads(self.immigration_info))

    def display_immigration_info(self, info):
        print(info)
        # print("\n=== Immigration Information ===\n")
        # print(f"Current Status: {info['current_status']}\n")
        
        # print("Next Steps:")
        # for i, step in enumerate(info['next_steps'], 1):
        #     print(f"{i}. {step['step']}")
        #     print(f"   {step['description']}\n")
        
        # print("Required Documents:")
        # for doc in info['required_documents']:
        #     print(f"- {doc}")
        
        # print(f"\nAdditional Information: {info['additional_info']}")

    def extract_form_code(self, input_pdf_path):
        try:
            with open(input_pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                # Extract text from the first page
                first_page_content = pdf_reader.pages[0].extract_text()
                
                # Use regex to find the form type
                form_match = re.search(r'Form\s+([A-Z]-\d+)', first_page_content)
                if form_match:
                    form_type = form_match.group(0)  # Full match (e.g., "Form I-90")
                    form_code = form_match.group(1)  # Just the code (e.g., "I-90")
                    # print(f"Form Type: {form_type}")
                    # print(f"Form Code: {form_code}")
                    return form_code
                else:
                    print("Form type not found in the document.")
                    return None
            
        except FileNotFoundError:
            print(f"Error: The file '{input_pdf_path}' was not found.")
        except PyPDF2.errors.PdfReadError:
            print(f"Error: '{input_pdf_path}' is not a valid PDF file or is encrypted.")
        except Exception as e:
            print(f"An unexpected error occurred: {str(e)}")
        
        return None

    # Example usage
    def help_with_document(self, instructions_pdf, form_code):
        # Configure Gemini
        genai.configure(api_key=os.environ["GEMINI_API_KEY"])
        
        sample_file = genai.upload_file(path=instructions_pdf, display_name=f"{form_code}_instructions")
        generation_config = {
            "temperature": 0.7,
            "top_p": 0.95,
            "top_k": 40,
            "max_output_tokens": 8192,
        }

        model = genai.GenerativeModel(
            model_name="gemini-1.5-pro-002",
            generation_config=generation_config,
        )
        chat = model.start_chat(history=[])

        # Initial message to set the context
        initial_prompt = f"You are an assistant helping with the instructions and questions for form {form_code}. The instructions have been uploaded as a PDF. Please provide a brief summary of the document."
        response = chat.send_message([sample_file, initial_prompt])
        self.chat_history += [(response.text, "")]


    def answer(self):
        file_out = ""
        documents_dir = 'Documents'
        for file in os.listdir(documents_dir):
            file_path = os.path.join(documents_dir, file)
            if file.endswith('.pdf') and self.form_code.lower() in file:
                file_out = file
                break
        try:
            instructions_pdf = os.path.join(documents_dir, file_out)
            self.help_with_document(instructions_pdf, self.form_code)
        except:
            pass