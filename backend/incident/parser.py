import os
import json
from typing import Dict, Any, List
from groq import AsyncGroq
from dotenv import load_dotenv

load_dotenv()

class LogParser:
    """Universal AI-powered Log & Incident Normalizer using LLM zero-shot extraction."""
    
    @staticmethod
    async def parse_raw_log(raw_text: str) -> Dict[str, Any]:
        groq_api_key = os.getenv("GROQ_API_KEY", "").strip()
        raw_model = os.getenv("LLM_MODEL", "openai/gpt-oss-120b")
        model = raw_model.replace("groq/", "").strip()

        if not groq_api_key or groq_api_key.startswith("your_"):
            return LogParser._fallback_parser(raw_text)

        system_prompt = """
You are a Universal System Log & Incident Parser.
Analyze the provided raw log trace or error dump (from any programming language, framework, database, or infrastructure).

Extract and return ONLY a valid JSON object matching this schema:
{
  "service": "<detected or candidate service name, e.g. recommendation-engine, payment-api, auth-service, k8s-cluster>",
  "severity": "<high | critical | medium>",
  "summary": "<concise 1-sentence description of the failure>",
  "symptoms": ["<extracted symptom 1>", "<extracted symptom 2>"],
  "logs": ["<extracted primary error stack trace or exception line>"],
  "recent_changes": ["<extracted configuration or deployment change if mentioned, otherwise leave empty>"]
}
"""

        try:
            client = AsyncGroq(api_key=groq_api_key)
            response = await client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"RAW LOG TRACE:\n{raw_text[:3000]}"}
                ],
                response_format={"type": "json_object"},
                temperature=0.1
            )
            data = json.loads(response.choices[0].message.content)
            data["metrics"] = {"parsed_lines_count": len(raw_text.splitlines()), "ai_parsed": True}
            return data
        except Exception as err:
            print(f"[LogParser Error] Fallback triggered: {err}")
            return LogParser._fallback_parser(raw_text)

    @staticmethod
    def _fallback_parser(raw_text: str) -> Dict[str, Any]:
        lines = [line.strip() for line in raw_text.strip().split("\n") if line.strip()]
        extracted_logs = []
        extracted_symptoms = []
        
        for line in lines:
            if any(k in line for k in ["Error", "Exception", "CRITICAL", "FATAL", "Timeout", "OOM", "500", "503", "panic"]):
                extracted_logs.append(line[:300])
                extracted_symptoms.append(line.split(":")[0][:50])

        if not extracted_logs and lines:
            extracted_logs.append(lines[0][:300])
        if not extracted_symptoms:
            extracted_symptoms.append("Unclassified System Anomaly")

        return {
            "service": "production-service",
            "severity": "high",
            "summary": extracted_symptoms[0] if extracted_symptoms else "Raw Log Intake",
            "symptoms": list(set(extracted_symptoms))[:3],
            "logs": extracted_logs[:5],
            "metrics": {"parsed_lines_count": len(lines), "ai_parsed": False},
            "recent_changes": ["Pasted raw log trace"]
        }