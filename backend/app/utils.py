"""Utility functions for the project."""

import re


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


def extract_key_phrases(transcript: str, sieve_data: dict, num_phrases: int = 4) -> list[str]:
    """Extract key phrases from transcript for video generation."""
    # Split transcript into sentences
    sentences = re.split(r'[.!?]+', transcript)
    sentences = [s.strip() for s in sentences if s.strip()]
    
    # Get themes and sentiment from sieve data
    themes = sieve_data.get("topics", [])
    sentiment = sieve_data.get("sentiment", "reflective")
    
    # If we have fewer sentences than requested phrases, return all sentences
    if len(sentences) <= num_phrases:
        return [f"A {sentiment} scene showing {sentence.lower()}" for sentence in sentences]
    
    # Select sentences that are substantial (more than 5 words)
    substantial_sentences = [s for s in sentences if len(s.split()) > 5]
    
    # If we still have too many, take every nth sentence
    if len(substantial_sentences) > num_phrases:
        step = len(substantial_sentences) // num_phrases
        selected_sentences = [substantial_sentences[i * step] for i in range(num_phrases)]
    else:
        selected_sentences = substantial_sentences
    
    # Format as video prompts
    key_phrases = []
    for i, sentence in enumerate(selected_sentences):
        if themes and i < len(themes):
            prompt = f"A {sentiment} scene about {themes[i]}: {sentence.lower()}"
        else:
            prompt = f"A {sentiment} scene showing {sentence.lower()}"
        key_phrases.append(prompt)
    
    return key_phrases
