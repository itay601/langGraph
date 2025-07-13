from langchain_core.tools import tool
import requests
from pydantic import BaseModel
import xml.etree.ElementTree as ET
from datetime import datetime
from astrapy import DataAPIClient
import re
from dotenv import load_dotenv
import os

load_dotenv()



class ArxivToAstra:
    def __init__(self, astra_token, astra_endpoint):
        """Initialize connection to Astra DB"""
        self.client = DataAPIClient(astra_token)
        self.db = self.client.get_database_by_api_endpoint(astra_endpoint)

    # regex search
    def search_papers(self, query=None, limit=10, collection_name="arxiv_papers"):
      collection = self.db.get_collection(collection_name)

      if query:
          results = collection.find({}, limit=100) 
          filtered_results = [
              doc for doc in results
              if (doc.get('title') and re.search(query, doc['title'], re.IGNORECASE)) or
                (doc.get('summary') and re.search(query, doc['summary'], re.IGNORECASE))
          ]
          return filtered_results[:limit]
      else:
          results = collection.find({}, limit=limit)
          return list(results)
    
    # Better Alternative approach more control over the vector search
    # need to configure vector embeddings for the data for using this matrix
    def search_papers_advanced(self, query=None, limit=10, collection_name="arxiv_papers", similarity_threshold=0.7):
        collection = self.db.get_collection(collection_name)
        
        if query:
            # Use vector_find_one to get the most similar document first (optional)
            results = collection.find(
                sort={"$vector": query},
                limit=limit,
                projection={"title": 1, "summary": 1, "authors": 1, "categories": 1, "_id": 1},
                include_similarity=True
            )
            
            if similarity_threshold:
                filtered_results = [
                    doc for doc in results 
                    if doc.get('$similarity', 0) >= similarity_threshold
                ]
                return filtered_results
            
            return list(results)
        else:
            results = collection.find({}, limit=limit)
            return list(results)



@tool(description="Fetches arxives collected in database using vector search for relevant data user query.")
def fetch_arxives(economic_term):
    ASTRA_TOKEN = os.environ["ASTRA_TOKEN"] 
    ASTRA_ENDPOINT = os.environ["ASTRA_ENDPOINT"] 

    # Initialize the ArXiv to Astra pipeline
    arxiv_store = ArxivToAstra(ASTRA_TOKEN, ASTRA_ENDPOINT)
    print(f"\nSearching for {economic_term} papers...")
    results = arxiv_store.search_papers( economic_term, limit=3)
    #results = arxiv_store.search_papers_advanced( economic_term, limit=3) # TODO: in production
    
    for paper in results:
        print(f"- {paper['title']}")
        print(f"  Authors: {', '.join([a['name'] for a in paper['authors']])}")
        print(f"  Categories: {', '.join(paper['categories'])}")
        print()
    return {"arxives": results}    



@tool(description="Fetches the latest economic or stock-related articles.")
def fetch_articles(economic_term, symbol) -> dict:
    url = f"http://localhost:8000/v1/api/dataagent?economic_term={economic_term}&symbol={symbol}"
    try:
        response = requests.post(url)
        response.raise_for_status()
        return {"data": response.json()}
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}



@tool
# This is new! 
class Question(BaseModel):
    """Question to ask user."""
    content: str        

@tool
# This is new! 
class Done(BaseModel):
    """Analysis has been sent to the user."""
    done: bool

tools = [ 
    fetch_articles, 
    Question, 
    Done,
]