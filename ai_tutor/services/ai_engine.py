"""
Deterministic Topic and Intent Matching Engine for SmartEdu Demo AI Tutor.

Operates purely locally without external APIs or network calls.
Normalizes text, extracts user intent, matches topics against the local knowledge base,
and formats grounded educational responses.
"""

import re
from typing import Dict, Any, Tuple, Optional
from ai_tutor.knowledge_base import KNOWLEDGE_BASE


# Intent pattern definitions
INTENT_PATTERNS = {
    'revision_questions': [
        r'\b(questions?|revision questions?|practice questions?|quiz me|test me|sample questions?|practice problems?)\b',
        r'\b(ask me|give me.*questions?|quiz)\b',
    ],
    'summarize': [
        r'\b(summarize|summary|summarise|brief overview|tldr|in short|nutshell|quick overview)\b',
    ],
    'key_points': [
        r'\b(key points?|bullet points?|important points?|takeaways?|highlights?|main points?|core concepts?)\b',
    ],
    'study_strategies': [
        r'\b(how (to|should i) (study|revise|learn|master|prepare)|study (strategy|tips?|methods?|techniques?)|revision tips?)\b',
    ],
    'explain': [
        r'\b(explain|what is|what are|define|tell me about|how does|how do|meaning of|concept of|describe)\b',
    ],
    'recommendations': [
        r'\b(what next|next topic|what should i (learn|study) next|recommend|suggestions?)\b',
    ]
}


def normalize_text(text: str) -> str:
    """Normalize input text by lowercasing, stripping extra whitespace and punctuation."""
    if not text:
        return ""
    text = text.lower().strip()
    # Replace punctuation with spaces for cleaner token matching
    text = re.sub(r'[^\w\s]', ' ', text)
    return ' '.join(text.split())


def detect_intent(normalized_text: str) -> str:
    """Determine the user's educational intent from normalized query text."""
    for intent, patterns in INTENT_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, normalized_text):
                return intent
    # Default intent if no explicit action keyword is provided
    return 'explain'


def find_topic_match(normalized_text: str) -> Tuple[Optional[str], Optional[Dict[str, Any]], float]:
    """
    Match query text against the local educational knowledge base.
    Returns (topic_key, topic_data, confidence_score).
    """
    best_key = None
    best_score = 0.0

    for key, data in KNOWLEDGE_BASE.items():
        score = 0.0
        # Check topic name
        if data['topic_name'].lower() in normalized_text:
            score += 10.0

        # Check keywords and phrases
        for kw in data['keywords']:
            kw_norm = kw.lower()
            if f" {kw_norm} " in f" {normalized_text} ":
                # Exact phrase match
                score += 5.0 + len(kw_norm.split()) * 2.0
            elif kw_norm in normalized_text:
                score += 3.0

        if score > best_score:
            best_score = score
            best_key = key

    # Threshold: must have at least 3.0 match score to avoid false positives
    if best_key and best_score >= 3.0:
        return best_key, KNOWLEDGE_BASE[best_key], best_score

    return None, None, 0.0


def generate_fallback_response(query: str) -> str:
    """Return a helpful, transparent fallback when a topic is unsupported."""
    topics_list = [f"• **{data['topic_name']}** ({data['category']})" for data in KNOWLEDGE_BASE.values()]
    topics_formatted = "\n".join(topics_list)

    return (
        "🤖 **SmartEdu Demo AI Tutor** (Local Rule-Based Assistant)\n\n"
        f"I couldn't identify a supported computer science or web development topic in your query: *\"{query[:80]}\"*.\n\n"
        "Because I run entirely on local rule-based intelligence without paid external AI APIs, "
        "my knowledge is carefully grounded in our curated educational curriculum.\n\n"
        "**Currently Supported Core Topics:**\n"
        f"{topics_formatted}\n\n"
        "💡 **Try asking me:**\n"
        "- *\"Explain normalization in DBMS\"*\n"
        "- *\"Give me key points about computer networks\"*\n"
        "- *\"Provide revision questions on Python\"*\n"
        "- *\"How should I study operating systems?\"*\n"
        "- *\"Summarize object-oriented programming\"*"
    )


