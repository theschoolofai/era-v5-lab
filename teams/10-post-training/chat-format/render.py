"""Render and parse ChatML-style chat format v0.

Rule (instructor, 27 Oct): special tokens only for structure the model must never confuse
with normal text: role-turn start/end, tool-call start/end, tool-result start/end, thinking
start/end. Values inside that structure (tool names, arguments, effort level, options) are plain
text. Effort is a plain-text line at the top of the first system turn.
The 9 assigned markers and 247 reserved slots (256 total) are sent to
Team 3 (G3 Tokenizer) by Sat 31 Oct so G3 reserves the token IDs.
"""

from __future__ import annotations

import json

COUNT = 256

EFFORT_BUDGETS = {
    "1k": 1024,
    "4k": 4096,
    "16k": 16384,
    "64k": 65536,
}

# Fixed token ID -> (name, atomic special-token surface).
# Every chat marker in ChatML v0 is a single special token in the tokenizer.
ASSIGNED_SURFACES: dict[int, tuple[str, str]] = {
    0: ("endoftext", "<|endoftext|>"),
    1: ("im_start", "<|im_start|>"),
    2: ("im_end", "<|im_end|>"),
    24: ("think", "<|think|>"),
    25: ("think_end", "<|/think|>"),
    26: ("tool_call", "<|tool_call|>"),
    27: ("tool_call_end", "<|/tool_call|>"),
    28: ("tool_result", "<|tool_result|>"),
    29: ("tool_result_end", "<|/tool_result|>"),
}

ASSIGNED: dict[int, str] = {idx: name for idx, (name, _) in ASSIGNED_SURFACES.items()}
ROLES = ("system", "user", "assistant", "tool")
EFFORT_PREFIX = "Reasoning effort: "

# Plain-text XML tags and Unicode look-alikes that must NEVER be used in place of atomic special tokens.
_PLAIN_TEXT_LOOKALIKES = (
    "<think>",
    "</think>",
    "<tool_call>",
    "</tool_call>",
    "<tool_result>",
    "</tool_result>",
    "<｜think｜>",
    "<｜/think｜>",
    "<｜tool_call｜>",
    "<｜/tool_call｜>",
    "<｜tool_result｜>",
    "<｜/tool_result｜>",
    "＜think＞",
    "＜/think＞",
    "＜tool_call＞",
    "＜/tool_call＞",
    "＜tool_result＞",
    "＜/tool_result＞",
)


def surface(name: str) -> str:
    for _, (n, surf) in ASSIGNED_SURFACES.items():
        if n == name:
            return surf
    return f"<|{name}|>"


def reserved_name(index: int) -> str:
    return f"reserved_{index:03d}"


def all_tokens() -> list[tuple[int, str, str, str]]:
    """Return (index, name, surface, status) for all 256 reserved token IDs (0..255)."""
    rows: list[tuple[int, str, str, str]] = []
    for index in range(COUNT):
        if index in ASSIGNED_SURFACES:
            name, surf = ASSIGNED_SURFACES[index]
            rows.append((index, name, surf, "assigned"))
        else:
            name = reserved_name(index)
            rows.append((index, name, f"<|{name}|>", "reserved"))
    return rows


def by_name() -> dict[str, str]:
    return {name: token for _, name, token, _ in all_tokens()}


def id_by_surface() -> dict[str, int]:
    return {token: index for index, _, token, _ in all_tokens()}


T = by_name()
_ID_BY_SURFACE = id_by_surface()
_SURFACES = sorted(T.values(), key=len, reverse=True)


class RenderError(ValueError):
    """The transcript is not valid chat-format v0."""


def effort_limit(effort: str) -> int:
    try:
        return EFFORT_BUDGETS[effort]
    except KeyError as exc:
        raise RenderError(
            f"effort must be one of {', '.join(EFFORT_BUDGETS)}"
        ) from exc


def _reject_specials(text: str, where: str) -> None:
    for token in _SURFACES:
        if token in text:
            raise RenderError(f"{where} contains special token {token}")
    for tag in _PLAIN_TEXT_LOOKALIKES:
        if tag in text:
            raise RenderError(
                f"{where} contains plain-text marker {tag}; every chat marker must be one special token"
            )


