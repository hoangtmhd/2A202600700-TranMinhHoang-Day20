# Design Template: Multi-Agent Research System

## Problem

Hệ thống cần xử lý các truy vấn nghiên cứu chuyên sâu, phức tạp từ người dùng (ví dụ: "Nghiên cứu tình trạng công nghệ GraphRAG hiện nay và viết báo cáo tóm tắt 500 từ"). Hệ thống phải tự tìm kiếm thông tin trên internet, phân tích đối chiếu tài liệu, và tổng hợp thành một báo cáo hoàn chỉnh có trích dẫn nguồn uy tín.

## Why multi-agent?

Đối với các yêu cầu nghiên cứu phức tạp:
1. **Single-agent** thường gặp khó khăn do phải đảm nhận quá nhiều vai trò cùng lúc (vừa tìm kiếm, vừa đánh giá dữ liệu, vừa viết bài), dễ dẫn đến tình trạng bỏ sót thông tin, lập luận thiếu khách quan, trích dẫn không chính xác hoặc thậm chí bị ảo tưởng (hallucination).
2. **Multi-agent** cho phép chia nhỏ bài toán thành các chuyên gia chuyên biệt (Separation of Concerns):
   - **Researcher** tập trung hoàn toàn vào thu thập facts và trích xuất nguồn.
   - **Analyst** phản biện lập luận, đối chiếu góc nhìn khách quan và phát hiện lỗi bằng chứng.
   - **Writer** chau chuốt từ ngữ, định hình cấu trúc và định hướng đúng độc giả.
   - **Supervisor** điều phối thông minh giúp quy trình lặp đi lặp lại linh hoạt cho đến khi đạt chất lượng mong muốn.

## Agent roles

| Agent | Responsibility | Input | Output | Failure mode |
|---|---|---|---|---|
| **Supervisor** | Điều phối luồng làm việc của các Agent dựa trên State hiện tại; định tuyến động tới Agent tiếp theo hoặc kết thúc. | `ResearchState` (lịch sử chạy, trạng thái các ghi chú) | Tên của Agent tiếp theo (`next`) kèm lý do điều phối. | Đưa ra quyết định định tuyến vòng lặp vô hạn hoặc sai địa chỉ. |
| **Researcher** | Tìm kiếm dữ liệu internet bằng Tavily API, lọc các nguồn chất lượng và viết ghi chú nghiên cứu thô. | `ResearchState` và câu hỏi truy vấn | `state.research_notes` và danh sách `state.sources`. | Tavily API bị rate limit hoặc không tìm thấy dữ liệu liên quan. |
| **Analyst** | Phân tích các ghi chú thô, trích xuất luận điểm chính, tìm xung đột thông tin và cảnh báo luận cứ yếu. | `state.research_notes` | `state.analysis_notes` | Bỏ sót các mâu thuẫn chính hoặc phân tích hời hợt. |
| **Writer** | Tổng hợp từ ghi chú nghiên cứu & phân tích để viết báo cáo hoàn chỉnh đáp ứng đúng đối tượng độc giả. | `state.research_notes` và `state.analysis_notes` | `state.final_answer` (chứa References) | Báo cáo viết quá dài, sai văn phong hoặc trích dẫn sai số thứ tự. |
| **Critic** | (Tùy chọn) Kiểm tra chéo chất lượng bài viết và tính chính xác của các trích dẫn so với nguồn gốc. | `state.final_answer` và `state.sources` | Đánh giá phản biện (ghi nhận trong `agent_results`). | Phản biện quá khắt khe gây vòng lặp vô hạn. |

## Shared state

Hệ thống sử dụng một State tập trung làm nguồn chân lý duy nhất (Single Source of Truth) kế thừa từ Pydantic `BaseModel`:
- `request`: Chứa câu hỏi nghiên cứu, số lượng nguồn tối đa, và độc giả mục tiêu.
- `iteration` & `route_history`: Theo dõi số bước chạy và lịch sử định tuyến để áp dụng guardrails.
- `sources`: Danh sách tài liệu thô được tìm kiếm để đối chiếu trích dẫn.
- `research_notes` & `analysis_notes`: Bộ nhớ đệm lưu thông tin thô và phân tích giúp các Agent chuyển giao context.
- `final_answer`: Báo cáo kết quả cuối cùng.
- `agent_results`: Ghi nhận log chi phí, token tiêu thụ của từng Agent để phục vụ benchmark.
- `errors` & `trace`: Giám sát sự kiện và ghi nhận lỗi hệ thống.

## Routing policy

Sử dụng LangGraph StateGraph với luồng định tuyến động dựa trên Supervisor:
1. `START` -> `supervisor`.
2. `supervisor` phân tích State hiện tại qua LLM:
   - Nếu thiếu nghiên cứu -> gọi `researcher` -> quay lại `supervisor`.
   - Nếu thiếu phân tích -> gọi `analyst` -> quay lại `supervisor`.
   - Nếu đã có đủ dữ liệu -> gọi `writer` -> gọi `critic` -> quay lại `supervisor`.
   - Nếu báo cáo đã đạt chất lượng và đầy đủ -> định tuyến sang `END` (kết thúc).

## Guardrails

- **Max iterations**: Giới hạn tối đa 6 lượt lặp để tránh lặp vô hạn và bảo vệ chi phí API.
- **Timeout**: Thiết lập giới hạn thời gian chạy cho mỗi cuộc gọi LLM/Search Client.
- **Retry**: Sử dụng thư viện `tenacity` để tự động thử lại (exponential backoff) tối đa 3 lần khi API LLM/Tavily gặp sự cố kết nối hoặc Rate Limit.
- **Fallback**: Tự động chuyển hướng về Mock Search Data nếu Tavily Search gặp lỗi để bảo toàn tiến trình chạy.
- **Validation**: Kiểm tra tính hợp lệ của schema dữ liệu qua Pydantic.

## Benchmark plan

- **Queries thử nghiệm**:
  - *"Research GraphRAG state-of-the-art and write a 500-word summary"*
- **Các chỉ số (Metrics) đo lường**:
  - **Latency**: Thời gian thực thi thực tế bằng giây.
  - **Cost**: Chi phí USD ước tính dựa trên số lượng token input/output của Gemini.
  - **Quality**: Điểm số đánh giá chất lượng (0-10) thực hiện tự động bằng LLM-as-a-judge.
  - **Citation coverage**: Số lượng nguồn thực sự được trích dẫn trong văn bản cuối cùng.
  - **Failure rate**: Tỷ lệ lỗi phát sinh trong quá trình chạy.
