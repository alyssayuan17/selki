"""
analyzer/metrics/content_structure.py

Content-structure metric (rule-based, spaCy-backed):

- Uses spaCy to:
  - Split transcript into sentences
  - Measure sentence lengths
  - Detect "signposts" (first, next, in summary, finally, ...)

Outputs a metric object matching your schema:

  {
    "score_0_100": int | None,
    "label": "unclear_structure" |
             "mixed_structure" |
             "mostly_clear_structure" |
             "very_clear_structure" |
             "abstained",
    "confidence": float,
    "abstained": bool,
    "details": {...},
    "feedback": [...]
  }
"""

from __future__ import annotations
from typing import Dict, Any, List, Optional

import spacy

# Global cache so we don't reload model every call
_NLP = None


def _get_nlp():
    """
    Lazy-load spaCy English model.
    Make sure you've run:
        pip install spacy
        python -m spacy download en_core_web_sm
    """
    global _NLP
    if _NLP is None:
        try:
            _NLP = spacy.load("en_core_web_sm")
        except OSError as e:
            raise RuntimeError(
                "spaCy model 'en_core_web_sm' is not installed. "
                "Run: python -m spacy download en_core_web_sm"
            ) from e
    return _NLP


# --------------------------------------------------------
# Signpost detection
# --------------------------------------------------------

_SIGNPOST_PHRASES = [
    # Ordering/Sequencing
    "first",
    "firstly",
    "second",
    "secondly",
    "third",
    "thirdly",
    "fourth",
    "fifth",
    "next",
    "then",
    "after that",
    "following that",
    "lastly",
    "last",
    "finally",

    # Adding/Continuing
    "additionally",
    "furthermore",
    "moreover",
    "in addition",
    "also",
    "another point",
    "another thing",
    "what's more",
    "besides",

    # Contrasting
    "however",
    "on the other hand",
    "in contrast",
    "conversely",
    "nevertheless",
    "nonetheless",
    "although",
    "but",
    "yet",
    "despite this",
    "even so",
    "alternatively",

    # Comparing/Similarity
    "similarly",
    "likewise",
    "in the same way",
    "by the same token",

    # Exemplifying
    "for example",
    "for instance",
    "such as",
    "to illustrate",
    "as an example",
    "specifically",
    "namely",

    # Explaining/Clarifying
    "in other words",
    "that is",
    "to put it another way",
    "to clarify",

    # Cause/Effect
    "therefore",
    "thus",
    "consequently",
    "as a result",
    "hence",
    "accordingly",
    "for this reason",
    "because of this",

    # Summarizing/Concluding
    "in summary",
    "to summarize",
    "to sum up",
    "in conclusion",
    "to conclude",
    "in short",
    "overall",
    "all in all",
    "in brief",

    # Emphasizing
    "indeed",
    "in fact",
    "certainly",
    "obviously",
    "clearly",
    "importantly",
]


def _detect_signposts(doc) -> Dict[str, Any]:
    """
    Count signposts and collect a few example sentences.
    """
    text_lower = doc.text.lower()
    signpost_count = 0
    for phrase in _SIGNPOST_PHRASES:
        signpost_count += text_lower.count(phrase)

    # Grab up to a few example sentences that contain signposts
    examples: List[str] = []
    for sent in doc.sents:
        sent_lower = sent.text.lower()
        if any(p in sent_lower for p in _SIGNPOST_PHRASES):
            examples.append(sent.text.strip())
            if len(examples) >= 5:
                break

    return {
        "signpost_count": signpost_count,
        "signpost_examples": examples,
    }


# --------------------------------------------------------
# Sentence statistics
# --------------------------------------------------------

def _sentence_stats(doc) -> Dict[str, Any]:
    """
    Compute:
      - number of sentences
      - average sentence length (tokens, excluding punct/space)
      - number of long sentences
    """
    sentence_lengths: List[int] = []

    for sent in doc.sents:
        # count "content" tokens, ignoring punctuation and spaces
        length = sum(
            1
            for token in sent
            if not token.is_punct and not token.is_space
        )
        if length > 0:
            sentence_lengths.append(length)

    if not sentence_lengths:
        return {
            "num_sentences": 0,
            "avg_sentence_length_tokens": 0.0,
            "long_sentence_count": 0,
            "long_sentence_threshold": 30,
        }

    long_threshold = 30  # e.g., > 30 tokens is "long"
    long_sentence_count = sum(1 for L in sentence_lengths if L > long_threshold)

    avg_len = float(sum(sentence_lengths) / len(sentence_lengths))

    return {
        "num_sentences": len(sentence_lengths),
        "avg_sentence_length_tokens": avg_len,
        "long_sentence_count": long_sentence_count,
        "long_sentence_threshold": long_threshold,
    }


