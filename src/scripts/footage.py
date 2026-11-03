from pathlib import Path
from urllib.parse import unquote

from lxml import etree
from lxml.etree import _Element

from src.core.exceptions import SanityCheckException
from src.core.logger import get_logger

logger = get_logger(__name__)

class Asset:
    def __init__(self, parent: _Element):
        self.parent = parent

    def _sanityCheck(self, duration: str, hasAudio: int, audioSources: int, audioChannels:int, audioRate: int, filePath:str):
        """
        This function returs True if the parameters are valid
        """
        duration_valid = isinstance(duration, str)
        hasAudio_valid = isinstance(hasAudio, int)
        audioSources_valid = isinstance(audioSources, int)
        audioChannels_valid = isinstance(audioChannels, int)
        audioRate_valid = isinstance(audioRate, int)
        decoded_file_path = unquote(filePath)
        path_parts = decoded_file_path.split(':')
        if len(path_parts) != 2:
            raise SanityCheckException("The URI has something strange, check it")
        if path_parts[0] != 'file':
            raise SanityCheckException("Check that URI has 'file' prefix")
        file = Path.from_uri(decoded_file_path)

        if not (duration_valid and hasAudio_valid and audioSources_valid and audioChannels_valid and audioRate_valid and file.exists()):
            raise SanityCheckException("Sanity Check Failed")

    def configureAsset(self, id: str, name: str, start: str, duration:str, hasAudio:int, audioSources: int , audioChannels:int, filePath_encoded: str, audioRate:int = 44100):
        """This function configures the asset node in the XML

        Args:
            id (str): The id of the asset. Usually in 'r123' fromat
            name (str): The canonical name of the asset
            start (str): The start value of the asset. Format: 123s
            duration (str): The duration of the whole asset. Fractional format allowed
            hasAudio (str): '1' if the asset has audio, '0' otherwise
            audioSources (int): Number of audio sources
            audioChannels (int): Number of audio channels
            filePath_encoded (str): The full, url encoded, path of the media in format: 'file:///file/path.extension'
            audioRate (int, optional): Audio rate. Defaults to 44100.
        """
        try:
            self._sanityCheck(duration, hasAudio, audioSources, audioChannels, audioRate, filePath_encoded)
            attributes = {
                'id': id,
                'name': name,
                'start': start,
                'duration': duration,
                'hasAudio': hasAudio,
                'audioSources': audioSources,
                'audioChannels': audioChannels,
                'audioRate': audioRate
            }
            # create asset node
            asset_node = etree.SubElement(self.paren, 'asset', attrib=attributes)

            # create media-rep child
            media_rep_attributes = {
                'kind': 'original-media',
                'src': filePath_encoded,
            }
            media_rep_node = etree.SubElement(asset_node, 'media-rep', attrib=media_rep_attributes)
            return asset_node, media_rep_node
        except SanityCheckException:
            logger.debug("Sanity check failed, please check the values")

    
class Footage:
    def __init__(self):
        pass

    def setStart(self):
        """This method should set the footage onto the timeline
        """

    def setEnd(self):
        """This method should set the end of the footage
        """

    def setMedia(self):
        """This method should set all the attributes related to the media
        """

    def place(self):
        """This method should place the footage onto the timeline
        """

    def addAsAsset(self):
        """This method should add the media to the 'asset' section of the xml
        """