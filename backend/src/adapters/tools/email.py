def email_sender(to: str, subject: str, body: str) -> str:
    """Mock email sender."""
    # Mocking a successful email send
    return f"Success: Email sent to {to} with subject '{subject}'."
