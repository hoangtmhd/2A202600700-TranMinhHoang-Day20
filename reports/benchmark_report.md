# Báo cáo Benchmark: Single-Agent vs Multi-Agent

Báo cáo này so sánh hiệu năng của giải pháp Đơn tác nhân (Single-Agent Baseline) và Đa tác nhân (Multi-Agent Workflow) dựa trên các tiêu chí: Tốc độ xử lý (Latency), Chi phí token ước tính (Cost) và Chất lượng nội dung đánh giá bởi LLM-as-a-judge (Quality).

| Run | Latency (s) | Cost (USD) | Quality | Notes |
|---|---:|---:|---:|---|
| Single-Agent Baseline | 10.72s | $0.000250 | 7.0/10 | Cited 0/0 sources. | Feedback: The report offers an excellent, well-structured, and in-depth overview of GraphRAG's state-of-the-art, but it significantly lacks any citations to support its claims and demonstrate academic rigor. |
| Multi-Agent Workflow | 83.27s | $0.002053 | 8.8/10 | Cited 5/5 sources. | Feedback: The report provides a comprehensive and well-structured overview of GraphRAG, covering its pipeline, advantages, state-of-the-art implementations, and future directions with excellent clarity and citation usage, though it significantly exceeds the requested 500-word limit. |

## Phân tích kết quả thực nghiệm

- **Chất lượng câu trả lời (Quality Score)**: Hệ thống Multi-Agent thường có điểm chất lượng cao hơn nhờ có sự tách biệt vai trò rõ ràng: Researcher thu thập dữ liệu chuyên biệt, Analyst phản biện lập luận, và Writer chải chuốt văn phong.
- **Thời gian xử lý (Latency)**: Do phải trải qua nhiều bước gọi LLM trung gian và định tuyến, hệ thống Multi-Agent có độ trễ lớn hơn đáng kể so với Single-Agent.
- **Chi phí (Cost)**: Số lượng token tiêu thụ của Multi-Agent lớn hơn nhiều do phải truyền đi truyền lại context (shared state) qua nhiều agent khác nhau.

## Traces & Observability
Hệ thống đã được tích hợp và ghi nhận vết thực thi chi tiết trên nền tảng Langfuse giúp theo dõi trực quan cấu trúc cuộc gọi và hiệu năng của từng node.
