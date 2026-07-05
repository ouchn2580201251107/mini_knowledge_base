import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from qa_system import KnowledgeBase


def test_boundary_detailed():
    kb = KnowledgeBase()
    print("=" * 70)
    print("边界值测试详细分析报告")
    print("=" * 70)

    print("\n" + "-" * 70)
    print("1. 关键词长度边界测试")
    print("-" * 70)
    
    length_tests = [
        ("人", "单字"),
        ("AI", "双字母缩写"),
        ("机器学习", "四字专业术语"),
        ("卷积神经网络", "六字专业术语"),
        ("长短期记忆网络", "八字专业术语"),
    ]
    
    for query, desc in length_tests:
        keywords = kb.extract_keywords(query)
        answer = kb.get_answer(query)
        matched = kb.match_question(query)
        print(f"\n输入: '{query}' ({desc})")
        print(f"  提取关键词: {keywords}")
        print(f"  匹配问题: {matched[:30] if matched else '无'}")
        print(f"  答案: {'有' if answer else '无'}")

    print("\n" + "-" * 70)
    print("2. 相近关键词区分测试")
    print("-" * 70)
    
    similar_tests = [
        ("机器学习", "深度学习"),
        ("监督学习", "非监督学习"),
        ("CNN", "RNN"),
        ("LSTM", "GRU"),
        ("TensorFlow", "PyTorch"),
        ("BERT", "GPT"),
        ("分类", "聚类"),
        ("回归", "分类"),
        ("过拟合", "欠拟合"),
        ("数据挖掘", "机器学习"),
    ]
    
    for query, similar in similar_tests:
        keywords = kb.extract_keywords(query)
        answer = kb.get_answer(query)
        matched = kb.match_question(query)
        similar_answer = kb.get_answer(similar)
        similar_matched = kb.match_question(similar)
        
        print(f"\n输入: '{query}'")
        print(f"  提取关键词: {keywords}")
        print(f"  匹配问题: {matched[:30] if matched else '无'}")
        print(f"  答案: {'有' if answer else '无'}")
        
        print(f"\n相似输入: '{similar}'")
        print(f"  匹配问题: {similar_matched[:30] if similar_matched else '无'}")
        print(f"  答案: {'有' if similar_answer else '无'}")
        
        if matched and similar_matched:
            same = matched == similar_matched
            print(f"  是否匹配同一问题: {'是' if same else '否'}")

    print("\n" + "-" * 70)
    print("3. 多关键词组合测试")
    print("-" * 70)
    
    combo_tests = [
        ("机器学习算法", ["机器学习", "算法"]),
        ("深度学习框架", ["深度学习", "框架"]),
        ("Python机器学习", ["Python", "机器学习"]),
        ("TensorFlow深度学习", ["TensorFlow", "深度学习"]),
        ("监督学习分类算法", ["监督学习", "分类", "算法"]),
        ("计算机视觉图像识别", ["计算机视觉", "图像识别"]),
        ("自然语言处理文本分类", ["自然语言处理", "文本分类"]),
        ("AI伦理安全监管", ["AI", "伦理", "安全", "监管"]),
    ]
    
    for query, expected_kws in combo_tests:
        keywords = kb.extract_keywords(query)
        answer = kb.get_answer(query)
        matched = kb.match_question(query)
        
        print(f"\n输入: '{query}'")
        print(f"  预期关键词: {expected_kws}")
        print(f"  实际提取: {keywords}")
        print(f"  匹配问题: {matched[:40] if matched else '无'}")
        print(f"  答案: {'有' if answer else '无'}")

    print("\n" + "-" * 70)
    print("4. 噪声与干扰测试")
    print("-" * 70)
    
    noise_tests = [
        ("什么是机器学习啊", "末尾语气词"),
        ("嗯，我想问一下深度学习", "开头语气词"),
        ("机器学习...是什么？", "省略号"),
        ("【机器学习】入门", "括号"),
        ("机器学习_入门", "下划线"),
        ("机器学习/深度学习", "斜杠"),
        ("机器学习和深度学习", "和"),
        ("机器学习还是深度学习", "还是"),
    ]
    
    for query, desc in noise_tests:
        keywords = kb.extract_keywords(query)
        answer = kb.get_answer(query)
        matched = kb.match_question(query)
        
        print(f"\n输入: '{query}' ({desc})")
        print(f"  提取关键词: {keywords}")
        print(f"  匹配问题: {matched[:30] if matched else '无'}")
        print(f"  答案: {'有' if answer else '无'}")

    print("\n" + "-" * 70)
    print("5. 权重分析")
    print("-" * 70)
    
    test_keywords = ["机器学习", "深度学习", "LSTM", "TensorFlow", "定义", "概念", "基础"]
    print(f"关键词权重分析:")
    for kw in test_keywords:
        weight = kb.keyword_weights.get(kw, 0)
        print(f"  {kw}: {weight:.3f}")

    print("\n" + "=" * 70)
    print("测试完成")
    print("=" * 70)


if __name__ == "__main__":
    test_boundary_detailed()
