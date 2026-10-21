import logging
import sys
import yake
import re


logger = logging.getLogger(__name__)
logger.level=logging.DEBUG
_streamHandler = logging.StreamHandler(sys.stdout)
_formatter = logging.Formatter("%(levelname)s at %(asctime)s | %(filename)s | %(funcName)s >> %(message)s")
_streamHandler.setFormatter(_formatter)
logger.addHandler(_streamHandler)

def analyzeChapter(chapter_text: str, lang='en', num_of_keywords=20):
    clean_text = re.sub(r"\[.*?\]", "", chapter_text)
    
    kw_extractor = yake.KeywordExtractor(lan=lang, top=num_of_keywords)
    kw=kw_extractor.extract_keywords(clean_text)
    return kw

if __name__ == "__main__":
    
    chapter='In the heart of the Iranian desert [EMPHASIS], beneath a mountain, a room full of machines was having a very bad year'
    kw=analyzeChapter(chapter)
    for word in kw:
        print(word)
    print(len(kw))


