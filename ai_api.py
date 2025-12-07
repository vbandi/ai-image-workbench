"""
AI API module for prompt enhancement using OpenAI.
"""
import openai
import os
from typing import Optional


def enhance_prompt(prompt: str, directions: Optional[str] = None) -> str:
    """
    Enhance the prompt using OpenAI API, with optional directions.
    
    Args:
        prompt: The original prompt to enhance
        directions: Optional specific directions for enhancement
        
    Returns:
        Enhanced prompt string
        
    Raises:
        Exception: If OpenAI API call fails or returns no content
    """
    if not prompt.strip():
        raise ValueError("Prompt cannot be empty")

    client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    
    system_message = ("You are a creative assistant that enhances user prompts for an image generation model. "
                     "Add more visual details to the prompt, making it more descriptive and imaginative. "
                     "The enhanced prompt should be a single paragraph.")
    
    user_message = prompt
    if directions:
        user_message = f"Enhance the following prompt with these directions: '{directions}'\n\nPrompt: '{prompt}'"

    response = client.chat.completions.create(
        model="gpt-5.1",
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message}
        ]
    )
    
    content = response.choices[0].message.content
    if not content:
        raise ValueError("No content received from OpenAI")
        
    return content.strip()