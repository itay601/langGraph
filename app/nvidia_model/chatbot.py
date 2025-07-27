from openai import OpenAI
import os
from dotenv import load_dotenv 


def nvidia_model(query : str):
    load_dotenv()
    NVIDIA_MODEL_KEY =os.environ["NVIDIA_MODEL_KEY"]

    client = OpenAI(
        base_url = "https://integrate.api.nvidia.com/v1",
        api_key = NVIDIA_MODEL_KEY
        )

    completion = client.chat.completions.create(
        model="nvidia/llama-3.1-nemotron-70b-instruct",
        messages=[{"role":"user","content": query}],
        temperature=0.5,
        top_p=1,
        max_tokens=1024,
        stream=True
        )

    full_response = ""
    for chunk in completion:
        if chunk.choices[0].delta.content is not None:
            content = chunk.choices[0].delta.content
            print(content, end="")
            full_response = full_response + content
       
    return full_response  


