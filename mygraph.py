import os,re
import dotenv
from pinecone import Pinecone
from langchain_groq import ChatGroq
from langchain_pinecone import PineconeVectorStore
from langchain.schema import BaseOutputParser, SystemMessage, HumanMessage, AIMessage
from langchain.memory import ConversationBufferMemory
from langchain_huggingface.embeddings import HuggingFaceEndpointEmbeddings
from langgraph.graph import Graph
from langchain_core.runnables import RunnableLambda

dotenv.load_dotenv()

GROK_API_KEY        = os.environ.get('LLM_API_KEY')
PINECONE_API_KEY   = os.environ.get('PINECONE_API_KEY')
HUGGINGFACE_API_KEY = os.environ.get('HUGGINGFACE_API_KEY')


def load_file(fname):
    with open(fname, 'r', encoding='utf-8') as f:
        data = f.read()
    return data

class CleanStrOutputParser(BaseOutputParser):
    def parse(self, output: str) -> str:
        return self.get_clean_output_from_llm(output)
    
    def get_clean_output_from_llm(self, response, rtype = str):
        if response:
            pattern = r'<think>.*?</think>|\n'
            response = re.sub(pattern, '', response if type(response) == rtype else response.content, flags=re.DOTALL)
            return response

class MyAgent:
    def __init__(self, 
        VECTOR_STORE_INDEX_NAME = 'resume-index-bge',
        EMBEDDING_MODEL_NAME    = 'BAAI/bge-large-en-v1.5',
        LLM_MODEL_NAME          = "llama-3.3-70b-versatile",
        TOP_K = 3,
        NAME = 'Muhammed Jaabir'
        ):

        self.VECTOR_STORE_INDEX_NAME = VECTOR_STORE_INDEX_NAME
        self.EMBEDDING_MODEL_NAME    = EMBEDDING_MODEL_NAME
        self.LLM_MODEL_NAME          = LLM_MODEL_NAME
        self.TOP_K = TOP_K
        self.NAME = NAME
        
        self.system_prompt_template = load_file(os.path.join('.', 'system_prompt.txt'))
        self.memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

        pc = Pinecone(PINECONE_API_KEY)
        index = pc.Index(self.VECTOR_STORE_INDEX_NAME)
        embedding_model = HuggingFaceEndpointEmbeddings(
            model=self.EMBEDDING_MODEL_NAME, 
            huggingfacehub_api_token=HUGGINGFACE_API_KEY,  
            model_kwargs={"wait_for_model": True}
            )
        vector_store = PineconeVectorStore(index=index, embedding=embedding_model)

        self.retriever = vector_store.as_retriever(search_type="similarity", search_kwargs={'k': TOP_K})
        self.llm = ChatGroq(model=self.LLM_MODEL_NAME,
            temperature=0.9,
            max_tokens=1000,
            timeout=None,
            max_retries=2,
            api_key=GROK_API_KEY)
        
    def retrieve_context(self, state):
        query = state["user_query"]
        top_k_docs = self.retriever.get_relevant_documents(query)
        state['context'] = '\n'.join([doc.page_content for doc in top_k_docs])
        return state 

    def retrieve_past_conversation(self):
        return self.memory.load_memory_variables({})['chat_history']

    def generate_response(self, state):
        user_query = state["user_query"]
        context = state["context"]
        name = self.NAME
        top_k = self.TOP_K

        chat_history = self.retrieve_past_conversation()
        system_message = self.system_prompt_template.format(name=name, K=top_k)
        
        messages = [
            SystemMessage(content=system_message),
            *chat_history,  
            HumanMessage(content=f"User Query: {user_query}\nContext: {context}"),
        ]
        
        response = self.llm.invoke(messages)
        
        self.memory.save_context({"input": user_query}, {"output": response.content})
        
        state["llm_response"] = response.content
        return state

            
    def clean_output(self, state):
        response = state['llm_response']
        state['response'] = CleanStrOutputParser().parse(response)
        return state
    

    def compile_graph(self):
        workflow = Graph()
        workflow.add_node("retrieve", self.retrieve_context)
        workflow.add_node("generate", self.generate_response)
        workflow.add_node("clean", self.clean_output)

        workflow.add_edge("retrieve", "generate")
        workflow.add_edge("generate", "clean")

        workflow.set_entry_point("retrieve")
        workflow.set_finish_point("clean")

        app = workflow.compile()
        return app
    


