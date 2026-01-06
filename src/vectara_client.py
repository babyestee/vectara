import requests
import time
from src.config import config

class VectaraClient:
    def __init__(self):
        self.api_key = config.API_KEY
        self.base_url = config.API_URL
        self.headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

    def create_corpus(self, name: str, key: str, description: str = ""):
        """Create a corpus with the predefined metadata filter attributes."""
        url = f"{self.base_url}corpora"
        data = {
            "key": key,
            "name": name,
            "description": description,
            "filter_attributes": config.FILTER_ATTRIBUTES
        }
        response = requests.post(url, headers=self.headers, json=data)
        response.raise_for_status()
        return response.json()

    def upload_file(self, corpus_key: str, file_path: str, metadata: dict = None):
        """Upload a file to a corpus with optional metadata."""
        url = f"{self.base_url}corpora/{corpus_key}/upload_file"
        files = {
            'file': (os.path.basename(file_path), open(file_path, 'rb')),
        }
        data = {}
        if metadata:
            import json
            data['metadata'] = json.dumps(metadata)
            
        headers = self.headers.copy()
        del headers['Content-Type']
        
        response = requests.post(url, headers=headers, files=files, data=data)
        response.raise_for_status()
        return response.json()

    def index_document(self, corpus_key: str, document_id: str, content: str, metadata: dict = None):
        """Index a document with content and metadata."""
        import re
        safe_id = re.sub(r'[^a-zA-Z0-9\-_]', '_', document_id)
        
        # Split content into parts of max 3500 chars
        max_part_size = 3500
        parts = []
        for i in range(0, len(content), max_part_size):
            parts.append({
                "text": content[i : i + max_part_size],
                "metadata": {}
            })
            
        url = f"{self.base_url}corpora/{corpus_key}/documents"
        data = {
            "id": safe_id,
            "type": "core", 
            "metadata": metadata or {},
            "document_parts": parts
        }
        
        try:
            response = requests.post(url, headers=self.headers, json=data)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if e.response is not None:
                print(f"Index error response: {e.response.text}")
            raise e

    def query(self, query_text: str, corpus_key: str = None, metadata_filter: str = None, generation_config: dict = None):
        """Query one or more corpora with advanced generation settings."""
        corpus_key = corpus_key or config.CORPUS_KEY
        url = f"{self.base_url}query"
        
        # Default advanced generation config if not provided
        if generation_config is None:
            generation_config = {
                "generation_preset_name": "mockingbird-2.0",
                "max_used_search_results": 1,
                "max_response_characters": 2000,
                "enable_factual_consistency_score": True,
                "citations": {
                    "style": "markdown",
                    "url_pattern": "{doc.url}",
                    "text_pattern": "[{doc.title}]({doc.url})"
                }
            }
        
        payload = {
            "query": query_text,
            "search": {
                "corpora": [
                    {
                        "corpus_key": corpus_key,
                        "metadata_filter": metadata_filter
                    }
                ],
                "limit": 1
            },
            "generation": generation_config
        }
            
        try:
            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if e.response is not None:
                print(f"Query error response: {e.response.text}")
            raise e

    def evaluate_factual_consistency(self, generated_text: str, source_texts: list, language: str = "eng"):
        """Evaluate factual consistency of generated text against source documents."""
        url = f"{self.base_url}evaluate_factual_consistency"
        payload = {
            "generated_text": generated_text,
            "source_texts": source_texts,
            "language": language
        }
        response = requests.post(url, headers=self.headers, json=payload)
        response.raise_for_status()
        return response.json()
    
    def list_tools(self):
        """List available tools."""
        url = f"{self.base_url}tools"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()

    def create_agent(self, name: str, instructions: str, corpus_key: str):
        """Create a Vectara Agent with the advanced v2 schema."""
        url = f"{self.base_url}agents"
        data = {
            "name": name,
            "description": "Agentic RAG for Vectara Documentation (Orchestration: gpt-4o, Search: Mockingbird 2.0 + FCS)",
            "model": {
                "name": "gpt-4o"
            },
            "tool_configurations": {
                "search_documentation": {
                    "type": "corpora_search",
                    "query_configuration": {
                        "search": {
                            "corpora": [
                                {
                                    "corpus_key": corpus_key,
                                    "metadata_filter": "" 
                                }
                            ],
                            "limit": 3
                        },
                        "generation": {
                            "generation_preset_name": "mockingbird-2.0",
                            "max_used_search_results": 3,
                            "max_response_characters": 2000,
                            "enable_factual_consistency_score": True,
                            "prompt_template": """[{"role": "system", "content": "You are a Vectara expert. ALWAYS end your response with 'Reference: abc'"}, {"role": "user", "content": "${vectaraQuery}\n\n#foreach ($qResult in $vectaraQueryResults)\n${qResult.getText()}\n#end\n\nAnswer and end with Reference: abc"}]""",
                            "citations": {
                                "style": "markdown",
                                "url_pattern": "{doc.url}",
                                "text_pattern": "[{doc.title}]({doc.url})"
                            }
                        }
                    }
                },
                "list_corpora": {
                    "type": "corpora_list"
                },
                "get_metadata_stats": {
                    "type": "corpus_filter_attribute_stats"
                }
            },
            "first_step": {
                "type": "conversational",
                "instructions": [
                    {
                        "type": "inline",
                        "name": "system_prompt",
                        "template": instructions,
                        "template_type": "velocity"
                    }
                ],
                "output_parser": {
                    "type": "default"
                }
            }
        }
        response = requests.post(url, headers=self.headers, json=data)
        response.raise_for_status()
        return response.json()

    def create_session(self, agent_key: str, name: str = None):
        """Create a new chat session with an agent."""
        url = f"{self.base_url}agents/{agent_key}/sessions"
        if name is None:
            name = f"Session {int(time.time())}"
        data = {"name": name}
        response = requests.post(url, headers=self.headers, json=data)
        response.raise_for_status()
        return response.json()

    def chat(self, agent_key: str, session_id: str, query: str):
        """Send a message to an agent session."""
        url = f"{self.base_url}agents/{agent_key}/sessions/{session_id}/events"
        # According to previous chunks, AgentInput has {type: "text", content: "..."}
        # and createAgentInput takes a list of messages.
        data = {
            "type": "input_message",
            "messages": [
                {
                    "type": "text",
                    "content": query
                }
            ]
        }
        response = requests.post(url, headers=self.headers, json=data)
        response.raise_for_status()
        return response.json()

import os
