"""Utility functions for the project."""

import re


def beautify_diary(text: str) -> str:
    """Make diary text look nice."""
    # TODO: implement text beautification
    return text


def beautify_transcript(transcript: str, mood: str, sentiment_data: dict, gender: str = None, age_group: str = None, visual_style: str = None) -> str:
    """Format the transcript using sentiment analysis metadata and user attributes."""
    themes = ", ".join(sentiment_data.get("topics", []))
    sentiment = sentiment_data.get("sentiment", "reflective")
    user_desc = []
    if gender:
        user_desc.append(f"for a {gender}")
    if age_group:
        user_desc.append(f"in the {age_group} age group")
    if visual_style:
        user_desc.append(f"with a {visual_style} visual style")
    user_desc_str = ", ".join(user_desc)
    if user_desc_str:
        user_desc_str = f" ({user_desc_str})"
    return (
        f"A {sentiment} retelling of a day themed around {themes}{user_desc_str}:\n\n"
        f"{transcript}"
    )


def extract_key_phrases(
    transcript: str, sentiment_data: dict, num_phrases: int = 4,
    gender: str = None, age_group: str = None, visual_style: str = None
) -> list[str]:
    """Extract key phrases from transcript for video generation, tailored to user attributes. Selects the most important sentences by topic match and length."""
    sentences = re.split(r'[.!?]+', transcript)
    sentences = [s.strip() for s in sentences if s.strip()]
    themes = sentiment_data.get("topics", [])
    sentiment = sentiment_data.get("sentiment", "reflective")

    # Score each sentence by number of topic matches, then by length
    def topic_score(sentence):
        score = 0
        for topic in themes:
            if topic.lower() in sentence.lower():
                score += 1
        return score

    scored_sentences = [
        (s, topic_score(s), len(s.split()))
        for s in sentences if len(s.split()) > 2  # filter out very short sentences
    ]
    # Sort by topic score (desc), then by length (desc)
    scored_sentences.sort(key=lambda x: (x[1], x[2]), reverse=True)
    selected_sentences = [s[0] for s in scored_sentences[:num_phrases]]

    key_phrases = []
    for sentence in selected_sentences:
        details = []
        if gender:
            details.append(f"{gender}")
        if age_group:
            details.append(f"{age_group} age group")
        if visual_style:
            details.append(f"{visual_style} style")
        details_str = ", ".join(details)
        if details_str:
            details_str = f" ({details_str})"
        # Find the first matching topic for this sentence
        matching_topic = None
        for topic in themes:
            if topic.lower() in sentence.lower():
                matching_topic = topic
                break
        if matching_topic:
            prompt = f"A {sentiment} scene about {matching_topic}{details_str}: {sentence.lower()}"
        else:
            prompt = f"A {sentiment} scene showing {sentence.lower()}{details_str}"
        key_phrases.append(prompt)
    return key_phrases
