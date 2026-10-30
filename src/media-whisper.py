from asyncio import timeout
import json
import logging
import os
import re
import sys
import time
import uuid
from pathlib import Path
from urllib.parse import urlencode

import ollama
import requests
import yake
from dotenv import load_dotenv
from pydantic import BaseModel

from ollama import chat

logger = logging.getLogger(__name__)
logger.level=logging.DEBUG
_streamHandler = logging.StreamHandler(sys.stdout)
_formatter = logging.Formatter("%(levelname)s at %(asctime)s | %(filename)s | %(funcName)s >> %(message)s")
_streamHandler.setFormatter(_formatter)
logger.addHandler(_streamHandler)

client = ollama.Client(
    host='http://localhost:11434',
    timeout=100
)

env_file = Path('.env')
load_dotenv(env_file)

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

    # kw_file.write_text('\n'.join(kw))

    kw_file.write_text(json.dumps(kw_dict, indent=2), 'utf-8')
    return kw_dict

def getFootageSuggestions(synonymous:list, ngrams, lang: str = 'en', numOfSuggestions= 3, searchImages: bool = True):
    # This function should return suggestions for which media to download using pixabay 
    kw_suggestion_file = Path(f'kw_{'images' if searchImages else 'videos'}_suggestions_with{ngrams}ngrams.txt')
    api_key = os.getenv("PIXABAY_API_KEY")
    endpoint = os.getenv("PIXABAY_IMAGES_URL") if searchImages else os.getenv("PIXABAY_VIDEOS_URL")
    if not api_key:
        logger.warning("No PIXABAY API Key has been found, thus no suggestions will be generated")
        return
    if not endpoint:
            logger.warning("No endpoint has been found, thus no suggestions will be generated")
            return
    res = {}
    for kw in synonymous:

        params = {
            'key': api_key,
            'lang': lang,
            'q': kw,
        }
        results = requests.get(endpoint, params=params)
        results.raise_for_status()
        data: dict = results.json()
        data['hits'] = sorted(data['hits'], key= lambda x: x['downloads'])
        data['hits'] = data.get('hits',[])[:numOfSuggestions]
        logger.debug(f'Sent request for {kw}')

        res[kw]=data
        time.sleep(0.4)

    kw_suggestion_file.write_text(json.dumps(res, indent=2))
    
    return results



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

    
    # response = chat(model=model,messages=messages, format=Keyword_Item.model_json_schema(), ti)
    response = client.chat(model=model,messages=messages, format=Keyword_Item.model_json_schema())
    structured_response = Keyword_Item.model_validate_json(response.message.content)
    logger.debug(f"Generated: {structured_response}")
    return structured_response

def footageCheck():
    """This function checks the footage nomenclature is respected within /video folder"""
    video_folder = Path('..') / 'video'
    kw_file = Path('kw_file.txt')
    if not kw_file.exists():
        logger.error(f'{kw_file} does not exist')
        return False
    with open(kw_file, 'r') as f:
        kw_content: dict = json.load(f)
    
    footage_ids = kw_content.keys()
    video_folder_content = []
    for file in video_folder.iterdir():
        if file.is_file():
            video_folder_content.append(file.stem)

    logger.debug(f"Content of {video_folder}: {video_folder_content}")
    missing_files=[]
    for id in footage_ids:
        if id not in video_folder_content:
            missing_files.append(id)

    logger.debug(missing_files)
    return len(missing_files)==0


if __name__ == "__main__":
    
    chapter="""
    In 2010, inside the underground enrichment plant at Natanz, Iran, roughly a thousand centrifuges destroyed themselves while the control room screens showed normal operations. The malware, later identified as Stuxnet and built jointly by the US and Israel, had hijacked the facility's programmable logic controllers. It replayed twenty-one seconds of recorded telemetry in a continuous loop so technicians saw stable pressure and nominal speeds while the rotors spun out of control. 
    Stuxnet was the first confirmed digital weapon engineered to destroy physical infrastructure, the same industrial control architecture that governs civilian electrical grids today. That line of development traces back to software written with no destructive intent: the 1971 Creeper program, an experimental script that migrated across early ARPANET systems to display the message, "I'm the creeper, catch me if you can!"""

    # kw=analyzeChapter(chapter, ngrams=3)
    # results = mswPerSentence(chapter, kw, k=3)
    # kw_list= createKeywordFile(results)
    # logger.debug(kw_list)
    # indexFootage(kw_list)
    # logger.debug(getSuggestions(kw_list,3))
    #getSynonymous('#@#'.join(kw_list))
    sanity_check = footageCheck()
    print(sanity_check)