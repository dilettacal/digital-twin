"""AI service for chat completions."""
from typing import List, Dict
from fastapi import HTTPException
from botocore.exceptions import ClientError
from app.core.config import (
    AI_PROVIDER,
    bedrock_client,
    openai_client,
    BEDROCK_MODEL_ID,
    OPENAI_MODEL
)
from app.core.context import prompt


def call_bedrock(conversation: List[Dict], user_message: str) -> str:
    """Call AWS Bedrock with conversation history."""

    # Build messages in Bedrock format
    messages = []

    # Add system prompt as first user message (Bedrock convention)
    messages.append({
        "role": "user",
        "content": [{"text": f"System: {prompt()}"}]
    })

    # Add conversation history (limit to last 10 exchanges to manage context)
    for msg in conversation[-20:]:  # Last 10 back-and-forth exchanges
        messages.append({
            "role": msg["role"],
            "content": [{"text": msg["content"]}]
        })

    # Add current user message
    messages.append({
        "role": "user",
        "content": [{"text": user_message}]
    })

    try:
        # Call Bedrock using the converse API
        response = bedrock_client.converse(
            modelId=BEDROCK_MODEL_ID,
            messages=messages,
            inferenceConfig={
                "maxTokens": 2000,
                "temperature": 0.7,
                "topP": 0.9
            }
        )

        # Extract the response text
        return response["output"]["message"]["content"][0]["text"]

    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'ValidationException':
            # Handle message format issues
            print(f"Bedrock validation error: {e}")
            raise HTTPException(status_code=400, detail="Invalid message format for Bedrock")
        elif error_code == 'AccessDeniedException':
            print(f"Bedrock access denied: {e}")
            raise HTTPException(status_code=403, detail="Access denied to Bedrock model")
        else:
            print(f"Bedrock error: {e}")
            raise HTTPException(status_code=500, detail=f"Bedrock error: {str(e)}")


def call_openai(conversation: List[Dict], user_message: str) -> str:
    """Call OpenAI API with conversation history."""

    # Build messages in OpenAI format
    messages = []

    # Add system prompt
    messages.append({
        "role": "system",
        "content": prompt()
    })

    # Add conversation history (limit to last 20 messages to manage context)
    for msg in conversation[-20:]:
        messages.append({
            "role": msg["role"],
            "content": msg["content"]
        })

    # Add current user message
    messages.append({
        "role": "user",
        "content": user_message
    })

    try:
        # Call OpenAI API
        response = openai_client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=messages,
            max_tokens=2000,
            temperature=0.7
        )

        # Extract the response text
        return response.choices[0].message.content

    except Exception as e:
        print(f"OpenAI error: {e}")
        raise HTTPException(status_code=500, detail=f"OpenAI error: {str(e)}")


def get_ai_response(conversation: List[Dict], user_message: str) -> str:
    """Get AI response from configured provider."""
    if AI_PROVIDER == "openai":
        return call_openai(conversation, user_message)
    else:
        return call_bedrock(conversation, user_message)
