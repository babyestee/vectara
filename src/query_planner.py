import json
import re
from src.vectara_client import VectaraClient
from src.config import config

class QueryPlanner:
    def __init__(self, client: VectaraClient):
        self.client = client
        self.corpus_key = config.CORPUS_KEY

    def plan_queries(self, user_query: str) -> list:
        """
        Uses Vectara's generation API to decompose a user query into sub-queries.
        Note: We use a specific prompt format (JSON array) required by Vectara v2.
        """
        # Vectara v2 prompt_template expects a JSON array of messages
        # We'll use a simple one for planning
        planning_prompt = json.dumps([
            {"role": "system", "content": "You are an expert search query planner for Vectara documentation."},
            {"role": "user", "content": f"""
                Break down this user question into 3-5 distinct, focused search queries: "{user_query}"
                
                Available Metadata attributes:
                - section: ('rest-api', 'build', 'learn', 'deploy-and-scale')
                - topic: ('agents', 'corpora', 'query', 'auth', 'ingestion')
                - doc_type: ('guide', 'reference', 'tutorial', 'concept')
                
                OUTPUT FORMAT: A JSON array of objects. Each object has:
                - "query": The search string
                - "filter": A SQL-like filter string (e.g., "doc.section = 'rest-api'"). Return "" if no specific filter.
                - "reason": Why this query is needed.
                
                ONLY return the JSON array.
            """}
        ])

        try:
            response = self.client.query(
                query_text=user_query,
                corpus_key=self.corpus_key,
                generation_config={
                    "generation_preset_name": "mockingbird-2.0",
                    "max_response_characters": 1000,
                    "max_used_search_results": 3, # Lower limit for planning
                    "prompt_template": planning_prompt
                }
            )
            
            summary = response.get("summary", "")
            # Robust JSON extraction
            match = re.search(r'\[.*\]', summary, re.DOTALL)
            if match:
                json_str = match.group(0)
                # Clean up potential invalid control characters
                json_str = re.sub(r'[\x00-\x1F\x7F]', '', json_str)
                return json.loads(json_str)
            else:
                print(f"Failed to parse JSON from planner: {summary}")
                return [{"query": user_query, "filter": "", "reason": "Fallback to original query"}]
                
        except Exception as e:
            print(f"Error in query planning: {e}")
            return [{"query": user_query, "filter": "", "reason": "Fallback due to error"}]

class QueryOrchestrator:
    def __init__(self, client: VectaraClient):
        self.client = client
        self.planner = QueryPlanner(client)

    def execute_agentic_rag(self, user_query: str):
        print(f"\n[Agent] Planning search strategy for: {user_query}")
        plan = self.planner.plan_queries(user_query)
        
        all_results = []
        source_texts = []
        
        for i, step in enumerate(plan):
            print(f"  Step {i+1}: Searching for '{step['query']}' with filter [{step['filter']}]")
            res = self.client.query(
                query_text=step['query'],
                metadata_filter=step['filter'] if step['filter'] else None,
                skip_generation=True  # Search only, no generation for intermediate steps
            )
            # Collect results for final synthesis
            if "search_results" in res:
                all_results.extend(res["search_results"])
                # Collect source texts for FCS validation
                for r in res["search_results"]:
                    source_texts.append(r.get("text", ""))
        
        # Deduplicate results by ID
        unique_results = {r['document_id']: r for r in all_results}.values()
        print(f"\n[Agent] Gathered {len(unique_results)} relevant document segments. Synthesizing final answer with Mockingbird 2.0...")
        
        # Final synthesis using Vectara's Mockingbird 2.0 generation with FCS
        final_response = self.client.query(
            query_text=user_query,
            generation_config={
                "generation_preset_name": "mockingbird-2.0",
                "max_used_search_results": 2,
                "max_response_characters": 2500,
                "enable_factual_consistency_score": True,
                "citations": {
                    "style": "markdown",
                    "url_pattern": "{doc.url}",
                    "text_pattern": "[{doc.title}]({doc.url})"
                }
            }
        )
        
        # print(f"DEBUG - Final Response Keys: {final_response.keys()}")
        # Check if citations are in a list or part of search_results
        
        # Extract FCS score from response
        fcs_score = 0.0
        if "factual_consistency_score" in final_response:
            fcs_score = final_response["factual_consistency_score"]
        elif "summary" in final_response and isinstance(final_response.get("generation_metadata"), dict):
            fcs_score = final_response.get("generation_metadata", {}).get("factual_consistency_score", 0)
        
        # Extract citations
        citations = final_response.get("citations", [])
        
        return {
            "plan": plan,
            "answer": final_response.get("summary", "No answer generated."),
            "fcs": fcs_score,
            "citations": citations,
            "search_results_count": len(list(unique_results))
        }
