"""Một AI Agent viết từ đầu, theo vòng lặp ReAct (Yao et al., 2023).

Không dùng LangChain hay bất kỳ framework agent nào — chỉ Anthropic SDK.
Hai tool: search tra dân số từ World Bank, calculator làm phép tính.
"""

import json
import re
import textwrap
import urllib.request

import anthropic

MODEL = "claude-sonnet-4-6"
CAU_HOI = (
    "Dân số Trung Quốc và Ấn Độ, nước nào đông hơn, "
    "hơn bao nhiêu người, và theo nguồn nào?"
)
WB = (
    "https://api.worldbank.org/v2/country/{}"
    "/indicator/SP.POP.TOTL?date={}&format=json"
)


def search(country: str, year: int) -> str:
    """Tra dân số một nước theo mã ISO3 và năm, từ World Bank."""
    with urllib.request.urlopen(WB.format(country, year), timeout=20) as resp:
        payload = json.load(resp)
    rows = payload[1] if len(payload) > 1 and payload[1] else []
    if not rows or rows[0]["value"] is None:
        return f"Không có số liệu cho {country} năm {year}."
    return f"{country} {year}: {rows[0]['value']} (nguồn: World Bank, SP.POP.TOTL)"


def calculator(expression: str) -> str:
    """Tính một biểu thức số học."""
    # Chỉ cho phép chữ số và dấu phép tính — không có chữ cái nào đi qua được
    # bộ lọc này, nên không thể gọi tới một tên hay một hàm nào khác.
    if not re.fullmatch(r"[\d\s+\-*/().]+", expression):
        return "Chỉ nhận biểu thức số học."
    return str(eval(expression))


# ── Phần hiển thị, cho dễ đọc trên terminal ─────────────────────────────────
# Mỗi pha của ReAct một màu, để người xem nhìn là phân biệt được ngay.
MAU = {
    "CÂU HỎI": "\033[1;35m",
    "THOUGHT": "\033[36m",
    "ACTION": "\033[33m",
    "OBS": "\033[32m",
    "TRẢ LỜI": "\033[1;37m",
}
RESET = "\033[0m"


EMOJI = re.compile("[\U0001F000-\U0001FAFF\u2600-\u27BF\u2190-\u21FF\uFE0F\u200D]+")


def thuan(text: str) -> str:
    """Bỏ ký hiệu markdown, vì terminal không hiểu — bảng thành từng dòng."""
    text = re.sub(r"\*\*|__|`|^#+ |^>\s?|^-{3,}$", "", text, flags=re.M)
    text = EMOJI.sub("", text)
    text = re.sub(r"  +", " ", text)  # chỗ trống emoji vừa để lại
    giu = []
    for d in text.split("\n"):
        if re.fullmatch(r"\s*\|[\s:|-]*\|\s*", d):  # dòng kẻ ngang của bảng
            continue
        if d.strip().startswith("|"):
            d = "  ".join(o.strip() for o in d.strip().strip("|").split("|"))
        giu.append(d)
    return "\n".join(giu)


def hien(nhan: str, noi_dung: str) -> None:
    """In một block ReAct: nhãn có màu, nội dung thụt vào, cách một dòng."""
    print(f"{MAU[nhan]}{nhan}{RESET}")
    for doan in thuan(noi_dung).strip().split("\n"):
        print(textwrap.fill(doan.strip(), 76, initial_indent="    ",
                            subsequent_indent="    ") if doan.strip() else "")
    print()


def vach(vong: int) -> None:
    """Vạch ngăn giữa hai vòng, để thấy rõ ranh giới của vòng lặp."""
    print(f"\033[1;34m{'━' * 22} VÒNG {vong} {'━' * 22}{RESET}\n")


TOOLS = [
    {
        "name": "search",
        "description": "Tra dân số một nước theo mã ISO3 (ví dụ IND, CHN) và năm.",
        "input_schema": {
            "type": "object",
            "properties": {
                "country": {"type": "string", "description": "Mã ISO3, ví dụ IND"},
                "year": {"type": "integer", "description": "Năm, ví dụ 2024"},
            },
            "required": ["country", "year"],
            "additionalProperties": False,
        },
        "strict": True,
    },
    {
        "name": "calculator",
        "description": "Tính một biểu thức số học, ví dụ 1450935791 - 1408975000.",
        "input_schema": {
            "type": "object",
            "properties": {
                "expression": {"type": "string", "description": "Biểu thức số học"},
            },
            "required": ["expression"],
            "additionalProperties": False,
        },
        "strict": True,
    },
]
HANDLERS = {"search": search, "calculator": calculator}

client = anthropic.Anthropic()
messages = [{"role": "user", "content": CAU_HOI}]
hien("CÂU HỎI", CAU_HOI)

for vong in range(1, 11):
    reply = client.beta.messages.create(
        model=MODEL,
        max_tokens=16000,
        # interleaved thinking: mô hình suy luận lại sau mỗi observation,
        # nên vòng nào cũng có thought — chứ không chỉ vòng đầu.
        betas=["interleaved-thinking-2025-05-14"],
        thinking={"type": "enabled", "budget_tokens": 4000},
        tools=TOOLS,
        messages=messages,
    )
    messages.append({"role": "assistant", "content": reply.content})
    vach(vong)

    for block in reply.content:
        if block.type == "thinking":
            hien("THOUGHT", block.thinking)
        elif block.type == "text":
            hien("TRẢ LỜI", block.text)

    if reply.stop_reason != "tool_use":
        break

    observations = []
    for block in reply.content:
        if block.type != "tool_use":
            continue
        args = json.dumps(block.input, ensure_ascii=False)
        hien("ACTION", f"{block.name}({args})")
        result = HANDLERS[block.name](**block.input)
        hien("OBS", result)
        observations.append(
            {"type": "tool_result", "tool_use_id": block.id, "content": result}
        )
    messages.append({"role": "user", "content": observations})
