import logging
import re
import sys

import yake

logger = logging.getLogger(__name__)
logger.level=logging.DEBUG
_streamHandler = logging.StreamHandler(sys.stdout)
_formatter = logging.Formatter("%(levelname)s at %(asctime)s | %(filename)s | %(funcName)s >> %(message)s")
_streamHandler.setFormatter(_formatter)
logger.addHandler(_streamHandler)

def analyzeChapter(chapter_text: str, lang='en', num_of_keywords=100):
    clean_text = re.sub(r"\[.*?\]", "", chapter_text)
    
    kw_extractor = yake.KeywordExtractor(lan=lang, top=num_of_keywords)
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
                    "position": match.start()
                })

        # Step 1: Select the top-k most significant (lowest score = highest relevance)
        candidates.sort(key=lambda x: x["score"])
        top_k = candidates[:k]

        # Step 2: Re-sort the top-k subset chronologically by position
        top_k.sort(key=lambda x: x["position"])

        results.append({
            "sentence": sentence,
            "keywords": [(item["keyword"], item["score"]) for item in top_k]
        })

    return results
    

if __name__ == "__main__":
    
    chapter="""
    In 2010, inside the underground enrichment plant at Natanz, Iran, roughly a thousand centrifuges destroyed themselves while the control room screens showed normal operations. The malware, later identified as Stuxnet and built jointly by the US and Israel, had hijacked the facility's programmable logic controllers. It replayed twenty-one seconds of recorded telemetry in a continuous loop so technicians saw stable pressure and nominal speeds while the rotors spun out of control. 
    Stuxnet was the first confirmed digital weapon engineered to destroy physical infrastructure, the same industrial control architecture that governs civilian electrical grids today. That line of development traces back to software written with no destructive intent: the 1971 Creeper program, an experimental script that migrated across early ARPANET systems to display the message, "I'm the creeper, catch me if you can!"""

    kw=analyzeChapter(chapter)
    # logger.debug(sentences)
    for item in mswPerSentence(chapter, kw):
        print(item)

