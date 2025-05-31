"""Google Cloud Natural Language API integration for sentiment analysis and topic extraction."""

import os
import re
from typing import Dict, List, Any
from google.cloud import language_v1


def analyze_transcript(transcript: str) -> Dict[str, Any]:
    """
    Analyze transcript using Google Cloud Natural Language API.
    Returns sentiment and topics extracted from the text.
    """
    # Set Google credentials (if not already set)
    if not os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
        # Assumes the JSON key is in the project root
        root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        cred_path = os.path.join(root_dir, "veedxfal-hackathon-2025-ea1537c41d2c.json")
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = cred_path
    
    # Initialize the Language client
    client = language_v1.LanguageServiceClient()
    
    # Create document from transcript
    document = language_v1.Document(
        content=transcript,
        type_=language_v1.Document.Type.PLAIN_TEXT
    )
    
    result = {}
    
    try:
        # Analyze sentiment
        sentiment_response = client.analyze_sentiment(
            request={"document": document}
        )
        
        sentiment_score = sentiment_response.document_sentiment.score
        sentiment_magnitude = sentiment_response.document_sentiment.magnitude
        
        # Convert sentiment score to readable format
        if sentiment_score > 0.1:
            sentiment = "positive"
        elif sentiment_score < -0.1:
            sentiment = "negative"
        else:
            sentiment = "neutral"
            
        result["sentiment"] = sentiment
        result["sentiment_score"] = sentiment_score
        result["sentiment_magnitude"] = sentiment_magnitude
        
        # Analyze entities to extract topics
        entities_response = client.analyze_entities(
            request={"document": document}
        )
        
        # Extract meaningful topics from entities
        topics = []
        for entity in entities_response.entities:
            # Filter entities with high salience (importance)
            if entity.salience > 0.1:
                # Clean up entity names and categorize them
                entity_name = entity.name.lower().strip()
                entity_type = entity.type_.name.lower()
                
                # Skip very generic entities
                if len(entity_name) < 3 or entity_name in ["i", "me", "my", "the", "a", "an"]:
                    continue
                
                # Categorize based on entity type and content
                topic = categorize_entity(entity_name, entity_type)
                if topic and topic not in topics:
                    topics.append(topic)
        
        # If no entities found, extract topics from keywords
        if not topics:
            topics = extract_topics_from_keywords(transcript)
            
        result["topics"] = topics[:5]  # Limit to top 5 topics
        
        # Add entity details for debugging
        result["entities"] = [
            {
                "name": entity.name,
                "type": entity.type_.name,
                "salience": entity.salience
            }
            for entity in entities_response.entities
            if entity.salience > 0.05
        ]
        
    except Exception as e:
        print(f"Error analyzing transcript with GCP NLP: {e}")
        # Fallback to basic keyword extraction
        result = {
            "sentiment": "positive",
            "sentiment_score": 0.0,
            "sentiment_magnitude": 0.0,
            "topics": extract_topics_from_keywords(transcript),
            "entities": [],
            "error": str(e)
        }
    
    return result


