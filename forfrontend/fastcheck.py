from fastapi import FastAPI

#instance of FASTAPI
app = FastAPI()

#path operation decorator to link/agents
@app.get("/agents/{agent}") #path parameter can be passed here
async def agent_selection(agent: int): #path operation function
    return {"coder": agent}

#run development server with- development mode
# fastapi dev fastchekc.py
