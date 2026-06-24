# Lab Guide: Multi-Agent Research System

## Scenario

Bạn cần xây dựng một research assistant có thể nhận câu hỏi dài, tìm thông tin, phân tích và viết câu trả lời cuối cùng. Lab yêu cầu so sánh hai cách làm:

1. **Single-agent baseline**: một agent làm toàn bộ.
2. **Multi-agent workflow**: Supervisor điều phối Researcher, Analyst, Writer.

## Quy tắc quan trọng

- Không thêm agent nếu không có lý do rõ ràng.
- Mỗi agent phải có responsibility riêng.
- Shared state phải đủ rõ để debug.
- Phải có trace hoặc log cho từng bước.
- Phải benchmark, không chỉ nhìn output bằng cảm tính.

## Milestone 1: Baseline

File gợi ý:

- `src/multi_agent_research_lab/cli.py`
- `src/multi_agent_research_lab/services/llm_client.py`

TODO(student): thay baseline placeholder bằng một call LLM thật.

## Milestone 2: Supervisor

File gợi ý:

- `src/multi_agent_research_lab/agents/supervisor.py`
- `src/multi_agent_research_lab/graph/workflow.py`

TODO(student): implement routing policy.

Gợi ý câu hỏi thiết kế:

- Khi nào gọi Researcher?
- Khi nào gọi Analyst?
- Khi nào gọi Writer?
- Khi nào stop?
- Nếu agent fail thì retry hay fallback?

## Milestone 3: Worker agents

File gợi ý:

- `agents/researcher.py`
- `agents/analyst.py`
- `agents/writer.py`

TODO(student): implement từng worker.

## Milestone 4: Trace và benchmark

File gợi ý:

- `observability/tracing.py`
- `evaluation/benchmark.py`
- `evaluation/report.py`

Benchmark tối thiểu:

| Metric | Cách đo gợi ý |
|---|---|
| Latency | wall-clock time |
| Cost | token usage hoặc provider usage |
| Quality | rubric 0-10 do peer review |
| Citation coverage | số claims có source / tổng claims chính |
| Failure rate | số query fail / tổng query |

## Exit ticket

Mỗi nhóm trả lời 2 câu:

1. **Case nào nên dùng multi-agent? Vì sao?**
   - **Trả lời**: Nên dùng multi-agent cho các tác vụ nghiên cứu chuyên sâu, phức tạp, đòi hỏi sự phối hợp của nhiều kỹ năng chuyên biệt (như thu thập dữ liệu thô, đối chiếu mâu thuẫn lập luận, kiểm chứng thực tế và định hình văn phong theo đối tượng độc giả). Phân chia vai trò giúp nâng cao độ chính xác của trích dẫn (như đã thấy trong benchmark, tỷ lệ trích dẫn đạt 5/5 nguồn so với 0/0 ở single-agent) và cải thiện chất lượng tổng thể nhờ có khâu phản biện (Analyst/Critic).

2. **Case nào không nên dùng multi-agent? Vì sao?**
   - **Trả lời**: Không nên dùng multi-agent cho các truy vấn đơn giản, các tác vụ yêu cầu phản hồi thời gian thực (real-time/low latency) hoặc ngân sách chi phí hạn chế. Chạy hệ thống multi-agent làm tăng thời gian xử lý (latency tăng từ ~10s lên ~83s) và chi phí token (cost tăng gấp 8-10 lần) do luồng xử lý qua nhiều bước định tuyến trung gian và liên tục truyền chuyển shared state giữa các agent.