def categorize_entity(entity_name: str, entity_type: str) -> str:
    """
    Categorize entities into meaningful topics for video generation.
    """
    # Activity/action keywords
    activity_keywords = {
        "run", "running", "jog", "jogging", "walk", "walking", "exercise", "workout",
        "coffee", "breakfast", "lunch", "dinner", "eat", "eating", "drink", "drinking",
        "work", "working", "study", "studying", "read", "reading", "write", "writing",
        "paint", "painting", "draw", "drawing", "art", "create", "creating",
        "cook", "cooking", "bake", "baking", "clean", "cleaning",
        "shop", "shopping", "buy", "buying", "travel", "traveling", "drive", "driving"
    }
    
    # Location keywords
    location_keywords = {
        "home", "house", "office", "work", "school", "university", "park", "gym",
        "restaurant", "cafe", "coffee shop", "store", "mall", "beach", "city",
        "studio", "kitchen", "bedroom", "garden", "library", "hospital", "church"
    }
    
    # People/social keywords
    people_keywords = {
        "friend", "friends", "family", "mom", "dad", "mother", "father", "sister",
        "brother", "colleague", "coworker", "partner", "husband", "wife", "child",
        "kids", "children", "people", "team", "group"
    }
    
    # Object/interest keywords
    object_keywords = {
        "book", "books", "movie", "movies", "music", "song", "game", "games",
        "phone", "computer", "laptop", "car", "bike", "camera", "photo", "picture"
    }
    
    entity_lower = entity_name.lower()
    
    # Check for activities
    for keyword in activity_keywords:
        if keyword in entity_lower:
            if keyword in ["run", "running", "jog", "jogging", "walk", "walking", "exercise", "workout"]:
                return "exercise & fitness"
            elif keyword in ["coffee", "breakfast", "lunch", "dinner", "eat", "eating", "drink", "drinking"]:
                return "food & dining"
            elif keyword in ["work", "working", "study", "studying"]:
                return "work & productivity"
            elif keyword in ["paint", "painting", "draw", "drawing", "art", "create", "creating"]:
                return "art & creativity"
            elif keyword in ["cook", "cooking", "bake", "baking"]:
                return "cooking"
            elif keyword in ["shop", "shopping", "buy", "buying"]:
                return "shopping"
            elif keyword in ["travel", "traveling", "drive", "driving"]:
                return "travel"
    
    # Check for locations
    for keyword in location_keywords:
        if keyword in entity_lower:
            if keyword in ["park", "beach", "garden"]:
                return "nature & outdoors"
            elif keyword in ["restaurant", "cafe", "coffee shop"]:
                return "dining out"
            elif keyword in ["home", "house", "kitchen", "bedroom"]:
                return "home life"
            elif keyword in ["office", "work", "school", "university", "library"]:
                return "work & study"
            elif keyword == "gym":
                return "fitness"
    
    # Check for people/social
    for keyword in people_keywords:
        if keyword in entity_lower:
            return "social & relationships"
    
    # Check for objects/interests
    for keyword in object_keywords:
        if keyword in entity_lower:
            if keyword in ["book", "books", "read", "reading"]:
                return "reading"
            elif keyword in ["movie", "movies", "music", "song"]:
                return "entertainment"
            elif keyword in ["game", "games"]:
                return "gaming"
            elif keyword in ["photo", "picture", "camera"]:
                return "photography"
    
    # If entity_type gives us useful info
    if entity_type in ["person", "other"]:
        return "social time"
    elif entity_type == "location":
        return "places & travel"
    elif entity_type == "event":
        return "activities"
    
    # Default fallback - return the entity name if it's meaningful
    if len(entity_name) > 2 and not entity_name.isdigit():
        return entity_name
    
    return None


def extract_topics_from_keywords(transcript: str) -> List[str]:
    """
    Fallback method to extract topics using keyword matching.
    """
    topics = []
    text_lower = transcript.lower()
    
    # Define topic patterns
    topic_patterns = {
        "morning routine": ["morning", "wake up", "woke up", "sunrise", "early"],
        "exercise & fitness": ["run", "running", "jog", "exercise", "workout", "gym", "fitness"],
        "food & dining": ["coffee", "breakfast", "lunch", "dinner", "eat", "food", "restaurant", "cafe"],
        "work & productivity": ["work", "working", "office", "project", "meeting", "task"],
        "art & creativity": ["art", "paint", "painting", "draw", "drawing", "create", "creative", "studio"],
        "social & relationships": ["friend", "friends", "family", "dinner", "meet", "laugh", "together"],
        "nature & outdoors": ["park", "nature", "outside", "garden", "beach", "outdoor"],
        "home life": ["home", "house", "kitchen", "room", "clean", "organize"],
        "entertainment": ["movie", "music", "song", "game", "book", "read", "watch"],
        "travel": ["travel", "trip", "drive", "car", "bus", "train", "airport"],
        "shopping": ["shop", "shopping", "buy", "store", "mall", "purchase"],
        "cooking": ["cook", "cooking", "bake", "recipe", "kitchen", "chef"],
        "relaxation": ["relax", "calm", "peaceful", "quiet", "rest", "sleep"]
    }
    
    for topic, keywords in topic_patterns.items():
        if any(keyword in text_lower for keyword in keywords):
            topics.append(topic)
    
    # If no topics found, extract some basic ones
    if not topics:
        topics = ["daily life", "personal time"]
    
    return topics[:5]  # Return top 5 topics


def get_sentiment_description(sentiment: str, score: float) -> str:
    """
    Get a human-readable description of the sentiment.
    """
    if sentiment == "positive":
        if score > 0.5:
            return "very positive"
        else:
            return "positive"
    elif sentiment == "negative":
        if score < -0.5:
            return "very negative"
        else:
            return "negative"
    else:
        return "neutral" 