# --------------------------------------------------------
# Label + score logic
# --------------------------------------------------------

def _label_and_score(
    num_sentences: int,
    signpost_count: int,
    long_sentence_count: int,
) -> tuple[str, int]:
    """
    Map structure stats to your required labels + scores.

    Labels (must match your spec):
      "unclear_structure",
      "mixed_structure",
      "mostly_clear_structure",
      "very_clear_structure"
    """

    if num_sentences <= 0:
        return "abstained", 0

    long_ratio = long_sentence_count / max(1, num_sentences)
    low_signposts = (signpost_count == 0)

    if low_signposts and long_ratio > 0.4:
        # no guidance + many long sentences → unclear
        return "unclear_structure", 45
    elif low_signposts and long_ratio <= 0.4:
        # not terrible, but hard to follow
        return "mixed_structure", 60
    elif not low_signposts and long_ratio > 0.4:
        # has signposts, but some sentences are heavy
        return "mostly_clear_structure", 75
    else:
        # has signposts and sentences are mostly manageable
        return "very_clear_structure", 90


def _feedback_from_label(label: str) -> str:
    """
    High-level textual feedback based on label.
    """
    if label == "unclear_structure":
        return (
            "Your talk structure is hard to follow: you rarely use signposts and several "
            "sentences are quite long. Try adding phrases like 'first', 'next', or "
            "'in summary', and break long sentences into smaller units."
        )
    if label == "mixed_structure":
        return (
            "Some parts of your structure are clear, but the flow could be improved. "
            "Consider using more explicit signposts and shortening long sentences."
        )
    if label == "mostly_clear_structure":
        return (
            "Your structure is mostly clear, with some room to improve. "
            "A few long sentences could be simplified, and extra signposts may help transitions."
        )
    if label == "very_clear_structure":
        return (
            "Your structure is very clear. You use signposts effectively and keep sentences "
            "at a readable length—this makes it easy for the audience to follow."
        )
    # abstained or unknown
    return "Insufficient data to evaluate content structure."


# --------------------------------------------------------
# Public entrypoint
# --------------------------------------------------------

def compute_content_structure_metric(
    transcript_text: str,
) -> Dict[str, Any]:
    """
    Compute the content_structure metric from the transcript text.

    Returns a dict matching your metric schema.
    """

    if not transcript_text or not transcript_text.strip():
        return {
            "score_0_100": None,
            "label": "abstained",
            "confidence": 0.0,
            "abstained": True,
            "details": {"reason": "empty_transcript"},
            "feedback": [],
        }

    nlp = _get_nlp()
    doc = nlp(transcript_text)

    sent_stats = _sentence_stats(doc)
    signpost_stats = _detect_signposts(doc)

    num_sentences = sent_stats["num_sentences"]
    signpost_count = signpost_stats["signpost_count"]
    long_sentence_count = sent_stats["long_sentence_count"]

    label, score = _label_and_score(
        num_sentences=num_sentences,
        signpost_count=signpost_count,
        long_sentence_count=long_sentence_count,
    )

    if label == "abstained":
        return {
            "score_0_100": None,
            "label": "abstained",
            "confidence": 0.0,
            "abstained": True,
            "details": {"reason": "no_sentences"},
            "feedback": [],
        }

    # For now, use a fixed heuristic confidence
    confidence = 0.75
    feedback_text = _feedback_from_label(label)

    metric = {
        "score_0_100": score,
        "label": label,
        "confidence": confidence,
        "abstained": False,
        "details": {
            "num_sentences": num_sentences,
            "avg_sentence_length_tokens": sent_stats["avg_sentence_length_tokens"],
            "long_sentence_threshold": sent_stats["long_sentence_threshold"],
            "long_sentence_count": long_sentence_count,
            "signpost_count": signpost_count,
            "signpost_examples": signpost_stats["signpost_examples"],
            "low_signposts": (signpost_count == 0),
            "many_long_sentences": (
                long_sentence_count / max(1, num_sentences) > 0.4
            ),
        },
        "feedback": [
            {
                "start_sec": 0.0,
                "end_sec": 0.0,  # structure is global, so we don't tie to a time span yet
                "message": feedback_text,
                "tip_type": "content_structure",
            }
        ],
    }

    return metric
