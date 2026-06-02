class ISMRDataFetchError(Exception):

    def __init__(self, message: str, original_status: int = None):
        self.message = message
        self.original_status = original_status
        super().__init__(self.message)