import requests

with open("analysis_output.txt", "r", encoding="utf-8") as f:
    analysis = f.read()

prompt = f"""You are analyzing a research paper summary.

Based on the following page-by-page analysis, answer clearly:
What is DeepSeek's main contribution to AI research?

ANALYSIS:
{analysis[:6000]}
"""

response = requests.post(
    "http://localhost:11434/api/generate",
    json={"model": "qwen2.5:0.5b", "prompt": prompt, "stream": False},
    timeout=120,
)

print(response.json().get("response", "No response"))
