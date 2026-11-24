class InspectionError(ValueError):
    def __init__(self, code, source=None, status=422):
        self.code = code
        self.source = source
        self.status = status
        super().__init__(code)
