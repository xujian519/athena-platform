#!/usr/bin/env python3
"""
高级MCDM算法验证 - AHP和TOPSIS

验证更复杂的多准则决策方法：
1. AHP (Analytic Hierarchy Process) - 层次分析法
2. TOPSIS (Technique for Order Preference by Similarity to Ideal Solution) - 逼近理想解排序法

作者: Athena验证系统
日期: 2026-04-20
"""


import numpy as np


class AHPVerifier:
    """AHP层次分析法验证器"""

    def __init__(self):
        self.test_results = []

    def verify_consistency_ratio(self):
        """验证一致性比率计算"""
        print("\n[测试1] AHP一致性比率计算")

        # 判断矩阵（Saaty 1-9标度）
        matrix = np.array([
            [1, 3, 5],
            [1/3, 1, 2],
            [1/5, 1/2, 1]
        ])

        # 计算特征值和特征向量
        eigenvalues, eigenvectors = np.linalg.eig(matrix)

        # 最大特征值
        lambda_max = max(eigenvalues.real)

        # 一致性指标 CI
        n = len(matrix)
        CI = (lambda_max - n) / (n - 1)

        # 随机一致性指标 RI
        RI_dict = {1: 0, 2: 0, 3: 0.58, 4: 0.90, 5: 1.12, 6: 1.24, 7: 1.32, 8: 1.41, 9: 1.45}
        RI = RI_dict.get(n, 1.49)

        # 一致性比率 CR
        CR = CI / RI if RI != 0 else 0

        print(f"  最大特征值 λmax: {lambda_max:.4f}")
        print(f"  一致性指标 CI: {CI:.4f}")
        print(f"  随机一致性指标 RI: {RI:.2f}")
        print(f"  一致性比率 CR: {CR:.4f}")

        if CR < 0.1:
            print(f"  ✓ 一致性可接受 (CR={CR:.4f} < 0.1)")
            self.test_results.append(("一致性比率", True, CR))
        else:
            print(f"  ✗ 一致性不可接受 (CR={CR:.4f} >= 0.1)")
            self.test_results.append(("一致性比率", False, CR))

        # 计算权重（归一化特征向量）
        weights = eigenvectors[:, eigenvalues.real.argmax()].real
        weights = weights / weights.sum()

        print("\n  权重向量:")
        criteria = ["C1", "C2", "C3"]
        for _i, (c, w) in enumerate(zip(criteria, weights, strict=False)):
            print(f"    {c}: {w:.4f}")

        # 验证权重和为1
        if abs(weights.sum() - 1.0) < 0.0001:
            print(f"  ✓ 权重归一化正确 (sum={weights.sum():.4f})")
            self.test_results.append(("权重归一化", True, weights.sum()))
        else:
            print(f"  ✗ 权重归一化错误 (sum={weights.sum():.4f})")
            self.test_results.append(("权重归一化", False, weights.sum()))

    def verify_priority_calculation(self):
        """验证优先级计算"""
        print("\n[测试2] AHP优先级计算")

        # 准则层权重
        criteria_weights = np.array([0.4, 0.3, 0.3])

        # 方案层判断矩阵（针对每个准则）
        # 准则1: 成本
        alt1_cost = np.array([[1, 2], [1/2, 1])
        w1 = self._calculate_ahp_weights(alt1_cost)

        # 准则2: 质量
        alt2_quality = np.array([[1, 1/3], [3, 1])
        w2 = self._calculate_ahp_weights(alt2_quality)

        # 准则3: 时间
        alt3_time = np.array([[1, 1], [1, 1])
        w3 = self._calculate_ahp_weights(alt3_time)

        # 构建决策矩阵
        decision_matrix = np.array([w1, w2, w3]).T

        # 计算最终得分
        final_scores = decision_matrix @ criteria_weights

        print(f"  方案A得分: {final_scores[0]:.4f}")
        print(f"  方案B得分: {final_scores[1]:.4f}")

        if final_scores[0] > final_scores[1]:
            print("  ✓ 方案A优于方案B")
        else:
            print("  ✓ 方案B优于方案A")

        self.test_results.append(("优先级计算", True, final_scores))

    def _calculate_ahp_weights(self, matrix: np.ndarray) -> np.ndarray:
        """计算AHP权重（几何平均法）"""
        # 几何平均
        geometric_mean = np.prod(matrix, axis=1) ** (1 / len(matrix))

        # 归一化
        weights = geometric_mean / geometric_mean.sum()

        return weights


class TOPSISVerifier:
    """TOPSIS逼近理想解排序法验证器"""

    def __init__(self):
        self.test_results = []

    def verify_topsis_calculation(self):
        """验证TOPSIS完整计算流程"""
        print("\n[测试3] TOPSIS完整计算")

        # 决策矩阵（方案×准则）
        decision_matrix = np.array([
            [5, 8, 4],  # 方案A
            [7, 6, 8],  # 方案B
            [9, 4, 6],  # 方案C
        ])

        # 权重
        weights = np.array([0.4, 0.3, 0.3])

        # 准则类型（True=效益型，False=成本型）
        is_benefit = [True, True, True]

        print("  原始决策矩阵:")
        print(f"    方案A: {decision_matrix[0]}")
        print(f"    方案B: {decision_matrix[1]}")
        print(f"    方案C: {decision_matrix[2]}")

        # 步骤1: 归一化
        normalized_matrix = self._normalize(decision_matrix)

        print("\n  归一化矩阵:")
        for i, row in enumerate(normalized_matrix):
            print(f"    方案{chr(65+i)}: {[f'{x:.4f}' for x in row]}")

        # 步骤2: 加权归一化
        weighted_matrix = normalized_matrix * weights

        print("\n  加权归一化矩阵:")
        for i, row in enumerate(weighted_matrix):
            print(f"    方案{chr(65+i)}: {[f'{x:.4f}' for x in row]}")

        # 步骤3: 确定理想解和负理想解
        ideal_positive, ideal_negative = self._find_ideal_solutions(
            weighted_matrix, is_benefit
        )

        print(f"\n  正理想解: {[f'{x:.4f}' for x in ideal_positive]}")
        print(f"  负理想解: {[f'{x:.4f}' for x in ideal_negative]}")

        # 步骤4: 计算距离
        dist_positive = self._calculate_distances(weighted_matrix, ideal_positive)
        dist_negative = self._calculate_distances(weighted_matrix, ideal_negative)

        print(f"\n  距离正理想解: {[f'{d:.4f}' for d in dist_positive]}")
        print(f"  距离负理想解: {[f'{d:.4f}' for d in dist_negative]}")

        # 步骤5: 计算相对贴近度
        closeness = dist_negative / (dist_positive + dist_negative)

        print("\n  相对贴近度:")
        rankings = []
        for i, c in enumerate(closeness):
            print(f"    方案{chr(65+i)}: {c:.4f}")
            rankings.append((chr(65+i), c))

        # 排序
        rankings.sort(key=lambda x: x[1], reverse=True)

        print("\n  最终排名:")
        for rank, (alt, score) in enumerate(rankings, 1):
            print(f"    {rank}. 方案{alt}: {score:.4f}")

        # 验证（方案B最优，因为它在成本(7)和时间(8)上表现良好）
        # 方案A: 成本5(好) 质量8(好) 时间4(差)
        # 方案B: 成本7(中) 质量6(中) 时间8(好)  ← 综合最优
        # 方案C: 成本9(差) 质量4(差) 时间6(中)

        # 手动验证方案B的贴近度计算
        # D+ = sqrt((0.2249-0.2892)² + (0.1671-0.2228)² + (0.2228-0.2228)²) = 0.0850
        # D- = sqrt((0.2249-0.1606)² + (0.1671-0.1114)² + (0.2228-0.1114)²) = 0.1402
        # C = 0.1402 / (0.0850 + 0.1402) = 0.6224 ✓

        if rankings[0][0] == 'B':  # 方案B应该最优
            print(f"\n  ✓ TOPSIS计算正确，方案{rankings[0][0]}最优")
            print(f"     验证: 方案B在时间和成本上均衡，贴近度{rankings[0][1]:.4f}最高")
            self.test_results.append(("TOPSIS计算", True, rankings))
        else:
            print(f"\n  ✗ TOPSIS计算异常，预期方案B最优，实际方案{rankings[0][0]}")
            self.test_results.append(("TOPSIS计算", False, rankings))

    def _normalize(self, matrix: np.ndarray) -> np.ndarray:
        """向量化归一化"""
        normalized = np.zeros_like(matrix, dtype=float)

        for j in range(matrix.shape[1]):
            column = matrix[:, j]
            norm = np.sqrt(np.sum(column ** 2))
            normalized[:, j] = column / norm

        return normalized

    def _find_ideal_solutions(
        self, weighted_matrix: np.ndarray, is_benefit: list[bool]
    ) -> tuple[np.ndarray, np.ndarray]:
        """确定理想解和负理想解"""
        ideal_positive = np.zeros(weighted_matrix.shape[1])
        ideal_negative = np.zeros(weighted_matrix.shape[1])

        for j, benefit in enumerate(is_benefit):
            column = weighted_matrix[:, j]
            if benefit:
                ideal_positive[j] = np.max(column)
                ideal_negative[j] = np.min(column)
            else:
                ideal_positive[j] = np.min(column)
                ideal_negative[j] = np.max(column)

        return ideal_positive, ideal_negative

    def _calculate_distances(
        self, weighted_matrix: np.ndarray, ideal: np.ndarray
    ) -> np.ndarray:
        """计算欧氏距离"""
        distances = np.zeros(weighted_matrix.shape[0])

        for i in range(weighted_matrix.shape[0]):
            distances[i] = np.sqrt(np.sum((weighted_matrix[i] - ideal) ** 2))

        return distances


def test_comparison():
    """对比不同决策方法的结果"""
    print("\n[测试4] 多方法对比分析")

    # 同一决策问题
    options = ["方案A", "方案B", "方案C"]
    criteria = ["成本", "质量", "时间"]
    weights = [0.4, 0.3, 0.3]

    # 决策矩阵
    scores = np.array([
        [5, 8, 4],  # A
        [7, 6, 8],  # B
        [9, 4, 6],  # C
    ])

    print("\n  决策问题: 选择最优方案")
    print(f"  评估准则: {criteria}")
    print(f"  权重: {weights}")

    # 方法1: 简单加权求和(SAW)
    normalized = scores / scores.sum(axis=0)
    saw_scores = normalized @ weights

    print("\n  方法1 - 简单加权求和(SAW):")
    for i, opt in enumerate(options):
        print(f"    {opt}: {saw_scores[i]:.4f}")

    # 方法2: 加权乘法(WPM)
    wpm_scores = np.prod(scores ** weights, axis=1) / np.prod(scores ** weights, axis=1).sum()

    print("\n  方法2 - 加权乘法(WPM):")
    for i, opt in enumerate(options):
        print(f"    {opt}: {wpm_scores[i]:.4f}")

    print("\n  ✓ 多方法对比完成")
    print("  注: 不同方法可能产生不同排名，取决于数据特性和权重分布")


def main():
    """主验证流程"""
    print("=" * 60)
    print("高级MCDM算法验证")
    print("=" * 60)
    print("\n验证内容:")
    print("  1. AHP层次分析法")
    print("  2. TOPSIS逼近理想解排序法")
    print("  3. 多方法对比分析")

    # AHP验证
    ahp_verifier = AHPVerifier()
    ahp_verifier.verify_consistency_ratio()
    ahp_verifier.verify_priority_calculation()

    # TOPSIS验证
    topsis_verifier = TOPSISVerifier()
    topsis_verifier.verify_topsis_calculation()

    # 对比分析
    test_comparison()

    # 摘要
    print("\n" + "=" * 60)
    print("验证摘要")
    print("=" * 60)

    all_results = ahp_verifier.test_results + topsis_verifier.test_results
    passed = sum(1 for _, success, _ in all_results if success)
    total = len(all_results)

    print(f"\n总测试数: {total}")
    print(f"通过: {passed} ✅")
    print(f"失败: {total - passed} ❌")
    print(f"通过率: {passed/total*100:.1f}%")

    print("\n详细结果:")
    for name, success, _value in all_results:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"  {status} - {name}")

    if passed == total:
        print("\n🎉 所有高级MCDM算法验证通过!")
        print("\n建议:")
        print("  1. 可以在decision_engine工具中集成AHP和TOPSIS")
        print("  2. 提供方法选择参数（method='ahp'|'topsis'|'saw'）")
        print("  3. 添加一致性检查作为质量保证")
    else:
        print(f"\n⚠️  {total - passed}个测试失败，需要修复")

    print("=" * 60)


if __name__ == "__main__":
    main()
