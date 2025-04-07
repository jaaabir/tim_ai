import requests
# from langchain.embeddings.base import Embeddings
from langchain_core.embeddings import Embeddings

### This is a custom embedding class for Hugging Face Spaces.
### It allows you to use models hosted on Hugging Face Spaces for generating embeddings.
class HuggingFaceSpaceEmbeddings(Embeddings):
    def __init__(self, space_url: str, secret_key: str = None):
        """
        Args:
            space_url (str): The URL of your Hugging Face Space.
            secret_key (str, optional): The secret key to authenticate requests (if needed).
        """
        self.space_url = space_url.rstrip("/")  
        self.secret_key = secret_key  

    def embed_documents(self, texts):
        """
        Generates embeddings for a list of texts.
        """
        if type(texts) == str:
            return self._get_embedding(texts)
        return [self._get_embedding(text) for text in texts]

    def embed_query(self, text):
        """
        Generates an embedding for a single query.
        """
        return self._get_embedding(text)

    def _get_embedding(self, text):
        """
        Sends a POST request to the hosted model and retrieves embeddings.
        """
        data = {"user_input": text}
        headers = {"Content-Type": "application/json"}
        if self.secret_key:
            headers["X-SECRET-KEY"] = self.secret_key  

        response = requests.post(
            f"{self.space_url}/embed",
            json=data,
            headers=headers
        )
        if response.status_code == 200:
            return response.json()["output"]  
        else:
            raise ValueError(f"Error {response.status_code}: {response.text}")

