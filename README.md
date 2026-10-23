# Tự tạo AI Agent từ đầu (ReAct)

Một AI Agent viết từ đầu bằng Python, theo vòng lặp **ReAct**
(Yao et al., 2023) — không dùng LangChain hay bất kỳ framework agent nào,
chỉ dùng Anthropic SDK.

Agent trả lời câu hỏi:

> Dân số Trung Quốc và Ấn Độ, nước nào đông hơn, hơn bao nhiêu người,
> và theo nguồn nào?

Để trả lời được, agent có hai tool và một vòng lặp:

- `search` — tra dân số một nước theo mã ISO3 và năm, từ World Bank
- `calculator` — tính một biểu thức số học
- vòng lặp chạy đến khi mô hình trả về câu trả lời cuối (`stop_reason != "tool_use"`)

## Chạy

Cần `ANTHROPIC_API_KEY` trong môi trường:

```bash
export ANTHROPIC_API_KEY=sk-ant-...
make run
```

`make run` dùng `uv` để chạy kèm thư viện `anthropic`:

```bash
uv run --with anthropic python agent.py
```

Nếu không dùng `uv`:

```bash
pip install anthropic
python agent.py
```

## Ba paper nền tảng

Ý tưởng trong code đến từ ba paper:

- **Chain-of-Thought** — Wei et al., 2022 — <https://arxiv.org/abs/2201.11903>
- **MRKL** — Karpas et al., 2022 — <https://arxiv.org/abs/2205.00445>
- **ReAct** — Yao et al., 2023 — <https://arxiv.org/abs/2210.03629>

## Cấu trúc

Toàn bộ agent nằm trong một file `agent.py`: khai báo hai tool, schema cho
mô hình, và vòng lặp ReAct. Phần quyết định gọi tool nào, khi nào dừng,
nằm hoàn toàn ở mô hình — code chỉ cấp tool rồi lặp.
