import reflex as rx
import os
import json
import google.generativeai as genai
from dotenv import load_dotenv
import PyPDF2
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import io
import re

load_dotenv()


class State(rx.State):
    immigration_status: str = ""
    immigration_info: dict = {}
    form_code: str = ""
    chat_history: list = []

# Configure Gemini
genai.configure(api_key=os.environ["GEMINI_API_KEY"])

def get_immigration_info(status):
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
    Format the response as a JSON object with the following structure:
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
    return response.text

def display_immigration_info(info):
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

def extract_form_code(input_pdf_path):
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
def help_with_document(instructions_pdf, form_code):
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
    print("Assistant: " + response.text)

    # Start the conversation loop
    while True:
        user_input = input("\nYou: ")
        if user_input.lower() in ['exit', 'quit', 'bye']:
            print("Assistant: Goodbye! If you have any more questions, feel free to ask.")
            break

        # Send user's message and get response
        response = chat.send_message(user_input)
        print("Assistant: " + response.text)



def main():
    status = input("Enter your immigration status: ")
    info = get_immigration_info(status)
    display_immigration_info(info)
    # read_and_parse_pdf("../Documents/i-129.pdf")
    # input_pdf_path = '../test_Documents/i-485-test.pdf'
    # form_code = extract_form_code(input_pdf_path)
    form_code = input("What form do you need help with?")
    file_out = ""
    documents_dir = '../Documents'
    for file in os.listdir(documents_dir):
        file_path = os.path.join(documents_dir, file)
        if file.endswith('.pdf') and form_code.lower() in file:
            file_out = file
            break
    instructions_pdf = os.path.join(documents_dir, file_out)
    help_with_document(instructions_pdf, form_code)



if __name__ == "__main__":
    main()
