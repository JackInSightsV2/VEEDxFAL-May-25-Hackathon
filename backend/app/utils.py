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
    
    print(f"🔍 Input transcript ({len(transcript)} chars): {transcript[:200]}...")
    
    # More robust sentence splitting - handle multiple punctuation patterns
    sentences = re.split(r'[.!?]+\s*', transcript.strip())
    print(f"🔍 After initial split: {len(sentences)} sentences")
    
    # Also split on commas if sentences are very long
    expanded_sentences = []
    for sentence in sentences:
        if len(sentence.split()) > 20:  # If sentence is too long, try splitting on commas
            comma_parts = [part.strip() for part in sentence.split(',') if part.strip()]
            expanded_sentences.extend(comma_parts)
            print(f"🔍 Split long sentence into {len(comma_parts)} parts")
        else:
            expanded_sentences.append(sentence)
    
    # Clean and filter sentences
    sentences = [s.strip() for s in expanded_sentences if s.strip() and len(s.split()) > 2]
    print(f"🔍 After cleaning: {len(sentences)} valid sentences")
    for i, s in enumerate(sentences[:5]):  # Show first 5 sentences
        print(f"   {i+1}. {s[:100]}...")
    
    # Remove any empty or very short sentences
    sentences = [s for s in sentences if s and len(s.split()) >= 3]
    
    if not sentences:
        # Fallback: use the entire transcript as one sentence
        sentences = [transcript.strip()]
        print("🔍 Using fallback: entire transcript as one sentence")
    
    themes = sentiment_data.get("topics", [])
    sentiment = sentiment_data.get("sentiment", "reflective")
    print(f"🔍 Themes: {themes}, Sentiment: {sentiment}")

    # Score each sentence by number of topic matches, then by length
    def topic_score(sentence):
        score = 0
        sentence_lower = sentence.lower()
        for topic in themes:
            if topic.lower() in sentence_lower:
                score += 1
        return score

    scored_sentences = [
        (s, topic_score(s), len(s.split()))
        for s in sentences if len(s.split()) > 2  # filter out very short sentences
    ]
    
    # Sort by topic score (desc), then by length (desc)
    scored_sentences.sort(key=lambda x: (x[1], x[2]), reverse=True)
    
    # Take the top sentences, but ensure we don't exceed num_phrases
    selected_sentences = [s[0] for s in scored_sentences[:num_phrases]]
    print(f"🔍 Selected {len(selected_sentences)} sentences for phrase generation")
    
    # If we don't have enough sentences, pad with remaining ones
    if len(selected_sentences) < num_phrases and len(sentences) > len(selected_sentences):
        remaining_sentences = [s for s in sentences if s not in selected_sentences]
        selected_sentences.extend(remaining_sentences[:num_phrases - len(selected_sentences)])

    key_phrases = []
    for i, sentence in enumerate(selected_sentences):
        # Clean up the sentence
        sentence = sentence.strip()
        if not sentence:
            continue
            
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
        sentence_lower = sentence.lower()
        for topic in themes:
            if topic.lower() in sentence_lower:
                matching_topic = topic
                break
                
        if matching_topic:
            prompt = f"A {sentiment} scene about {matching_topic}{details_str}: {sentence_lower}"
        else:
            prompt = f"A {sentiment} scene showing {sentence_lower}{details_str}"
        
        key_phrases.append(prompt)
        print(f"🔍 Generated phrase {i+1}: {prompt[:100]}...")
    
    print(f"🔍 Final result: {len(key_phrases)} key phrases generated")
    # Ensure we return the correct number of phrases
    return key_phrases
