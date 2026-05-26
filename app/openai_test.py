import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()


client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

messages = [
    {
        "role": "system",
        "content": "You are a helpful assistant that can call tools."
    },
    {
        "role": "user",
        "content": "Give me a list of available AI courses."
    }
]

response = client.chat.completions.create(
    model="gpt-4.1-mini",
    messages=messages,
    temperature=0.7
)
print(response.choices[0].message.content)

from pydantic import BaseModel, Field
from typing import List, Optional, Literal

class GetCoursesRequest(BaseModel):
    topics: List[str] = Field(..., description="List of course topics to retrieve")
    max_cost: float = Field(0.0, ge=0, description="Maximum budget for the courses")
    difficulty: Optional[Literal["beginner", "intermediate", "advanced"]] = Field(
        None,
        description="Optional difficulty level of the courses"
    )



print(GetCoursesRequest.model_json_schema())
def make_get_courses_tool():
    return {
        "type": "function",
        "function": {
            "name": "get_courses",
            "description": "Retrieve a list of courses that match given topics.",
            "parameters": GetCoursesRequest.model_json_schema(),
        },
    }

print(make_get_courses_tool())
