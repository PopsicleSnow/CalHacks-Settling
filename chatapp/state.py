import reflex as rx
from openai import AsyncOpenAI
import google.generativeai as genai
import os
import json
from dotenv import load_dotenv

load_dotenv()

class State(rx.State):
    # The current question being asked
    question: str
    prev_question: str = ""

    immigration_status: str = ""
    when_moved: str = ""
    education: str = ""
    skills: list[str] = [""]
    location: str = ""

    # Greeting message for the user
    greeting_message: str = "Hello! I’m here to assist you with your personalized immigration experience. I will ask you some questions in regards to your immigration process and these responses will be used to create a personalized career and documentation application for you. I’m really excited to help and welcome you to the U.S.A! 😊 Let's begin!"

    questions: list[str] = [
        "What's your current immigration status?",
        "What date did you come to the US?",
        "What is your education level?",
        "What skills do you have?",
        "What is your current zipcode?"
    ]

    # Keep track of the chat history as a list of (question, answer) tuples.
    chat_history: list[tuple[str, str]] = [("", greeting_message), ("", "What's your current immigration status?")]

    # Index of the current question
    current_question_index: int = 0

    async def verify_input(self, question: str, answer: str) -> tuple[bool, str]:
        client = AsyncOpenAI(api_key=os.environ["OPENAI_API_KEY"])

        response = await client.chat.completions.create(
            model="gpt-4",  # Use the appropriate model
            messages=[
                {"role": "system", "content": "You are a very understanding and empathetic AI assistant verifying user input for an immigration survey. Respond with only the word 'valid' verbatim if the input is appropriate for the question, otherwise explain to the user what they should type instead very empathetically and very clearly. Assume these individuals don't speak English as a first language."},
                {"role": "user", "content": f"Question: {question}\nUser's answer: {answer}\nIs this a valid response?"}
            ],
            temperature=1.2
        )
        
        verification_result = response.choices[0].message.content
        is_valid = verification_result.lower().startswith("valid")
        return is_valid, verification_result
    
    def reset_chat(self):
        self.question = ""
        self.prev_question = ""
        self.immigration_status = ""
        self.when_moved = ""
        self.education = ""
        self.skills = [""]
        self.location = ""
        self.chat_history = [("", self.greeting_message), ("", "What is your updated immigration status?")]
        self.current_question_index = 0

    async def get_skills(self, skills_text: str) -> list[str]:
        client = AsyncOpenAI(api_key=os.environ["OPENAI_API_KEY"])

        response = await client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an advanced AI assistant. The user has listed skills as part of a survey. Your task is to extract the individual skills from their response and output them as an array of skills."},
                {"role": "user", "content": f"Extract the skills from the following text: {skills_text}, in an array"}
            ],
            temperature=1.2
        )
        skills_array = json.loads(response.choices[0].message.content)
        return skills_array

    async def answer(self):
        client = AsyncOpenAI(api_key=os.environ["OPENAI_API_KEY"])

        if not self.question:
            return
        
        # Verify user input
        validity, interpretation = await self.verify_input(self.questions[self.current_question_index], self.question)
        if not validity:
            # self.chat_history.append((self.questions[self.current_question_index], self.question))  # Store invalid response
            self.chat_history.append((self.question, ""))
            self.chat_history.append(("", interpretation))  # Add the feedback on invalid input
            self.question = ""
            yield
            return

        # Add user's valid response to chat history
        self.chat_history.append((self.question, ""))

        # Prepare the next question or finish the survey
        if self.current_question_index < len(self.questions) - 1:
            next_question = self.questions[self.current_question_index + 1]
            system_message = f"Ask the user: {next_question}"
        else:
            system_message = "Thank the user for completing the survey and provide a brief summary of their responses."

        # AI generates a response for the next question or closing
        session = await client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a very understanding, compassionate, and empathetic AI assistant conducting an immigration survey. Provide helpful responses based on the user's answers."},
                {"role": "user", "content": f"User's response to '{self.questions[self.current_question_index]}': {self.question}"},
                {"role": "system", "content": system_message}
            ],
            temperature=0.7,
            stream=True,
        )

        # Store the chatbot's response
        answer = ""

        # Clear the question input
        self.prev_question = self.question
        self.question = ""
        yield  # Clear the frontend input before continuing

        async for item in session:
            if hasattr(item.choices[0].delta, "content"):
                if item.choices[0].delta.content is None:
                    break
                answer += item.choices[0].delta.content
                self.chat_history[-1] = (
                    self.chat_history[-1][0],
                    answer,
                )
                yield

        # Update state based on user responses
        if not self.current_question_index:
            self.immigration_status = self.prev_question
        elif self.current_question_index == 1:
            self.when_moved = self.prev_question
        elif self.current_question_index == 2:
            self.education = self.prev_question
        elif self.current_question_index == 3:
            self.skills = await self.get_skills(answer)
        else:
            self.location = self.prev_question

        # Move to the next question
        self.current_question_index += 1

        # If the survey is finished, disable further input
        if self.current_question_index >= len(self.questions):
            self.current_question_index = -1
            