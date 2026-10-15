import logging
import sys

from lxml import etree
from lxml.etree import _Element


class FCPMarker:
    def __init__(self, parentNode: _Element, start: str, value:str, duration: str = '100/5000s'):
        """FCP marker costructor

        Args:
            parentNode (_Element): The node to which attach the marker
            start (str): When the marker should start expressed in: "xxxx/25s"
            value (str): Canonical name of the marker, i.e. the one that appears onto the timeline.
            duration (str): How much time should the marker last. Expressed in: "xxx/5000s"
        """
        self.parentNode = parentNode
        self.start = start
        self.value = value
        self.duration = duration
        self.logger = logging.getLogger(__name__)
        self.logger.level=logging.DEBUG
        self._streamHandler = logging.StreamHandler(sys.stdout)
        self._formatter = logging.Formatter("%(levelname)s at %(asctime)s | %(filename)s | %(funcName)s >> %(message)s")
        self._streamHandler.setFormatter(self._formatter)
        self.logger.addHandler(self._streamHandler)

    def check_parameters(self):
        if not (isinstance(self.parentNode, _Element) and isinstance(self.start, str) and isinstance(self.value, str) and isinstance(self.duration, str)):
            raise TypeError('Parameters\' format is invalid.') 
        
    def add_marker_to_timeline(self):
        """
        Adds the marker onto the timeline
        """
        try:
            self.check_parameters()
            attributes={
            'start': self.start,
            'duration': self.duration,
            'value': self.value
            }
            etree.SubElement(self.parentNode, "marker", attrib=attributes)
            self.logger.info(f"Marker node correctly added to {self.parentNode.tag}")
        except TypeError as e:
            self.logger.error(f'{e}')

        