def _call_json(call: object) -> str:
    if not isinstance(call, dict):
        raise RenderError("tool call must be an object")
    if "function" in call and isinstance(call["function"], dict):
        fn = call["function"]
        name = fn.get("name")
        arguments = fn.get("arguments", {})
        if isinstance(arguments, str):
            try:
                arguments = json.loads(arguments)
            except json.JSONDecodeError as exc:
                raise RenderError("tool call arguments must be valid JSON") from exc
    else:
        name = call.get("name")
        arguments = call.get("arguments", {})
    if not isinstance(name, str) or name == "":
        raise RenderError("tool call name must be a non-empty string")
    if not isinstance(arguments, dict):
        raise RenderError("tool call arguments must be an object")
    call_dict = {"arguments": arguments, "name": name}
    if "id" in call and isinstance(call["id"], str):
        call_dict["id"] = call["id"]
    try:
        payload = json.dumps(
            call_dict,
            sort_keys=True,
            ensure_ascii=False,
            separators=(",", ":"),
        )
    except TypeError as exc:
        raise RenderError("tool call arguments must be JSON values") from exc
    _reject_specials(payload, "tool call")
    return payload


def _turn(role: str, body: str) -> str:
    return f"{T['im_start']}{role}\n{body}{T['im_end']}\n"


def render(messages: list[dict], effort: str = "4k") -> str:
    """Render a transcript in ChatML v0 where every chat marker is one special token."""
    effort_limit(effort)
    if not isinstance(messages, list) or not messages:
        raise RenderError("messages must be a non-empty list")

    parts: list[str] = []
    first = messages[0]
    if not (isinstance(first, dict) and first.get("role") == "system"):
        parts.append(_turn("system", f"{EFFORT_PREFIX}{effort}"))
    for index, message in enumerate(messages):
        if not isinstance(message, dict):
            raise RenderError(f"message {index} must be an object")
        role = message.get("role")
        if role not in ROLES:
            raise RenderError(f"message {index} has role {role!r}")
        content = message.get("content", "")
        if content is None:
            content = ""
        if not isinstance(content, str):
            raise RenderError(f"message {index} content must be a string")
        _reject_specials(content, f"message {index} content")

        if role == "assistant":
            body: list[str] = []
            think = message.get("think") or ""
            if think:
                if not isinstance(think, str):
                    raise RenderError(f"message {index} think must be a string")
                _reject_specials(think, f"message {index} think")
                body.append(f"{T['think']}\n{think}\n{T['think_end']}\n")
            for call in message.get("tool_calls") or []:
                body.append(f"{T['tool_call']}\n{_call_json(call)}\n{T['tool_call_end']}\n")
            if content:
                body.append(content)
            parts.append(_turn("assistant", "".join(body)))
        elif role == "tool":
            if content == "":
                raise RenderError(f"message {index} tool content is empty")
            parts.append(
                _turn("tool", f"{T['tool_result']}\n{content}\n{T['tool_result_end']}")
            )
        elif role == "system" and index == 0:
            if content.startswith(EFFORT_PREFIX):
                raise RenderError(f"system content must not start with {EFFORT_PREFIX!r}")
            line = f"{EFFORT_PREFIX}{effort}"
            parts.append(_turn("system", f"{line}\n\n{content}" if content else line))
        else:
            parts.append(_turn(role, content))
    parts.append(T["endoftext"])
    return "".join(parts)


def tokenize_markers(text: str) -> list[tuple[str, int | str]]:
    """Split rendered text into ('special', token_id) and ('text', str) items.

    Proves for Team 3 (G3) that every chat marker is tokenized as a single
    special token ID in 0..255 and never left in a plain-text span.
    """
    items: list[tuple[str, int | str]] = []
    pos = 0
    buf_start = 0
    n = len(text)
    while pos < n:
        matched = None
        for surf in _SURFACES:
            if text.startswith(surf, pos):
                matched = surf
                break
        if matched is not None:
            if pos > buf_start:
                items.append(("text", text[buf_start:pos]))
            items.append(("special", _ID_BY_SURFACE[matched]))
            pos += len(matched)
            buf_start = pos
        else:
            pos += 1
    if n > buf_start:
        items.append(("text", text[buf_start:n]))
    return items


