from fastapi import FastAPI, Request
from mygraph_v2 import MyAgent
from fastapi.responses import StreamingResponse
import uvicorn
import asyncio
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import os
import dotenv
dotenv.load_dotenv()

workflow = MyAgent().compile_graph()
app = FastAPI(title = 'Fat.ai', 
              description = "My personal agentic AI, whos capable of answering the user's questions about me and also execute task like sendind and email to my mail, notifying me about the person enquired about me. ")

async def stream_response(input: dict):
    state = {'user_input': input.get('user_input', '')}
    thread_id = input.get('thread_id', None)
    if thread_id:
        for chunk in workflow.stream(state, config={'configurable': {'thread_id': thread_id}}):
            if 'invoke_llm' in chunk:
                yield chunk['invoke_llm']['llm_response']
            await asyncio.sleep(0)

class SecretKeyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        """
        Middleware to check if the request contains a valid secret key.
        """
        if request.method == "POST":
            client_secret = request.headers.get("X-SECRET-KEY")
            if client_secret != os.environ['SECRET_KEY']:
                return JSONResponse(status_code=403, content={"detail": "Forbidden: Invalid secret key"})

        response = await call_next(request)
        return response

app.add_middleware(SecretKeyMiddleware)

@app.post('/chat/stream')
async def run(input: dict):
    print(input)
    return StreamingResponse(stream_response(input), media_type='text/plain')

if __name__ == "__main__":
    uvicorn.run(app, port=8000)


# runnable_workflow = RunnableLambda(invoke_response)
# runnable_async_workflow = awit RunnableLambda(stream_response)

# add_routes(
#     app,
#     runnable_workflow, 
#     path="/chat", 
#     playground_type='chat'
# )

# def invoke_response(input: dict) -> str: 
#     state = {'user_query': input.get('user_query', '')}
#     response = workflow.stream(state) 
    
#     if isinstance(response, dict) and 'response' in response:
#         return response['response']
    
#     return {'output': 'Error processing request'}

# async def stream_response(input: dict):
#     state = {'user_query': input.get('user_query', '')}

#     for chunk in workflow.stream(state): 
#         if isinstance(chunk, dict):
#             if 'response' in chunk:
#                 yield chunk['response']
#         else:
#             yield str(chunk) 
#         await asyncio.sleep(0)