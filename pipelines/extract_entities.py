import re
import spacy
import langdetect

# ========================
# Chargement des modÃ¨les spaCy
# ========================
_SPACY_MODELS = {}

def get_spacy_model(lang):
    if lang not in _SPACY_MODELS:
        try:
            if lang == "fr":
                _SPACY_MODELS[lang] = spacy.load("fr_core_news_md")
            elif lang == "en":
                _SPACY_MODELS[lang] = spacy.load("en_core_web_md")
            else:
                _SPACY_MODELS[lang] = None
        except Exception:
            _SPACY_MODELS[lang] = None
    return _SPACY_MODELS[lang]

# ========================
# DÃ©tection de langue
# ========================
def detect_lang(text):
    try:
        return langdetect.detect(text)
    except Exception:
        return "fr"  # Fallback franÃ§ais

# ========================
# Extraction par regex
# ========================
def extract_montants(text):
    if not text:
        return []
    pattern = r"(\d{1,3}(?:[\s.,]\d{3})*(?:[.,]\d+)?\s*(?:â‚¬|euros?|dollars?|\$))"
    found = re.findall(pattern, text.replace('\xa0', ' ').replace('\n', ' '))
    return [m.strip() for m in found]

def extract_dates(text):
    if not text:
        return []
    pattern = r"\b(\d{1,2}[/\-.]\d{1,2}[/\-.]\d{2,4})\b"
    found = re.findall(pattern, text)
    return list(set(found))

# ========================
# Extraction spaCy NER
# ========================
def extract_spacy_entities(text, lang="fr"):
    nlp = get_spacy_model(lang)
    if not nlp:
        return {}
    doc = nlp(text)
    ents = {"PER": [], "ORG": [], "LOC": [], "MISC": []}
    for ent in doc.ents:
        ents.setdefault(ent.label_, []).append(ent.text)
    for k in ents:
        ents[k] = list(set(ents[k]))
    return ents

# ========================
# Fallback LLM extraction (GENERIC JSON)
# ========================
def fallback_llm_extract(text, llm_func=None):
    if not llm_func:
        return {}
    prompt = (
        "Extrait tous les montants (â‚¬, euros, $), dates, personnes, et entreprises du texte suivant. "
        "RÃ©ponds uniquement au format JSON avec les clÃ©s 'montants', 'dates', 'PER', 'ORG'.\n\n"
        f"TEXTE:\n{text}\n"
    )
    try:
        result = llm_func(prompt)
        if isinstance(result, str):
            import json
            result = json.loads(result)
        return result
    except Exception:
        return {}

# ========================
# Fallback LLM extraction PERSONS ONLY
# ========================
def fallback_llm_extract_persons(text, openai_api_key):
    import openai
    prompt = (
        "Tu es un expert du traitement documentaire. "
        "Extrais la liste des personnes physiques citÃ©es dans ce texte :\n"
        f"{text}\n"
        "Donne uniquement la liste, sans commentaire, sous forme JSON : { \"persons\": [ ... ] }"
    )
    response = openai.ChatCompletion.create(
        model="gpt-4",
        api_key=openai_api_key,
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )
    import json
    import re
    answer = response.choices[0].message.content
    try:
        match = re.search(r'\{.*\}', answer, re.DOTALL)
        if match:
            return json.loads(match.group(0)).get("persons", [])
    except Exception:
        pass
    return []

# ========================
# Fusion, fallback et filtrage
# ========================
def filter_entities(entities):
    # Garde que l'essentiel
    return {k: v for k, v in entities.items() if k in ["PER", "ORG", "montants", "dates"] and v}

def extract_all_entities(
    text,
    openai_api_key=None,
    fallback_llm=None,
    filter_result=True,
    force_lang=None
):
    lang = force_lang or detect_lang(text)
    entities = {}
    entities["montants"] = extract_montants(text)
    entities["dates"] = extract_dates(text)
    entities.update(extract_spacy_entities(text, lang=lang))

    # Fallback LLM (full JSON) si besoin et si llm_func fourni
    if fallback_llm and (
        not entities.get("PER") or not entities.get("ORG") or not entities.get("montants")
    ):
        llm_ents = fallback_llm_extract(text, fallback_llm)
        for k in ["PER", "ORG", "montants", "dates"]:
            if k in llm_ents and not entities.get(k):
                entities[k] = llm_ents[k]

    # Fallback LLM OpenAI spÃ©cifique personnes si toujours rien
    if openai_api_key and (not entities.get("PER") or len(entities.get("PER", [])) == 0):
        persons = fallback_llm_extract_persons(text, openai_api_key)
        if persons:
            entities["PER"] = persons

    # Nettoyage final si besoin
    if filter_result:
        entities = filter_entities(entities)
    return entities



