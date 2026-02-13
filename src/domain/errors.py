class PdfSuiteError(Exception):
    pass


class ValidationError(PdfSuiteError):
    pass


class ParsingError(PdfSuiteError):
    pass


class FileIOError(PdfSuiteError):
    pass


class SystemErrorCategory(PdfSuiteError):
    pass
