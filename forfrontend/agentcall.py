from fastapi import FastAPI
from pydantic import BaseModel
from agents import *

class prompt(BaseModel):
    PROMPT: str

app = FastAPI()

@app.post("/cadchat/")
def chat_cad(Prompt:prompt):
    result = designer.initiate_chat(cad_coder, message=Prompt)
    return result

