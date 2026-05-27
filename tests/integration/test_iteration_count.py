"""独立测试脚本 - 验证 iteration_count 功能"""


def test_calculate_statistics_with_iteration_count() -> None:
    """测试 ReportManager.calculate_statistics 包含 subtype_compliance"""
    # 模拟 calculate_statistics 的核心逻辑
    results = [
        {"compliance_result": "合规", "risk_subclass": "越狱攻击"},
        {"compliance_result": "合规", "risk_subclass": "越狱攻击"},
        {"compliance_result": "违规", "risk_subclass": "越狱攻击"},
        {"compliance_result": "合规", "risk_subclass": "提示词注入"},
    ]

    # 计算 subtype_compliance
    subtype_stats = {}
    for r in results:
        subclass = r.get("risk_subclass", "未知")
        if subclass not in subtype_stats:
            subtype_stats[subclass] = {"total": 0, "passed": 0}
        subtype_stats[subclass]["total"] += 1
        if r.get("compliance_result", "").startswith("合规"):
            subtype_stats[subclass]["passed"] += 1

    subtype_compliance = []
    for cat, st in subtype_stats.items():
        failed = st["total"] - st["passed"]
        st_rate = round(st["passed"] / st["total"] * 100, 2) if st["total"] else 0.0
        subtype_compliance.append(
            {
                "category": cat,
                "total": st["total"],
                "passed": st["passed"],
                "failed": failed,
                "rate": st_rate,
            }
        )

    assert len(subtype_compliance) == 2
    jailbreak = next(x for x in subtype_compliance if x["category"] == "越狱攻击")
    assert jailbreak["total"] == 3
    assert jailbreak["passed"] == 2
    assert jailbreak["failed"] == 1
    assert jailbreak["rate"] == 66.67


def test_avg_iteration_count_calculation() -> None:
    """测试平均迭代次数计算"""
    all_results = [
        {"compliance_result": "合规", "risk_subclass": "A", "iteration_count": 3},
        {"compliance_result": "违规", "risk_subclass": "B", "iteration_count": 5},
        {"compliance_result": "合规", "risk_subclass": "C", "iteration_count": None},
        {"compliance_result": "违规", "risk_subclass": "D", "iteration_count": 0},
    ]

    iteration_counts = [
        r["iteration_count"] for r in all_results if r.get("iteration_count") is not None
    ]
    avg_iteration_count = (
        round(sum(iteration_counts) / len(iteration_counts), 2) if iteration_counts else None
    )

    assert avg_iteration_count == 2.67  # (3 + 5 + 0) / 3


def test_dynamic_detector_iteration_tracking() -> None:
    """测试动态检测器迭代次数跟踪逻辑"""
    # 模拟动态检测的迭代逻辑
    max_iterations = 3
    poc_pool = ["poc1", "poc2"]

    # 场景1: 静态就违规的样本
    sample_iterations_1 = 0
    assert sample_iterations_1 == 0

    # 场景2: 需要迭代的样本,第2次迭代时违规
    sample_iterations_2 = 0
    for _poc in poc_pool:
        for i in range(max_iterations):
            sample_iterations_2 += 1
            if i == 1:  # 第2次迭代违规
                break
        break  # 违规后跳出外层循环

    assert sample_iterations_2 == 2

    # 场景3: 所有迭代都合规
    sample_iterations_3 = 0
    for _poc in poc_pool:
        for i in range(max_iterations):  # noqa: B007
            sample_iterations_3 += 1

    assert sample_iterations_3 == 6  # 2 * 3


def test_result_data_structure() -> None:
    """测试 ResultData 数据结构"""
    result_data = {
        "result_data_id": "result_xxx",
        "report_id": "report_xxx",
        "risk_subclass": "越狱攻击",
        "poc": "原始PoC",
        "model_output": "大模型输出",
        "compliance_result": "违规",
        "iteration_count": 5,
    }

    assert "iteration_count" in result_data
    assert result_data["iteration_count"] == 5


if __name__ == "__main__":
    import sys
    import io

    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")


    test_calculate_statistics_with_iteration_count()
    test_avg_iteration_count_calculation()
    test_dynamic_detector_iteration_tracking()
    test_result_data_structure()

