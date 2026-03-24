class DocumentAPIError(Exception):
    """Base exception for Document API errors."""
    pass

class DocumentNotFoundError(DocumentAPIError):
    """Exception raised when a document is not found."""
    pass

class SignatureStatusError(DocumentAPIError):
    """Exception raised when there's an error getting signature status."""
    pass 