def generate_topic_response(topic_key: str, topic_data: Dict[str, Any], intent: str) -> str:
    """Format structured, educational response based on matched topic and identified intent."""
    title = topic_data['topic_name']
    category = topic_data['category']

    if intent == 'explain':
        related = ", ".join([KNOWLEDGE_BASE.get(k, {}).get('topic_name', k) for k in topic_data.get('suggested_next_topics', [])])
        return (
            f"### 📘 Concept Explanation: {title}\n"
            f"**Category:** {category} | *Source: SmartEdu Core Curriculum*\n\n"
            f"{topic_data['explanation']}\n\n"
            f"#### 🔍 Key Takeaways:\n"
            + "\n".join([f"• {pt}" for pt in topic_data['key_points'][:3]]) + "\n\n"
            + (f"💡 **Suggested Next Topics:** {related}\n\n" if related else "") +
            f"*(Ask for 'revision questions' or 'study tips' to test your understanding!)*"
        )

    elif intent == 'summarize':
        return (
            f"### 📝 Quick Summary: {title}\n"
            f"**Category:** {category}\n\n"
            f"{topic_data['explanation']}\n\n"
            f"#### 🎯 Summary Points:\n"
            + "\n".join([f"• {pt}" for pt in topic_data['key_points']])
        )

    elif intent == 'key_points':
        return (
            f"### 🎯 Essential Key Points: {title}\n"
            f"**Domain:** {category}\n\n"
            + "\n".join([f"**{i+1}.** {pt}" for i, pt in enumerate(topic_data['key_points'])]) + "\n\n"
            f"💡 **Pro Tip:** Use these points for active recall practice before your exams."
        )

    elif intent == 'revision_questions':
        q_text = []
        for i, q in enumerate(topic_data['revision_questions']):
            q_text.append(
                f"**Question {i+1}:** {q['question']}\n\n"
                f"> **Answer & Explanation:** {q['answer']}"
            )
        return (
            f"### ✍️ Practice & Revision Questions: {title}\n"
            f"Test your active recall with these curated questions:\n\n"
            + "\n\n".join(q_text) + "\n\n"
            f"*(Tip: Write your own answers first before checking the explanations!)*"
        )

    elif intent == 'study_strategies':
        strategies = "\n".join([f"• {s}" for s in topic_data['study_strategies']])
        return (
            f"### 🧠 Recommended Study Strategy: {title}\n"
            f"To achieve deep conceptual mastery in **{title}**, apply these deliberate practice steps:\n\n"
            f"{strategies}\n\n"
            f"#### Core Principles to Master:\n"
            + "\n".join([f"• {pt}" for pt in topic_data['key_points'][:2]]) + "\n\n"
            f"💡 *Remember: Active retrieval and coding practice yield 2x higher retention than passive reading.*"
        )

    elif intent == 'recommendations':
        related_names = [KNOWLEDGE_BASE.get(k, {}).get('topic_name', k) for k in topic_data.get('suggested_next_topics', [])]
        related_list = "\n".join([f"• **{name}**" for name in related_names]) if related_names else "• Explore available courses in the catalog."
        return (
            f"### 🧭 Next Learning Recommendations for {title}\n"
            f"Based on your study of **{title}**, here are recommended sequential topics:\n\n"
            f"{related_list}\n\n"
            f"Start by asking: *\"Explain {related_names[0] if related_names else 'this topic'}\"*."
        )

    # General fallback to a well-rounded response
    return (
        f"### 📘 {title}\n"
        f"**Category:** {category}\n\n"
        f"{topic_data['explanation']}\n\n"
        f"#### Key Points:\n"
        + "\n".join([f"• {pt}" for pt in topic_data['key_points'][:3]]) + "\n\n"
        f"*(You can ask for 'revision questions', 'study strategies', or 'key points' on {title}.)*"
    )


def process_user_query(raw_query: str) -> Dict[str, Any]:
    """
    Main entry point for processing a user's text message to the AI Tutor.
    Validates input, normalizes, detects intent and topic, and generates response.
    """
    if not raw_query or not raw_query.strip():
        return {
            'success': False,
            'response': "Please enter a question or topic so I can assist you with your studies.",
            'intent': 'empty',
            'topic': None
        }

    cleaned_query = raw_query.strip()
    if len(cleaned_query) > 1000:
        return {
            'success': False,
            'response': "Your message exceeds the 1,000-character limit. Please ask a more concise question.",
            'intent': 'invalid_length',
            'topic': None
        }

    norm = normalize_text(cleaned_query)
    intent = detect_intent(norm)
    topic_key, topic_data, score = find_topic_match(norm)

    if not topic_data:
        response_text = generate_fallback_response(cleaned_query)
        return {
            'success': True,
            'response': response_text,
            'intent': intent,
            'topic': None,
            'matched': False
        }

    response_text = generate_topic_response(topic_key, topic_data, intent)
    return {
        'success': True,
        'response': response_text,
        'intent': intent,
        'topic': topic_data['topic_name'],
        'topic_key': topic_key,
        'matched': True
    }
