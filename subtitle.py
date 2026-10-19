from decimal import DivisionByZero
import logging
import sys

from lxml import etree
from lxml.etree import _Element

logger = logging.getLogger(__name__)
logger.level=logging.DEBUG
_streamHandler = logging.StreamHandler(sys.stdout)
_formatter = logging.Formatter("%(levelname)s at %(asctime)s | %(filename)s | %(funcName)s >> %(message)s")
_streamHandler.setFormatter(_formatter)
logger.addHandler(_streamHandler)

class SubtitleError(Exception):
      def __init__(self, message):
            self.message=message
            super().__init__(self.message)


class Subtitle:
    """
    This class represents a title tag with all its attributes and subchild
    """
    def __init__(self, titleNode: _Element):
        self.node = titleNode
        self.ref=titleNode.get('ref')
        self.lane=titleNode.get('lane')
        self.offset=titleNode.get('offset')
        self._offset_parsed=[]
        self.name=titleNode.get('name')
        self.start=titleNode.get('start')
        self._start_parsed=[]
        self.duration=titleNode.get('duration')
        self._duration_parsed=[]
        self.role=titleNode.get('role')

        self.marker: _Element=titleNode.xpath('./following-sibling::marker')
        self.children: list[_Element]= list(titleNode)
        #debug
        #logger.debug(self.children)
    
    def setRef(self, ref:str):
        """
        This function sets the ref attribute
        """
        self.ref=ref
        self.node.set('ref', self.ref)

    def setLane(self, lane:str):
            """
            This function sets the lane attribute
            """
            self.lane=lane
            self.node.set('lane', self.lane)

    def setOffset(self, offset:str):
            """
            This function sets the offset attribute
            """
            tmp_offset = offset.replace('s','')
            parts = [p for p in tmp_offset.split('/')]
            self._offset_parsed=parts
            logger.debug(parts)
            if all(p.isdigit() for p in parts):
                self.offset=offset
                self.node.set('offset', self.offset)
            else: raise SubtitleError('Invalid format for offset attribute')

    def setName(self, name:str):
            """
            This function sets the name attribute
            """
            self.name=name
            self.node.set('name', self.name)

    def setStart(self, start:str):
            """
            This function sets the start attribute
            """
            tmp_start = start.replace('s','')
            parts = [p for p in tmp_start.split('/')]
            self._start_parsed=parts
            logger.debug(parts)
            if all(p.isdigit() for p in parts):
                self.start=start
                self.node.set('start', self.start)
            else: raise SubtitleError('Invalid format for start attribute')
            

    def setDuration(self, duration:str):
            """
            This function sets the duration attribute
            """
            tmp_duration = duration.replace('s','')
            parts=[p for p in tmp_duration.split('/')]
            self._duration_parsed=parts
            logger.debug(parts)
            if all(p.isdigit() for p in parts):      
                self.duration=duration
                self.node.set('duration', self.duration)
            else: raise SubtitleError('Invalid format for duration attribute')

    def setRole(self, role:str):
            """
            This function sets the role attribute
            """
            self.role=role
            self.node.set('role', self.role)


    def getTimecodeOffset(self, framerate, parentTime):
        """
        This function returns the offset value with respect to the parent node
        """
        try:
            tmp_offset = self.offset.replace('s','')
            parts = [int(p) for p in tmp_offset.split('/')]
            self._offset_parsed=parts
            logger.debug(self._offset_parsed)
            if len(self._offset_parsed)==1:
                 absolute_sec=self._offset_parsed[0]
            else:
                 absolute_sec=self._offset_parsed[0]/self._offset_parsed[1]

            relative_sec = absolute_sec-float(parentTime)
            total_int_sec=int(relative_sec)
            decimal_part=relative_sec-total_int_sec

            hours = total_int_sec // 3600
            remainder = total_int_sec % 3600
            minutes = remainder // 60
            seconds = remainder % 60

            frames= (round(decimal_part*framerate))
            timecode_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}:{frames:02d}"
            value = f'Offset in seconds: {relative_sec:.2f}. Which is {timecode_str} in (HH:MM:SS:FF)'
            logger.debug(value)
            return value
        except DivisionByZero:
            raise SubtitleError('Division by zero happened here')