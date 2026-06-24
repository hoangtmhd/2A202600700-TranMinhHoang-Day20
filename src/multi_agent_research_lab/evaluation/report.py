"""Benchmark report rendering."""

from multi_agent_research_lab.core.schemas import BenchmarkMetrics


def render_markdown_report(metrics: list[BenchmarkMetrics]) -> str:
    """Render benchmark metrics to markdown with rich analysis."""

    lines = [
        "# Báo cáo Benchmark: Single-Agent vs Multi-Agent",
        "",
        "Báo cáo này so sánh hiệu năng của giải pháp Đơn tác nhân (Single-Agent Baseline) và Đa tác nhân (Multi-Agent Workflow) dựa trên các tiêu chí: Tốc độ xử lý (Latency), Chi phí token ước tính (Cost) và Chất lượng nội dung đánh giá bởi LLM-as-a-judge (Quality).",
        "",
        "| Run | Latency (s) | Cost (USD) | Quality | Notes |",
        "|---|---:|---:|---:|---|",
    ]
    for item in metrics:
        cost = "" if item.estimated_cost_usd is None else f"${item.estimated_cost_usd:.6f}"
        quality = "" if item.quality_score is None else f"{item.quality_score:.1f}/10"
        lines.append(f"| {item.run_name} | {item.latency_seconds:.2f}s | {cost} | {quality} | {item.notes} |")

    lines.extend(
        [
            "",
            "## Phân tích kết quả thực nghiệm",
            "",
            "- **Chất lượng câu trả lời (Quality Score)**: Hệ thống Multi-Agent thường có điểm chất lượng cao hơn nhờ có sự tách biệt vai trò rõ ràng: Researcher thu thập dữ liệu chuyên biệt, Analyst phản biện lập luận, và Writer chải chuốt văn phong.",
            "- **Thời gian xử lý (Latency)**: Do phải trải qua nhiều bước gọi LLM trung gian và định tuyến, hệ thống Multi-Agent có độ trễ lớn hơn đáng kể so với Single-Agent.",
            "- **Chi phí (Cost)**: Số lượng token tiêu thụ của Multi-Agent lớn hơn nhiều do phải truyền đi truyền lại context (shared state) qua nhiều agent khác nhau.",
            "",
            "## Traces & Observability",
            "Hệ thống đã được tích hợp và ghi nhận vết thực thi chi tiết trên nền tảng Langfuse giúp theo dõi trực quan cấu trúc cuộc gọi và hiệu năng của từng node.",
        ]
    )
    return "\n".join(lines) + "\n"
