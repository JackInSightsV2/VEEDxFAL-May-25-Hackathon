"""Utility functions for the project."""


def beautify_diary(text: str) -> str:
    """Make diary text look nice."""
    # TODO: implement text beautification
    return text


def beautify_transcript(transcript: str, mood: str, sieve_data: dict) -> str:
    """Format the transcript using simple metadata."""
    themes = ", ".join(sieve_data.get("topics", []))
    sentiment = sieve_data.get("sentiment", "reflective")
    return (
        f"A {sentiment} retelling of a day themed around {themes}:\n\n"
        f"{transcript}"
    )
