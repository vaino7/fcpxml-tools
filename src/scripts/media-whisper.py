import json
import re
import uuid
from pathlib import Path

import yake
from pydantic import BaseModel

import ollama
from src.core.config import Config
from src.core.logger import get_logger

logger = get_logger(__name__)
MEDIA_DIR = Path(f'{Config.MEDIA_FILE_DIR}')
MEDIA_DIR.mkdir(exist_ok=True)

client = ollama.Client(
    host=Config.OLLAMA_ENDPOINT,
    timeout=100
)

def analyzeChapter(chapter_text: str, lang='en', num_of_keywords=100, ngrams=3):
    clean_text = re.sub(r"\[.*?\]", "", chapter_text)
    
    kw_extractor = yake.KeywordExtractor(lan=lang, top=num_of_keywords, n=ngrams)
    kw=kw_extractor.extract_keywords(clean_text)
    return kw

def mswPerSentence(chapter: str, keywords: list, k=2):
    #sentences = chapter.strip().split('.')
    sentences=[sent.strip() for sent in chapter.replace('\n','').split('.')]
    kw_dict = {kw: score for kw, score in keywords}
    results=[]
    for sentence in sentences:
        
        candidates = []

        # Find keyword matches and their start positions
        for kw, score in kw_dict.items():
            match = re.search(r"\b" + re.escape(kw) + r"\b", sentence)
            if match:
                candidates.append({
                    "keyword": kw,
                    "score": score,
                    "position": match.start(),
                })

        candidates.sort(key=lambda x: x["score"])
        top_k = candidates[:k]

        # re-sort the top-k subset chronologically by position
        top_k.sort(key=lambda x: x["position"])

        results.append({
            "sentence": sentence,
            "keywords": [(item["keyword"], item["score"]) for item in top_k],
            "img-id": [item['keyword'] for item in top_k]
        })

    return results

def indexFootage(keywords):
    """This function takes in input the most significant ngrams and parses them in order to get a unique id to use for naming the footage

    Args:
        keywords (list[str]): the list of keywords
    """
    unique_filename_list: list[str] = [f"{kw.lower().replace(' ','_')}_{uuid.uuid4()}" for kw in keywords]
    for name in unique_filename_list:
        filename_path = MEDIA_DIR / f'{name}.jpg'
        filename_path.touch()
    logger.debug(unique_filename_list)
    return unique_filename_list

def createKeywordFile(msw: list[dict]):
    # This function should create the file that contains the keywords for the creator to look up
    kw_file = Path('kw_file.txt')
    kw = [elem for item in msw for elem in item['img-id']]

    # Create a dict that will contain keyword's metadata
    indexed_list =indexFootage(kw)

    # the llm expects a query in the format: "KEYWORD: [keyword]"
    logger.debug("Buildin up the array of synon, gimme some time, thanks")
    kw_synon = [getSynonymous(f"KEYWORD: {keyword}") for keyword in kw]
    logger.debug("Array of synon has been built")
    if len(kw) != len(indexed_list) != len(kw_synon.results):
        logger.error("There's a mismatch in lists length")
        logger.error("No kewyord file has been created")
        return

    logger.debug(f"Original kw length: {len(kw)}")
    logger.debug(f"Synon kw length: {len(kw_synon)}")
    
    kw_dict={}
    for i, kw_idx in enumerate(indexed_list):
        kw_dict[kw_idx] = {
            'id': kw_idx,
            'name': kw[i],
            'synonymous': kw_synon[i].suggestions
        }

    kw_file.write_text(json.dumps(kw_dict, indent=2), 'utf-8')
    return kw_dict


def getSynonymous (encoded_keyword: str):
    """This function asks the local llama3.2:3b (pretty lightweight) for search-engines suggestions about the keyword"""

    model='fcpxml-llama3.2-keyword-expert'
    messages=[{
        'role': 'user',
        'content': encoded_keyword
    }]

    class Keyword_Item(BaseModel):
        keyword: str
        suggestions: list[str]

    
    response = client.chat(model=model,messages=messages, format=Keyword_Item.model_json_schema())
    structured_response = Keyword_Item.model_validate_json(response.message.content)
    logger.debug(f"Generated: {structured_response}")
    return structured_response


if __name__ == "__main__":
    
    chapter="""
    In 2010, inside the underground enrichment plant at Natanz, Iran, roughly a thousand centrifuges destroyed themselves while the control room screens showed normal operations. The malware, later identified as Stuxnet and built jointly by the US and Israel, had hijacked the facility's programmable logic controllers. It replayed twenty-one seconds of recorded telemetry in a continuous loop so technicians saw stable pressure and nominal speeds while the rotors spun out of control. 
    Stuxnet was the first confirmed digital weapon engineered to destroy physical infrastructure, the same industrial control architecture that governs civilian electrical grids today. That line of development traces back to software written with no destructive intent: the 1971 Creeper program, an experimental script that migrated across early ARPANET systems to display the message, "I'm the creeper, catch me if you can!"""

    kw=analyzeChapter(chapter, ngrams=3)
    results = mswPerSentence(chapter, kw, k=3)
    kw_list= createKeywordFile(results)
    # logger.debug(kw_list)
    # indexFootage(kw_list)
    # logger.debug(getSuggestions(kw_list,3))
    #getSynonymous('#@#'.join(kw_list))