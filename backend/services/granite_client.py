"""
ParallaX | IBM Granite / watsonx.ai Integration
Uses ibm-watson-machine-learning SDK when credentials available.
Falls back to deterministic responses when unavailable.
"""
import os, json, logging, requests
logger = logging.getLogger(__name__)

class GraniteClient:
    def __init__(self):
        self.api_key = os.getenv("WATSONX_API_KEY", "")
        self.project_id = os.getenv("WATSONX_PROJECT_ID", "")
        self.url = os.getenv("WATSONX_URL", "https://us-south.ml.cloud.ibm.com")
        self.model_id = os.getenv("GRANITE_MODEL_ID", "ibm/granite-13b-instruct-v2")
        self.available = bool(self.api_key and self.project_id)
        self._token = None
        if self.available:
            logger.info("IBM Granite: credentials found, attempting connection")
        else:
            logger.info("IBM Granite: no credentials — deterministic fallback active")

    def _get_token(self) -> str:
        if self._token:
            return self._token
        resp = requests.post(
            "https://iam.cloud.ibm.com/identity/token",
            data={"grant_type": "urn:ibm:params:oauth:grant-type:apikey", "apikey": self.api_key},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=15
        )
        self._token = resp.json().get("access_token", "")
        return self._token

    def generate(self, prompt: str, max_tokens: int = 400) -> str:
        if not self.available:
            return self._fallback(prompt)
        try:
            token = self._get_token()
            payload = {
                "model_id": self.model_id,
                "input": prompt,
                "parameters": {"decoding_method": "greedy", "max_new_tokens": max_tokens},
                "project_id": self.project_id
            }
            resp = requests.post(
                f"{self.url}/ml/v1/text/generation?version=2023-05-29",
                headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
                json=payload, timeout=30
            )
            data = resp.json()
            if "results" in data:
                return data["results"][0].get("generated_text", "")
            return self._fallback(prompt)
        except Exception as e:
            logger.warning(f"Granite API error: {e} — using fallback")
            return self._fallback(prompt)

    def enhance_answer(self, question: str, computed_answer: str, data: dict) -> str:
        prompt = (
            f"You are a road safety analyst for Bengaluru, India.\n"
            f"Question: {question}\n"
            f"Data: {computed_answer}\n"
            f"Provide a concise, factual 2-3 sentence response based strictly on the data provided. "
            f"Do not invent numbers. Label any interpretation as an observation, not a fact.\n"
            f"Response:"
        )
        return self.generate(prompt, max_tokens=200)

    def explain_risk(self, station: str, risk_score: float, fatal: int, total: int, yoy: float) -> str:
        prompt = (
            f"Road safety analysis for {station} police station, Bengaluru:\n"
            f"Risk score: {risk_score}/100 | Fatal accidents: {fatal} | Total: {total} | YoY change: {yoy:+.1f}%\n"
            f"Provide a 2-sentence plain-language explanation of this risk profile for a traffic authority officer. "
            f"Be factual. Do not invent data.\nExplanation:"
        )
        return self.generate(prompt, max_tokens=150)

    def summarize_blackspot(self, station: str, blackspots: list) -> str:
        bs_desc = "; ".join(b.get("original_location_description", "") for b in blackspots[:5])
        prompt = (
            f"Official Bengaluru Traffic Police blackspots in {station}:\n{bs_desc}\n"
            f"Summarize these locations and their road safety significance in 2-3 sentences.\nSummary:"
        )
        return self.generate(prompt, max_tokens=200)

    def _fallback(self, prompt: str) -> str:
        # Deterministic fallback — labeled clearly
        return "[IBM Granite unavailable — deterministic fallback] " + \
               "Analysis based on supplied accident statistics and official BTP blackspot data. " + \
               "Configure WATSONX_API_KEY and WATSONX_PROJECT_ID in .env to enable Granite LLM responses."

    @property
    def status(self) -> dict:
        return {
            "available": self.available,
            "model": self.model_id if self.available else "N/A",
            "fallback_active": not self.available,
            "note": "Set WATSONX_API_KEY and WATSONX_PROJECT_ID in .env to enable"
        }
