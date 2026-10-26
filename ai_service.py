import os
from pydantic import BaseModel, Field
from google import genai

# Setup the Gemini client
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

# Define predictable data structures
class Flashcard(BaseModel):
    id: int
    front: str = Field(description="The question, key term, or concept")
    back: str = Field(description="The definition or explanation")

class QuizQuestion(BaseModel):
    id: int
    question: str
    options: list[str] = Field(description="List of 4 distinct choices")
    correct_index: int = Field(description="Index of correct option (0, 1, 2, or 3)")
    explanation: str = Field(description="Why this option is correct")

class StudySet(BaseModel):
    summary: str
    flashcards: list[Flashcard]
    quiz: list[QuizQuestion]

def generate_study_material(notes_text: str) -> StudySet:
    prompt = f"""
    Analyze the following study notes and generate 5 clear revision flashcards 
    and 3 multiple-choice quiz questions.
    
    Notes:
    \"\"\"{notes_text}\"\"\"
    """
    
    response = client.models.generate_content(
        model='gemini-3.8-flash',
        contents=prompt,
        config={
            'response_mime_type': 'application/json',
            'response_schema': StudySet,
        },
    )
    return StudySet.model_validate_json(response.text)