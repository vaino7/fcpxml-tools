import json
import logging
import os
import re
import sys
from pathlib import Path
import time
from urllib.parse import urlencode
from dotenv import load_dotenv

import requests
import yake

logger = logging.getLogger(__name__)
logger.level=logging.DEBUG
_streamHandler = logging.StreamHandler(sys.stdout)
_formatter = logging.Formatter("%(levelname)s at %(asctime)s | %(filename)s | %(funcName)s >> %(message)s")
_streamHandler.setFormatter(_formatter)
logger.addHandler(_streamHandler)

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

def createKeywordFile(msw: list[dict]):
    # This function should create the file that contains the keywords for the creator to look up
    kw_file = Path('kw_file.txt')
    kw = [elem for item in msw for elem in item['img-id']]
    kw_file.write_text('\n'.join(kw))
    return kw

def getSuggestions(keywords:list, lang: str = 'en', numOfSuggestions= 3, searchImages: bool = True):
    # This function should return suggestions for which media to download using pixabay 
    kw_suggestion_file = Path('kw_suggestions.txt')
    api_key = os.getenv("PIXABAY_API_KEY")
    endpoint = os.getenv("PIXABAY_IMAGES_URL") if searchImages else os.getenv("PIXABAY_VIDEOS_URL")
    if not api_key:
        logger.warning("No PIXABAY API Key has been found, thus no suggestions will be generated")
        return
    if not endpoint:
            logger.warning("No endpoint has been found, thus no suggestions will be generated")
            return
    res = {}
    for kw in keywords:

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

    

if __name__ == "__main__":
    
    chapter="""
    In 2010, inside the underground enrichment plant at Natanz, Iran, roughly a thousand centrifuges destroyed themselves while the control room screens showed normal operations. The malware, later identified as Stuxnet and built jointly by the US and Israel, had hijacked the facility's programmable logic controllers. It replayed twenty-one seconds of recorded telemetry in a continuous loop so technicians saw stable pressure and nominal speeds while the rotors spun out of control. 
    Stuxnet was the first confirmed digital weapon engineered to destroy physical infrastructure, the same industrial control architecture that governs civilian electrical grids today. That line of development traces back to software written with no destructive intent: the 1971 Creeper program, an experimental script that migrated across early ARPANET systems to display the message, "I'm the creeper, catch me if you can!"""

    kw=analyzeChapter(chapter, ngrams=1)
    results = mswPerSentence(chapter, kw, k=3)
    kw_list= createKeywordFile(results)
    logger.debug(getSuggestions(kw_list))


# Consider using https://pixabay.com/api/docs/ for autodownload