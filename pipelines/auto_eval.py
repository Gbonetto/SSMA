# pipelines/auto_eval.py
import openai
import os

def auto_eval_llm(question, answer, sources):
    """
    Utilise GPT-4 (ou GPT-3.5) pour scorer automatiquement la pertinence et la clartÃ© dâ€™une rÃ©ponse.
    NÃ‰CESSITE la variable d'env OPENAI_API_KEY.
    """
    openai.api_key = os.environ.get("OPENAI_API_KEY")
    if not openai.api_key:
        raise RuntimeError("OPENAI_API_KEY non trouvÃ©e dans l'environnement.")
    prompt = f"""
Tu es un Ã©valuateur professionnel pour un assistant IA.
Question :
{question}

RÃ©ponse gÃ©nÃ©rÃ©e :
{answer}

Sources utilisÃ©es :
{sources}

Donne une note sur 10 Ã  la pertinence, une note sur 10 Ã  la clartÃ©, et un commentaire (bref) en JSON strict :
{{
  "pertinence": int,
  "clarte": int,
  "commentaire": str
}}
RÃ©ponds uniquement en JSON.
"""
    response = openai.ChatCompletion.create(
        model="gpt-4",   # Ou "gpt-3.5-turbo" si tu veux rÃ©duire le coÃ»t
        messages=[{"role": "user", "content": prompt}],
        max_tokens=200
    )
    import json
    try:
        return json.loads(response['choices'][0]['message']['content'])
    except Exception as e:
        return {"pertinence": -1, "clarte": -1, "commentaire": f"Erreur parsing: {str(e)}"}



