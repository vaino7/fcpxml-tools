class SubtitleError(Exception):
      def __init__(self, message):
            self.message=message
            super().__init__(self.message)


class SanityCheckException(Exception):
      def __init__(self, message):
            self.message=message
            super().__init__(self.message)