from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_core.messages import AnyMessage
from langgraph.checkpoint.memory import MemorySaver
from langchain.schema import BaseOutputParser, SystemMessage, AIMessage, HumanMessage
from langchain_groq import ChatGroq
from langchain.memory import ConversationBufferMemory

from pinecone import Pinecone
from langchain_pinecone.vectorstores import PineconeVectorStore
from space_embedding import HuggingFaceSpaceEmbeddings

import os,re
import dotenv

dotenv.load_dotenv()


def load_file(fname):
    with open(fname, 'r', encoding='utf-8') as f:
        return f.read()

def get_retriver_from_pc(index_name, embedding_model_name, top_k):
    pc = Pinecone(api_key = os.environ['PINECONE_API_KEY'])
    secret_key = os.environ.get('SECRET_KEY')
    embedding_model = HuggingFaceSpaceEmbeddings(
        space_url= embedding_model_name,
        secret_key= secret_key
    )
    vector_store = PineconeVectorStore(index= pc.Index(index_name), embedding = embedding_model )
    return vector_store.as_retriever(search_type="similarity", search_kwargs={'k': top_k})

def load_llm_from_huggingface(model_name):
    llm = ChatGroq(model= model_name,
            temperature=0.9,
            max_tokens=1000,
            timeout=None,
            max_retries=2,
            api_key= os.environ['LLM_API_KEY'])
    return llm

def load_sys_prompt(fname, username, top_k):
    return SystemMessage(load_file(fname).format(name = username, K = top_k))

### State Schema
class State(TypedDict):
    user_input   : str
    chat_history : Annotated[list[AnyMessage], add_messages]
    llm_response : str


class CleanStrOutputParser(BaseOutputParser):
    def parse(self, output: str) -> str:
        return self.get_clean_output_from_llm(output)
    
    def get_clean_output_from_llm(self, response, rtype = str):
        if response:
            pattern = r'<think>.*?</think>|\n'
            response = re.sub(pattern, '', response if type(response) == rtype else response.content, flags=re.DOTALL)
            return response

class MyAgent:
    def __init__(self, name = 'Muhammed Jaabir', top_k = 3):
        
        self.username = name
        self.top_k = top_k
        index_name = 'resume-index-bge'
        self.sys_message = load_file('system_prompt.txt').format(name = self.username, K = self.top_k)
        embedding_model_name = 'https://jaaabir-baai-bge-large-en-v1-5.hf.space'
        model_name = "llama-3.3-70b-versatile"
        self.retriever = get_retriver_from_pc(index_name, embedding_model_name, top_k)
        self.llm = load_llm_from_huggingface(model_name)

        self.graph = StateGraph(State)
        self.graph.add_node('init_sys_message', self.init_sys_message_to_state)
        self.graph.add_node('retriever', self.retriever_node)
        self.graph.add_node('invoke_llm', self.llm_node)

        self.graph.set_entry_point('init_sys_message')
        self.graph.add_edge('init_sys_message', 'retriever')
        self.graph.add_edge('retriever', 'invoke_llm')
        self.graph.add_edge('invoke_llm', END)

    def compile_graph(self):
        return self.graph.compile(checkpointer=MemorySaver())
    
    ### Nodes 
    def init_sys_message_to_state(self, state: State) -> State:
        if not state['chat_history']:
            memory = ConversationBufferMemory(return_messages=True)
            memory.chat_memory.add_message(SystemMessage(self.sys_message))
            return {
                'chat_history' : memory.chat_memory.messages,
            }
        return state
    
    def retriever_node(self, state: State) -> State:
        user_query = state['user_input']
        context = '\n'.join([doc.page_content for doc in self.retriever.invoke(user_query)])
        user_query = user_query + '\n' + '[CONTEXT FROM VECTOR STORE]' + '\n' + context
        state['chat_history'].append(HumanMessage(user_query))
        return state

    def llm_node(self, state: State) -> State:
        chain = self.llm | CleanStrOutputParser()
        messages = state['chat_history']
        response = chain.invoke(messages)
        if response:
            state['chat_history'].pop()
            state['chat_history'].append(HumanMessage(state['user_input']))
            state['chat_history'].append(AIMessage(response))
            return {
                'llm_response': response
            }
        return state


# prompt = '''
# user's question with context from the vector store: {user_input}

# past_conversation : {chat_history}
# '''

# model_input_prompt = PromptTemplate(input_variables=['user_input', 'chat_history'], template=prompt)

# chain = model_input_prompt | self.llm | CleanStrOutputParser()

# user_input = state['user_input']
# system_message = state['chat_history'][0]
# human_messages = [m for m in state['chat_history'] if isinstance(m, HumanMessage)]
# bot_messages = [m for m in state['chat_history'] if isinstance(m, AIMessage)]
# history = 'Human messages:' + '\n' + human_messages + '\n' + 'Ai messages:' + '\n' + bot_messages

