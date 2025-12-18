"""
Test the content_structure metric.
"""

from analyzer.metrics.content_structure import compute_content_structure_metric

def test_content_structure():
    print("=" * 60)
    print("CONTENT STRUCTURE METRIC TESTS")
    print("=" * 60)
    
    # Test 1: Good structure (signposts + short sentences)
    print("\n1. Good structure (signposts + short sentences):")
    text1 = """
    First, let me introduce the topic. Machine learning is changing the world.
    Second, we'll discuss neural networks. They are very powerful.
    Finally, I'll conclude with future directions. Thank you for listening.
    """
    result1 = compute_content_structure_metric(text1)
    print(f"   Score: {result1['score_0_100']}/100")
    print(f"   Label: {result1['label']}")
    print(f"   Signposts: {result1['details']['signpost_count']}")
    print(f"   Sentences: {result1['details']['num_sentences']}")
    print(f"   Avg length: {result1['details']['avg_sentence_length_tokens']:.1f} tokens")
    print(f"   Feedback: {result1['feedback'][0]['message'][:80]}...")
    
    # Test 2: Poor structure (no signposts + long sentences)
    print("\n2. Poor structure (no signposts + long sentences):")
    text2 = """
    The implementation of machine learning algorithms in production systems requires 
    careful consideration of numerous factors including but not limited to data quality 
    preprocessing techniques model selection hyperparameter tuning deployment infrastructure 
    monitoring and maintenance procedures all of which must be carefully orchestrated to 
    ensure optimal performance and reliability in real-world applications where unexpected 
    edge cases and data drift can significantly impact model accuracy over time.
    """
    result2 = compute_content_structure_metric(text2)
    print(f"   Score: {result2['score_0_100']}/100")
    print(f"   Label: {result2['label']}")
    print(f"   Signposts: {result2['details']['signpost_count']}")
    print(f"   Long sentences: {result2['details']['long_sentence_count']}")
    print(f"   Feedback: {result2['feedback'][0]['message'][:80]}...")
    
    # Test 3: Mixed (has signposts but long sentences)
    print("\n3. Mixed (has signposts but long sentences):")
    text3 = """
    First, I want to talk about the implementation of machine learning algorithms in 
    production systems which requires careful consideration of numerous factors including 
    but not limited to data quality preprocessing techniques model selection hyperparameter 
    tuning and deployment infrastructure. However, we must also consider monitoring and 
    maintenance procedures all of which must be carefully orchestrated to ensure optimal 
    performance. In conclusion, these are complex topics that need attention.
    """
    result3 = compute_content_structure_metric(text3)
    print(f"   Score: {result3['score_0_100']}/100")
    print(f"   Label: {result3['label']}")
    print(f"   Signposts: {result3['details']['signpost_count']}")
    print(f"   Long sentences: {result3['details']['long_sentence_count']}")
    
    # Test 4: Empty transcript (should abstain)
    print("\n4. Empty transcript (should abstain):")
    result4 = compute_content_structure_metric("")
    print(f"   Abstained: {result4['abstained']}")
    print(f"   Reason: {result4['details']['reason']}")
    
    # Test 5: Real-world example with various signposts
    print("\n5. Real-world example with various signposts:")
    text5 = """
    Today I'll discuss three main topics. First, the background of our research.
    We started by analyzing existing solutions. For example, traditional methods
    have limitations. However, our approach is different. Moreover, we achieved
    better results. In addition, the system is more efficient. Therefore, we
    recommend this approach. In conclusion, this represents a significant advance.
    """
    result5 = compute_content_structure_metric(text5)
    print(f"   Score: {result5['score_0_100']}/100")
    print(f"   Label: {result5['label']}")
    print(f"   Signposts found: {result5['details']['signpost_count']}")
    print(f"   Examples: {result5['details']['signpost_examples'][:3]}")
    
    print("\n" + "=" * 60)
    print("ALL TESTS COMPLETED")
    print("=" * 60)

if __name__ == "__main__":
    test_content_structure()
