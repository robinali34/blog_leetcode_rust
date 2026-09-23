#!/usr/bin/env python3
"""Convert C++ LeetCode snippets in markdown to real Ruby."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

CODE_BLOCK_RE = re.compile(
    r"(```)(cpp|c\+\+|C\+\+|rust|python)(\s*\n)(.*?)(```)",
    re.DOTALL,
)

TWO_SUM_RUBY = """# @param {Integer[]} nums
# @param {Integer} target
# @return {Integer[]}
def two_sum(nums, target)
  idx = {}
  nums.each_with_index do |x, j|
    i = idx[target - x]
    return [i, j] if i
    idx[x] = j
  end
end
"""

RUBY_KEYWORDS = {
    "BEGIN", "END", "alias", "and", "begin", "break", "case", "class",
    "def", "defined?", "do", "else", "elsif", "end", "ensure", "false",
    "for", "if", "in", "module", "next", "nil", "not", "or", "redo",
    "rescue", "retry", "return", "self", "super", "then", "true", "undef",
    "unless", "until", "when", "while", "yield",
}


def split_params(params: str) -> list[str]:
    parts: list[str] = []
    depth = 0
    cur: list[str] = []
    for ch in params:
        if ch in "<([":
            depth += 1
        elif ch in ">)]":
            depth = max(0, depth - 1)
        if ch == "," and depth == 0:
            p = "".join(cur).strip()
            if p:
                parts.append(p)
            cur = []
        else:
            cur.append(ch)
    p = "".join(cur).strip()
    if p:
        parts.append(p)
    return parts


def param_name(p: str) -> str:
    p = re.sub(r"\s*=\s*.+$", "", p.strip())
    p = p.replace("&", " ").replace("*", " ")
    p = re.sub(
        r"\b(const|auto|int|long|bool|char|double|float|string|void|unsigned)\b",
        "",
        p,
    )
    p = re.sub(r"vector\s*<[^>]+>", "", p)
    p = re.sub(r"\b\w+<[^>]+>", "", p)
    toks = p.split()
    return toks[-1] if toks else ""


def camel_to_snake(name: str) -> str:
    s1 = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s1).lower()


def skip_string(code: str, i: int) -> int:
    q = code[i]
    i += 1
    while i < len(code):
        if code[i] == "\\" and i + 1 < len(code):
            i += 2
            continue
        if code[i] == q:
            return i + 1
        i += 1
    return i


def extract_balanced(code: str, start: int, open_ch: str = "{", close_ch: str = "}") -> tuple[str, int]:
    assert code[start] == open_ch
    i = start + 1
    depth = 1
    inner: list[str] = []
    while i < len(code) and depth:
        ch = code[i]
        if ch in "'\"":
            j = skip_string(code, i)
            inner.append(code[i:j])
            i = j
            continue
        if ch == open_ch:
            depth += 1
            inner.append(ch)
            i += 1
            continue
        if ch == close_ch:
            depth -= 1
            if depth == 0:
                return "".join(inner), i + 1
            inner.append(ch)
            i += 1
            continue
        inner.append(ch)
        i += 1
    return "".join(inner), i


def split_commas(s: str) -> list[str]:
    parts: list[str] = []
    depth = 0
    cur: list[str] = []
    i = 0
    while i < len(s):
        ch = s[i]
        if ch in "'\"":
            j = skip_string(s, i)
            cur.append(s[i:j])
            i = j
            continue
        if ch in "{([":
            depth += 1
        elif ch in "})]":
            depth = max(0, depth - 1)
        if ch == "," and depth == 0:
            parts.append("".join(cur))
            cur = []
            i += 1
            continue
        cur.append(ch)
        i += 1
    if cur:
        parts.append("".join(cur))
    return parts


def convert_initializer_lists(code: str) -> str:
    """Turn C++ `{ {k, v}, ... }` and `{a, b, c}` inits into Ruby hashes/arrays."""
    out: list[str] = []
    i = 0
    n = len(code)
    while i < n:
        if code[i] in "'\"":
            j = skip_string(code, i)
            out.append(code[i:j])
            i = j
            continue
        if code[i] == "=" and (i == 0 or code[i - 1] not in "=!<>"):
            j = i + 1
            while j < n and code[j].isspace():
                j += 1
            if j < n and code[j] == "{":
                inner, end = extract_balanced(code, j)
                out.append("= ")
                out.append(ruby_from_init(inner))
                i = end
                continue
        out.append(code[i])
        i += 1
    return "".join(out)


def ruby_from_init(inner: str) -> str:
    s = inner.strip()
    if not s:
        return "{}"
    pairs = []
    i = 0
    while i < len(s):
        while i < len(s) and s[i] in " \t\n,":
            i += 1
        if i >= len(s):
            break
        if s[i] == "{":
            piece, nxt = extract_balanced(s, i)
            parts = split_commas(piece)
            if len(parts) == 2:
                pairs.append((parts[0].strip(), parts[1].strip()))
                i = nxt
                continue
        break
    if pairs and i >= len(s):
        return "{ " + ", ".join(f"{k} => {v}" for k, v in pairs) + " }"
    parts = [p.strip() for p in split_commas(s) if p.strip()]
    if parts and not any(";" in p for p in parts):
        return "[" + ", ".join(parts) + "]"
    return s


def prev_non_ws(code: str, i: int) -> str:
    j = i - 1
    while j >= 0 and code[j].isspace():
        j -= 1
    return code[j] if j >= 0 else ""


def skip_ws(code: str, i: int) -> int:
    while i < len(code) and code[i].isspace():
        i += 1
    return i


def read_stmt(code: str, i: int) -> tuple[str, int]:
    """Read one statement (or a nested block) starting at i."""
    i = skip_ws(code, i)
    if i >= len(code):
        return "", i
    if code.startswith(("if", "while", "for"), i) and (
        i + 2 >= len(code) or not (code[i + 2].isalnum() or code[i + 2] == "_")
        if code.startswith("if", i)
        else True
    ):
        # handled by rewrite from this position — fall through to generic
        pass
    if i < len(code) and code[i] == "{":
        inner, end = extract_balanced(code, i)
        return "{" + inner + "}", end
    start = i
    depth = 0
    while i < len(code):
        ch = code[i]
        if ch in "'\"":
            i = skip_string(code, i)
            continue
        if ch in "{([":
            depth += 1
        elif ch in "})]":
            if ch == "}" and depth == 0:
                break
            depth = max(0, depth - 1)
        if ch == ";" and depth == 0:
            return code[start : i + 1], i + 1
        if ch == "\n" and depth == 0:
            # statement without semicolon
            return code[start:i], i
        i += 1
    return code[start:i], i


def looks_ident_boundary(code: str, i: int, word: str) -> bool:
    if i > 0 and (code[i - 1].isalnum() or code[i - 1] == "_"):
        return False
    j = i + len(word)
    if j < len(code) and (code[j].isalnum() or code[j] == "_"):
        return False
    return True


def is_ruby_literal_brace(code: str, brace_at: int, inner: str) -> bool:
    prev = prev_non_ws(code, brace_at)
    stripped = inner.strip()
    if prev in "=,([":
        return True
    if "=>" in inner:
        return True
    if stripped == "":
        return prev in "=,"
    if prev == ")" and ";" not in inner and not re.search(
        r"\b(if|while|for|return|else)\b", inner
    ):
        return True
    return False


def rewrite_c_blocks(code: str) -> str:
    """Recursively turn C if/while/for/{ } into Ruby if/while/end."""
    out: list[str] = []
    i = 0
    n = len(code)
    while i < n:
        if code[i] in "'\"":
            j = skip_string(code, i)
            out.append(code[i:j])
            i = j
            continue

        if code[i] == "#":
            j = code.find("\n", i)
            if j < 0:
                out.append(code[i:])
                break
            out.append(code[i:j])
            i = j
            continue

        if looks_ident_boundary(code, i, "if") and code.startswith("if", i):
            j = skip_ws(code, i + 2)
            if j < n and code[j] == "(":
                chunk, i = convert_if_chain(code, i)
                out.append(chunk)
                continue

        if looks_ident_boundary(code, i, "while") and code.startswith("while", i):
            j = skip_ws(code, i + 5)
            if j < n and code[j] == "(":
                chunk, i = convert_while(code, i)
                out.append(chunk)
                continue

        if looks_ident_boundary(code, i, "for") and code.startswith("for", i):
            j = skip_ws(code, i + 3)
            if j < n and code[j] == "(":
                chunk, i = convert_for(code, i)
                out.append(chunk)
                continue

        if code[i] == "{":
            inner, nxt = extract_balanced(code, i)
            if is_ruby_literal_brace(code, i, inner):
                out.append("{" + inner + "}")
                i = nxt
                continue
            body = rewrite_c_blocks(inner).strip("\n")
            out.append("\n" + body + "\nend" if body else "\nend")
            i = nxt
            continue

        if code[i] == "}":
            out.append("\nend")
            i += 1
            continue

        out.append(code[i])
        i += 1
    return "".join(out)


def convert_for(code: str, i: int) -> tuple[str, int]:
    """Generic C for (init; cond; incr) → init; while cond; body; incr; end."""
    assert code.startswith("for", i)
    i += 3
    i = skip_ws(code, i)
    if i < len(code) and code[i] == "(":
        inner, i = extract_balanced(code, i, "(", ")")
        parts = [p.strip() for p in split_commas_semi(inner)]
        while len(parts) < 3:
            parts.append("")
        init, cond, incr = parts[0], parts[1] or "true", parts[2]
        body, i = convert_body(code, i)
        init_r = rewrite_c_blocks(strip_cpp_type_decl(init)).strip()
        incr_r = rewrite_c_blocks(incr).strip().rstrip(";")
        cond_r = tidy_cond(cond)
        extra = f"\n  {incr_r}" if incr_r else ""
        head = (init_r + "\n") if init_r else ""
        return f"{head}while {cond_r}\n{body}{extra}\nend\n", i
    return "for", i + 3


def split_commas_semi(s: str) -> list[str]:
    parts: list[str] = []
    depth = 0
    cur: list[str] = []
    i = 0
    while i < len(s):
        ch = s[i]
        if ch in "'\"":
            j = skip_string(s, i)
            cur.append(s[i:j])
            i = j
            continue
        if ch in "{([":
            depth += 1
        elif ch in "})]":
            depth = max(0, depth - 1)
        if ch == ";" and depth == 0:
            parts.append("".join(cur))
            cur = []
            i += 1
            continue
        cur.append(ch)
        i += 1
    if cur:
        parts.append("".join(cur))
    return parts


def strip_cpp_type_decl(stmt: str) -> str:
    stmt = stmt.strip().rstrip(";")
    stmt = re.sub(
        r"^(?:int|long long|long|bool|char|double|float|size_t|auto|unsigned)\s+",
        "",
        stmt,
    )
    # int l = 0, r = 0
    if "," in stmt and "=" in stmt:
        bits = []
        for part in split_commas(stmt):
            part = part.strip()
            part = re.sub(
                r"^(?:int|long long|long|bool|char|double|size_t|auto)\s+",
                "",
                part,
            )
            bits.append(part)
        return "\n".join(bits)
    return stmt


def parse_paren_cond(code: str, i: int) -> tuple[str, int]:
    i = skip_ws(code, i)
    if i < len(code) and code[i] == "(":
        inner, end = extract_balanced(code, i, "(", ")")
        return tidy_cond(inner), end
    # already paren-less
    start = i
    while i < len(code) and code[i] not in "{\n":
        i += 1
    return tidy_cond(code[start:i]), i


def tidy_cond(cond: str) -> str:
    cond = cond.strip()
    cond = re.sub(r"^\((.*)\)$", r"\1", cond)
    cond = re.sub(r"\btrue\b", "true", cond)
    cond = re.sub(r"\bfalse\b", "false", cond)
    # !ptr for typical node / collection names
    cond = re.sub(r"!(\w+)\.empty\?", r"\1.empty?", cond)  # already converted
    cond = re.sub(r"!(\w+)(?!\s*[\[(.\w])", r"\1.nil?", cond)
    cond = re.sub(r"(\w+)\s*==\s*nil", r"\1.nil?", cond)
    cond = re.sub(r"(\w+)\s*!=\s*nil", r"!\1.nil?", cond)
    cond = re.sub(r"(\w+)\s*==\s*nullptr", r"\1.nil?", cond)
    cond = re.sub(r"(\w+)\s*!=\s*nullptr", r"!\1.nil?", cond)
    return cond.strip()


def convert_body(code: str, i: int) -> tuple[str, int]:
    i = skip_ws(code, i)
    if i < len(code) and code[i] == "{":
        inner, end = extract_balanced(code, i)
        body = rewrite_c_blocks(inner)
        return indent_ruby(body), end
    stmt, end = read_stmt(code, i)
    body = rewrite_c_blocks(stmt)
    return indent_ruby(body), end


def indent_ruby(body: str) -> str:
    body = body.strip("\n")
    if not body.strip():
        return "  nil"
    lines = []
    for ln in body.split("\n"):
        if ln.strip() == "":
            lines.append("")
        else:
            lines.append("  " + ln.lstrip())
    return "\n".join(lines)


def convert_if_chain(code: str, i: int) -> tuple[str, int]:
    assert code.startswith("if", i)
    i += 2
    cond, i = parse_paren_cond(code, i)
    then_body, i = convert_body(code, i)
    parts = [f"if {cond}", then_body]
    while True:
        j = skip_ws(code, i)
        if code.startswith("else", j) and looks_ident_boundary(code, j, "else"):
            j += 4
            k = skip_ws(code, j)
            if code.startswith("if", k) and looks_ident_boundary(code, k, "if"):
                k += 2
                econd, k = parse_paren_cond(code, k)
                ebody, k = convert_body(code, k)
                parts.append(f"elsif {econd}")
                parts.append(ebody)
                i = k
                continue
            ebody, k = convert_body(code, j)
            parts.append("else")
            parts.append(ebody)
            i = k
            break
        break
    parts.append("end")
    return "\n".join(p for p in parts if p is not None) + "\n", i


def convert_while(code: str, i: int) -> tuple[str, int]:
    assert code.startswith("while", i)
    i += 5
    cond, i = parse_paren_cond(code, i)
    body, i = convert_body(code, i)
    return f"while {cond}\n{body}\nend\n", i


def add_braces_to_single_line_control(code: str) -> str:
    """Wrap brace-less if/while/else bodies using balanced parentheses."""
    out: list[str] = []
    i = 0
    n = len(code)
    while i < n:
        if code[i] in "'\"":
            j = skip_string(code, i)
            out.append(code[i:j])
            i = j
            continue
        wrapped = False
        for word in ("else if", "while", "if"):
            if code.startswith(word, i) and looks_ident_boundary(code, i, word):
                if word == "else if" and not looks_ident_boundary(code, i, "else"):
                    continue
                j = i + len(word)
                j = skip_ws(code, j)
                if j < n and code[j] == "(":
                    _cond, k = extract_balanced(code, j, "(", ")")
                    k = skip_ws(code, k)
                    if k < n and code[k] != "{" and not code.startswith("if", k):
                        stmt, end = read_to_semicolon(code, k)
                        out.append(code[i:j] + "(" + _cond + ") { " + stmt.strip() + " }")
                        i = end
                        wrapped = True
                        break
        if wrapped:
            continue
        if looks_ident_boundary(code, i, "else") and code.startswith("else", i):
            j = i + 4
            j = skip_ws(code, j)
            if j < n and not code.startswith("if", j) and code[j] != "{":
                stmt, end = read_to_semicolon(code, j)
                out.append("else { " + stmt.strip() + " }")
                i = end
                continue
        out.append(code[i])
        i += 1
    return "".join(out)


def read_to_semicolon(code: str, i: int) -> tuple[str, int]:
    start = i
    depth = 0
    while i < len(code):
        ch = code[i]
        if ch in "'\"":
            i = skip_string(code, i)
            continue
        if ch in "{([":
            depth += 1
        elif ch in "})]":
            if ch == "}" and depth == 0:
                return code[start:i], i
            depth = max(0, depth - 1)
        if ch == ";" and depth == 0:
            return code[start : i + 1], i + 1
        i += 1
    return code[start:i], i


def tidy_indent(code: str) -> str:
    lines = [ln.rstrip() for ln in code.split("\n")]
    # drop blank lines at end
    while lines and lines[-1] == "":
        lines.pop()
    # drop extra trailing ends from class Solution
    opens = 0
    ends = 0
    for ln in lines:
        s = ln.strip()
        if re.match(r"def |class |if |elsif |while |unless |case |begin ", s) and not s.startswith("#"):
            opens += 1
        if (re.search(r"\bdo\s*\|", s) or s.endswith(" do") or re.search(r"\.each do", s)
                or re.search(r"downto\(.*\) do", s) or re.search(r"\.times do", s)) and not s.startswith("#"):
            opens += 1
        if (s == "end" or s.startswith("end ") or s.startswith("end#")) and not s.startswith("#"):
            ends += 1
    extra = ends - opens
    while extra > 0 and lines and lines[-1].strip() == "end":
        lines.pop()
        extra -= 1
    # reindent
    indent = 0
    out: list[str] = []
    for ln in lines:
        s = ln.strip()
        if not s:
            out.append("")
            continue
        dedent = s == "end" or s.startswith("else") or s.startswith("elsif ")
        if dedent:
            indent = max(0, indent - 1)
        out.append(("  " * indent) + s)
        opens_block = (
            s.startswith("def ")
            or s.startswith("class ")
            or s.startswith("if ")
            or s.startswith("elsif ")
            or s.startswith("else")
            or s.startswith("while ")
            or s.startswith("unless ")
            or re.search(r"\bdo\s*\|", s)
            or s.endswith(" do")
        )
        postfix = bool(
            re.search(r"\s(?:if|unless)\s+\S+", s)
            and not s.startswith(("if ", "unless ", "elsif "))
        )
        if opens_block and not postfix and not s.endswith(" end"):
            indent += 1
    return "\n".join(out)


def convert_cpp_to_ruby(code: str) -> str:
    result = code.replace("\t", "    ")

    result = re.sub(r"^\s*#include[^\n]*\n", "", result, flags=re.M)
    result = re.sub(r"^\s*using\s+namespace\s+std\s*;\s*\n", "", result, flags=re.M)
    result = re.sub(r"^\s*using\s+std::\w+\s*;\s*\n", "", result, flags=re.M)
    result = re.sub(r"/\*.*?\*/", "", result, flags=re.S)
    result = re.sub(r"^\s*(public|private|protected)\s*:\s*\n", "", result, flags=re.M)

    if "struct ListNode" in result or "ListNode*" in result:
        result = (
            "# Definition for singly-linked list.\n"
            "# class ListNode\n"
            "#   attr_accessor :val, :next\n"
            "#   def initialize(val = 0, _next = nil)\n"
            "#     @val = val\n"
            "#     @next = _next\n"
            "#   end\n"
            "# end\n\n"
        ) + re.sub(r"struct\s+ListNode\s*\{[^}]*\}", "", result)

    if "struct TreeNode" in result or "TreeNode*" in result:
        result = (
            "# Definition for a binary tree node.\n"
            "# class TreeNode\n"
            "#   attr_accessor :val, :left, :right\n"
            "#   def initialize(val = 0, left = nil, right = nil)\n"
            "#     @val = val\n"
            "#     @left = left\n"
            "#     @right = right\n"
            "#   end\n"
            "# end\n\n"
        ) + re.sub(r"struct\s+TreeNode\s*\{[^}]*\}", "", result)

    result = re.sub(r"\bclass\s+Solution\s*\{", "", result)
    result = re.sub(r"\bstd::", "", result)

    result = convert_initializer_lists(result)
    result = add_braces_to_single_line_control(result)

    # for-loops before other work (they contain semicolons)
    result = re.sub(
        r"for\s*\(\s*(?:int|long|size_t|auto)\s+(\w+)\s*=\s*([^;]+);\s*\1\s*<\s*([^;]+);\s*(?:\+\+\1|\1\+\+)\s*\)",
        r"(\2...\3).each do |\1|",
        result,
    )
    result = re.sub(
        r"for\s*\(\s*(?:int|long)\s+(\w+)\s*=\s*([^;]+);\s*\1\s*<=\s*([^;]+);\s*(?:\+\+\1|\1\+\+)\s*\)",
        r"(\2..\3).each do |\1|",
        result,
    )
    result = re.sub(
        r"for\s*\(\s*(?:int|long)\s+(\w+)\s*=\s*([^;]+)\s*-\s*1;\s*\1\s*>=\s*0;\s*(?:--\1|\1--)\s*\)",
        r"(\2 - 1).downto(0) do |\1|",
        result,
    )
    result = re.sub(
        r"for\s*\(\s*(?:int|long)\s+(\w+)\s*=\s*([^;]+);\s*\1\s*>=\s*0;\s*(?:--\1|\1--)\s*\)",
        r"\2.downto(0) do |\1|",
        result,
    )
    result = re.sub(
        r"for\s*\(\s*(?:int|long|char|auto|bool)\s*&?\s+(\w+)\s*:\s*(\w+)\s*\)",
        r"\2.each do |\1|",
        result,
    )
    result = re.sub(
        r"for\s*\(\s*auto\s*&?\s*\[(\w+)\s*,\s*(\w+)\]\s*:\s*(\w+)\s*\)",
        r"\3.each do |\1, \2|",
        result,
    )
    # brace-less for-each body needs an end
    result = re.sub(
        r"(\.each do \|[^|]+\|\s*)(?![\s\n]*\{)([^;\n{]+;)",
        r"\1\n\2\nend\n",
        result,
    )

    result = re.sub(r"\bclass\s+(\w+)\s*\{", r"class \1\n", result)

    def repl_fn(m: re.Match) -> str:
        name = camel_to_snake(m.group(2))
        names = [param_name(p) for p in split_params(m.group(3))]
        names = [rename_ident(n) for n in names if n and n not in {"void"}]
        return f"def {name}({', '.join(names)})"

    result = re.sub(
        r"(?:^|\n)[ \t]*(?:static\s+)?(void|bool|int|long|double|float|char|string|vector\s*<[^>]+>|ListNode\s*\*|TreeNode\s*\*|unordered_map\s*<[^>]+>)\s+(\w+)\s*\(([^)]*)\)\s*\{",
        lambda m: "\n" + repl_fn(m),
        result,
    )
    result = re.sub(
        r"^(\s*)(\w+)\s*\(([^)]*)\)\s*\{",
        lambda m: (
            m.group(1)
            + "def initialize("
            + ", ".join(
                rename_ident(n)
                for n in (param_name(p) for p in split_params(m.group(3)))
                if n
            )
            + ")"
            if m.group(2)[:1].isupper()
            else m.group(0)
        ),
        result,
        flags=re.M,
    )

    result = re.sub(r"\bunordered_map\s*<[^>]+>\s+(\w+)\s*=\s*", r"\1 = ", result)
    result = re.sub(r"\bunordered_map\s*<[^>]+>\s+(\w+)\s*;", r"\1 = {}", result)
    result = re.sub(r"\bunordered_set\s*<[^>]+>\s+(\w+)\s*;", r"\1 = Set.new", result)
    result = re.sub(r"\bmap\s*<[^>]+>\s+(\w+)\s*;", r"\1 = {}", result)
    result = re.sub(r"\bset\s*<[^>]+>\s+(\w+)\s*;", r"\1 = Set.new", result)
    result = re.sub(
        r"\bvector\s*<\s*vector\s*<\s*int\s*>\s*>\s+(\w+)\s*\(\s*([^,]+)\s*,\s*vector\s*<\s*int\s*>\s*\(\s*([^,]+)\s*,\s*([^)]+)\)\s*\)\s*;",
        r"\1 = Array.new(\2) { Array.new(\3, \4) }",
        result,
    )
    result = re.sub(
        r"\bvector\s*<\s*vector\s*<[^>]+>\s*>\s+(\w+)\s*\(\s*([^)]+)\s*\)\s*;",
        r"\1 = Array.new(\2) { [] }",
        result,
    )
    result = re.sub(
        r"\bvector\s*<\s*int\s*>\s+(\w+)\s*\(\s*([^,]+)\s*,\s*([^)]+)\)\s*;",
        r"\1 = Array.new(\2, \3)",
        result,
    )
    result = re.sub(
        r"\bvector\s*<\s*bool\s*>\s+(\w+)\s*\(\s*([^)]+)\s*\)\s*;",
        r"\1 = Array.new(\2, false)",
        result,
    )
    result = re.sub(
        r"\bvector\s*<[^>]+>\s+(\w+)\s*\(\s*([^)]+)\s*\)\s*;",
        r"\1 = Array.new(\2)",
        result,
    )
    result = re.sub(r"\bvector\s*<[^>]+>\s+(\w+)\s*;", r"\1 = []", result)
    result = re.sub(r"\bstack\s*<[^>]+>\s+(\w+)\s*;", r"\1 = []", result)
    result = re.sub(r"\bqueue\s*<[^>]+>\s+(\w+)\s*;", r"\1 = []", result)
    result = re.sub(r"\bdeque\s*<[^>]+>\s+(\w+)\s*;", r"\1 = []", result)
    result = re.sub(r"\bpriority_queue\s*<[^>]+>\s+(\w+)\s*;", r"\1 = []", result)
    result = re.sub(r"\bstring\s+(\w+)\s*;", r'\1 = ""', result)
    result = re.sub(r"\bstring\s+(\w+)\s*=\s*", r"\1 = ", result)

    result = re.sub(r"\bListNode\s*\*\s*(\w+)\s*=\s*", r"\1 = ", result)
    result = re.sub(r"\bTreeNode\s*\*\s*(\w+)\s*=\s*", r"\1 = ", result)
    result = re.sub(r"\bListNode\s*\*\s*(\w+)\s*;", r"\1 = nil", result)
    result = re.sub(r"\bTreeNode\s*\*\s*(\w+)\s*;", r"\1 = nil", result)

    def split_prim(m: re.Match) -> str:
        indent, decls = m.group(1), m.group(3)
        bits = []
        for part in decls.split(","):
            part = part.strip()
            if not part:
                continue
            if "=" in part:
                name, val = part.split("=", 1)
                bits.append(f"{indent}{rename_ident(name.strip())} = {val.strip()}")
            else:
                bits.append(f"{indent}{rename_ident(part)} = 0")
        return "\n".join(bits)

    result = re.sub(
        r"^(\s*)(int|long|long long|bool|char|double|size_t)\s+([^;]+);",
        split_prim,
        result,
        flags=re.M,
    )

    result = re.sub(r"\.push_back\s*\(", ".push(", result)
    result = re.sub(r"\.emplace_back\s*\(", ".push(", result)
    result = re.sub(r"\.pop_back\s*\(\s*\)", ".pop", result)
    result = re.sub(r"\.size\s*\(\s*\)", ".length", result)
    result = re.sub(r"\.length\s*\(\s*\)", ".length", result)
    result = re.sub(r"\.empty\s*\(\s*\)", ".empty?", result)
    result = re.sub(r"\.top\s*\(\s*\)", ".last", result)
    result = re.sub(r"\.front\s*\(\s*\)", ".first", result)
    result = re.sub(r"\.back\s*\(\s*\)", ".last", result)
    result = re.sub(r"\.pop_front\s*\(\s*\)", ".shift", result)
    result = re.sub(r"\.contains\s*\(([^)]+)\)", r".include?(\1)", result)
    result = re.sub(r"\.count\s*\(([^)]+)\)", r".include?(\1)", result)
    result = re.sub(r"\.find\s*\(([^)]+)\)", r"[\1]", result)
    result = re.sub(r"\.insert\s*\(([^)]+)\)", r".add(\1)", result)
    result = re.sub(r"\.erase\s*\(([^)]+)\)", r".delete(\1)", result)
    result = re.sub(r"\.clear\s*\(\s*\)", ".clear", result)
    result = re.sub(r"\.pop\s*\(\s*\)", ".pop", result)
    result = re.sub(r"(\w+)\[(\w+)\]\+\+", r"\1[\2] = (\1[\2] || 0) + 1", result)
    result = re.sub(r"\+\+(\w+)\[(\w+)\]", r"\1[\2] = (\1[\2] || 0) + 1", result)

    result = re.sub(r"sort\s*\(\s*(\w+)\.begin\(\)\s*,\s*\1\.end\(\)\s*\)", r"\1.sort!", result)
    result = re.sub(r"reverse\s*\(\s*(\w+)\.begin\(\)\s*,\s*\1\.end\(\)\s*\)", r"\1.reverse!", result)
    result = re.sub(r"\bto_string\s*\(([^)]+)\)", r"\1.to_s", result)
    result = re.sub(r"\bstoi\s*\(([^)]+)\)", r"\1.to_i", result)
    result = re.sub(r"(?<![\w.])max\s*\(([^,]+),\s*([^)]+)\)", r"[\1, \2].max", result)
    result = re.sub(r"(?<![\w.])min\s*\(([^,]+),\s*([^)]+)\)", r"[\1, \2].min", result)
    result = re.sub(r"\babs\s*\(([^)]+)\)", r"(\1).abs", result)
    result = re.sub(r"\bswap\s*\(([^,]+),\s*([^)]+)\)", r"\1, \2 = \2, \1", result)

    result = re.sub(r"\bnullptr\b", "nil", result)
    result = re.sub(r"\bNULL\b", "nil", result)
    result = re.sub(r"\bINT_MAX\b", "(2**31 - 1)", result)
    result = re.sub(r"\bINT_MIN\b", "(-(2**31))", result)
    result = re.sub(r"\(long long\)", "", result)
    result = re.sub(r"\(unsigned char\)", "", result)
    result = re.sub(r"\(unsigned\)", "", result)
    result = re.sub(r"\(int\)", "", result)
    result = re.sub(r"\(long\)", "", result)
    result = re.sub(r"\bconst\s+", "", result)

    result = re.sub(r"->", ".", result)
    result = re.sub(r"\bthis\s*\.", "@", result)
    result = re.sub(r"\bthis\.", "@", result)
    result = re.sub(r"\blong long\b", "", result)
    result = re.sub(r"\bunsigned\b", "", result)
    result = re.sub(r"^(\s*)(?:long|int|bool|char|double|float|size_t|auto)\s+", r"\1", result, flags=re.M)

    result = re.sub(
        r"\b([a-z]+[A-Z]\w*)\s*\(",
        lambda m: camel_to_snake(m.group(1)) + "(",
        result,
    )
    result = re.sub(
        r"\b([a-z]+[A-Z]\w*)\b",
        lambda m: camel_to_snake(m.group(1)),
        result,
    )

    result = re.sub(
        r"\+\+(\w+\[(?:[^\[\]]|\[[^\[\]]*\])*\])",
        r"(\1 += 1)",
        result,
    )
    result = re.sub(
        r"(\w+\[(?:[^\[\]]|\[[^\[\]]*\])*\])\+\+",
        r"(\1 += 1)",
        result,
    )
    result = re.sub(
        r"--(\w+\[(?:[^\[\]]|\[[^\[\]]*\])*\])",
        r"(\1 -= 1)",
        result,
    )
    result = re.sub(
        r"(\w+\[(?:[^\[\]]|\[[^\[\]]*\])*\])--",
        r"(\1 -= 1)",
        result,
    )
    result = re.sub(r"^\s*\+\+(\w+)\s*;", lambda m: f"{rename_ident(m.group(1))} += 1", result, flags=re.M)
    result = re.sub(r"^\s*(\w+)\+\+\s*;", lambda m: f"{rename_ident(m.group(1))} += 1", result, flags=re.M)
    result = re.sub(r"^\s*--(\w+)\s*;", lambda m: f"{rename_ident(m.group(1))} -= 1", result, flags=re.M)
    result = re.sub(r"^\s*(\w+)--\s*;", lambda m: f"{rename_ident(m.group(1))} -= 1", result, flags=re.M)
    result = re.sub(r"\+\+(\w+)", lambda m: f"{rename_ident(m.group(1))} += 1", result)
    result = re.sub(r"(\w+)\+\+", lambda m: f"{rename_ident(m.group(1))} += 1", result)
    result = re.sub(r"--(\w+)", lambda m: f"{rename_ident(m.group(1))} -= 1", result)
    result = re.sub(r"(\w+)--", lambda m: f"{rename_ident(m.group(1))} -= 1", result)

    result = re.sub(r"cout\s*<<\s*endl", "puts", result)
    result = re.sub(r"cout\s*<<\s*", "puts ", result)
    result = re.sub(r"\s*<<\s*endl", "", result)
    result = re.sub(r"cin\s*>>\s*(\w+)", r"\1 = gets.to_i", result)
    result = re.sub(r"\bnew\s+ListNode\s*\(([^)]*)\)", r"ListNode.new(\1)", result)
    result = re.sub(r"\bnew\s+TreeNode\s*\(([^)]*)\)", r"TreeNode.new(\1)", result)

    result = re.sub(r"return\s+\{\}\s*;", "return []", result)
    result = re.sub(r"return\s+\{([^}]+)\}\s*;", r"return [\1]", result)

    result = re.sub(r"//", "#", result)

    # `next` is a Ruby keyword as a local variable, but ListNode#next is fine
    result = re.sub(r"(?<![.:@])\bnext\b", "nxt", result)

    result = rewrite_c_blocks(result)

    result = re.sub(r";\s*(#.*)$", r"  \1", result, flags=re.M)
    result = re.sub(r";\s*$", "", result, flags=re.M)
    result = re.sub(r"\}\s*;\s*$", "end", result, flags=re.M)
    result = re.sub(r"\n{3,}", "\n\n", result)

    if re.search(r"\bSet\.new\b", result) and "require 'set'" not in result:
        result = "require 'set'\n\n" + result.lstrip("\n")

    result = tidy_indent(result)
    return result.strip() + "\n"


def rename_ident(name: str) -> str:
    if name == "next":
        return "nxt"
    if name == "end":
        return "ending"
    if name == "class":
        return "klass"
    return name


def looks_like_lc1_two_sum(code: str) -> bool:
    return bool(
        re.search(r"\btwoSum\b|\btwo_sum\b", code)
        and re.search(r"unordered_map|HashMap|idx", code)
        and "two_sum_sorted" not in code
        and "twoSumSorted" not in code
    )


def process_file(path: Path) -> bool:
    original = path.read_text(encoding="utf-8")
    content = original

    def repl(m: re.Match) -> str:
        src = m.group(4)
        if looks_like_lc1_two_sum(src):
            return "```ruby\n" + TWO_SUM_RUBY + "```"
        ruby = convert_cpp_to_ruby(src)
        return f"```ruby\n{ruby}```"

    content = CODE_BLOCK_RE.sub(repl, content)
    content = content.replace("/blog_leetcode/", "/blog_leetcode_rust/")
    content = content.replace(
        "https://robinali34.github.io/blog_leetcode/",
        "https://robinali34.github.io/blog_leetcode_rust/",
    )
    content = re.sub(r"(categories:[^\n]*\s)cpp(\s)", r"\1ruby\2", content)
    content = re.sub(r"(categories:\s*\[[^\]]*?\b)cpp(\b)", r"\1ruby\2", content)
    content = re.sub(r"(tags:\s*\[[^\]]*?\b)cpp(\b)", r"\1ruby\2", content)

    if content != original:
        path.write_text(content, encoding="utf-8")
        return True
    return False


def main() -> int:
    targets = [Path(p) for p in sys.argv[1:]] if len(sys.argv) > 1 else []
    if not targets:
        targets.extend(ROOT.glob("_posts/*.md"))
        targets.extend(ROOT.glob("_templates/*.md"))
        for name in ("rust-guide.md", "cpp-guide.md"):
            p = ROOT / name
            if p.exists():
                targets.append(p)

    n = 0
    for path in targets:
        if path.exists() and process_file(path):
            n += 1
            print(f"converted: {path.name}")
    leftover = 0
    for p in list(ROOT.glob("_posts/*.md")):
        t = p.read_text(encoding="utf-8")
        if "```cpp" in t or "```rust" in t:
            leftover += 1
            print("leftover fence:", p.name)
    print(f"\nUpdated {n} files; leftover cpp/rust fences: {leftover}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