def _parse_system_effort(body: str) -> tuple[str, str]:
    """Split the first system turn into (effort level, remaining system content)."""
    if not body.startswith(EFFORT_PREFIX):
        raise RenderError(f"first system turn must start with {EFFORT_PREFIX!r}")
    rest = body[len(EFFORT_PREFIX) :]
    level, sep, content = rest.partition("\n\n")
    if level not in EFFORT_BUDGETS:
        raise RenderError(f"effort must be one of {', '.join(EFFORT_BUDGETS)}")
    return level, content


def _parse_assistant(body: str) -> dict:
    message: dict = {"role": "assistant"}
    think_open = f"{T['think']}\n"
    think_close = f"\n{T['think_end']}\n"
    call_open = f"{T['tool_call']}\n"
    call_close = f"\n{T['tool_call_end']}\n"

    while True:
        if body.startswith(think_open):
            end = body.find(think_close)
            if end < 0:
                raise RenderError(f"missing {T['think_end']}")
            think = body[len(think_open) : end]
            _reject_specials(think, "parsed think")
            message["think"] = think
            body = body[end + len(think_close) :]
            continue
        if body.startswith(call_open):
            end = body.find(call_close)
            if end < 0:
                raise RenderError(f"missing {T['tool_call_end']}")
            payload = body[len(call_open) : end]
            _reject_specials(payload, "parsed tool call")
            try:
                call = json.loads(payload)
            except json.JSONDecodeError as exc:
                raise RenderError("tool call is not JSON") from exc
            message.setdefault("tool_calls", []).append(call)
            body = body[end + len(call_close) :]
            continue
        break

    if body:
        _reject_specials(body, "parsed text")
        message["content"] = body
    return message


def parse(text: str) -> dict:
    """Inverse of `render` for transcripts this module produced."""
    if not isinstance(text, str) or not text.endswith(T["endoftext"]):
        raise RenderError("transcript must end with <|endoftext|>")
    pos = 0
    end = len(text) - len(T["endoftext"])
    messages: list[dict] = []
    effort: str | None = None

    while pos < end:
        if not text.startswith(T["im_start"], pos):
            raise RenderError(f"expected <|im_start|> at offset {pos}")
        pos += len(T["im_start"])
        newline = text.find("\n", pos)
        if newline < 0 or newline > end:
            raise RenderError("turn is missing a role")
        role = text[pos:newline]
        if role not in ROLES:
            raise RenderError(f"unknown role {role!r}")
        pos = newline + 1
        close = text.find(T["im_end"], pos)
        if close < 0 or close > end:
            raise RenderError("missing <|im_end|>")
        body = text[pos:close]
        pos = close + len(T["im_end"])
        if text.startswith("\n", pos):
            pos += 1

        if not messages and effort is None:
            if role != "system":
                raise RenderError("first turn must be the system turn with the effort line")
            effort, body = _parse_system_effort(body)
            _reject_specials(body, "parsed text")
            if body:
                messages.append({"role": "system", "content": body})
            continue
        if role == "assistant":
            messages.append(_parse_assistant(body))
        elif role == "tool":
            open_tag = f"{T['tool_result']}\n"
            close_tag = f"\n{T['tool_result_end']}"
            if not body.startswith(open_tag) or not body.endswith(close_tag):
                raise RenderError("tool turn must wrap output in <|tool_result|>...<|/tool_result|>")
            content = body[len(open_tag) : len(body) - len(close_tag)]
            if content == "":
                raise RenderError("tool content is empty")
            _reject_specials(content, "parsed text")
            messages.append({"role": "tool", "content": content})
        else:
            _reject_specials(body, "parsed text")
            messages.append({"role": role, "content": body})

    if pos != end:
        raise RenderError("trailing bytes before endoftext")
    return {"effort": effort, "messages": messages}
