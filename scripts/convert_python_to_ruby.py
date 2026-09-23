#!/usr/bin/env python3
"""Convert Python LeetCode snippets in markdown to idiomatic Ruby."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

CODE_BLOCK_RE = re.compile(
    r"(```)(python|py|cpp|c\+\+|C\+\+|rust|ruby)(\s*\n)(.*?)(```)",
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

LISTNODE_COMMENT = """# Definition for singly-linked list.
# class ListNode
#   attr_accessor :val, :next
#   def initialize(val = 0, _next = nil)
#     @val = val
#     @next = _next
#   end
# end
"""

TREENODE_COMMENT = """# Definition for a binary tree node.
# class TreeNode
#   attr_accessor :val, :left, :right
#   def initialize(val = 0, left = nil, right = nil)
#     @val = val
#     @left = left
#     @right = right
#   end
# end
"""

COLLECTIONS = {
    "st", "stack", "q", "queue", "seen", "visited", "res", "ans", "arr",
    "nums", "heap", "pq", "path", "tmp", "s", "cnt", "freq", "hm", "mp",
    "map", "idx", "keys", "vals", "bucket", "adj", "g", "graph", "dq",
    "strs", "words", "edges", "points", "intervals", "tickets",
}

NODE_NAMES = {
    "head", "curr", "cur", "node", "root", "prev", "nxt", "p", "tail",
    "dummy", "left", "right", "parent", "child", "fast", "slow",
}


def camel_to_snake(name: str) -> str:
    if name == "__init__":
        return "initialize"
    s1 = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s1).lower()


def strip_type(hint: str) -> str:
    hint = hint.strip()
    hint = re.sub(r":\s*[^=]+", "", hint)
    return hint.strip()


def convert_params(params: str) -> str:
    if not params.strip():
        return ""
    parts: list[str] = []
    depth = 0
    cur: list[str] = []
    for ch in params:
        if ch in "[(":
            depth += 1
        elif ch in "])":
            depth = max(0, depth - 1)
        if ch == "," and depth == 0:
            parts.append("".join(cur).strip())
            cur = []
        else:
            cur.append(ch)
    if cur:
        parts.append("".join(cur).strip())
    names = []
    for p in parts:
        p = p.strip()
        if not p or p == "self" or p.startswith("*"):
            continue
        if "=" in p:
            name, default = p.split("=", 1)
            name = strip_type(name)
            default = default.strip()
            default = convert_expr(default)
            names.append(f"{name} = {default}")
        else:
            names.append(strip_type(p))
    return ", ".join(n for n in names if n)


def convert_range_loop(var: str, args: str) -> str:
    args = args.strip()
    parts = split_args(args)
    if len(parts) == 1:
        n = convert_expr(parts[0])
        return f"(0...{n}).each do |{var}|"
    if len(parts) == 2:
        a, b = convert_expr(parts[0]), convert_expr(parts[1])
        return f"({a}...{b}).each do |{var}|"
    a, b, step = (convert_expr(p) for p in parts[:3])
    if parts[2].strip() in {"-1", "(-1)"}:
        # range(start, stop, -1) stop exclusive → downto(stop+1)
        stop = parts[1].strip()
        if stop == "-1":
            return f"({a}).downto(0) do |{var}|"
        return f"({a}).downto(({b}) + 1) do |{var}|"
    return f"({a}...{b}).step({step}) do |{var}|"


def split_args(args: str) -> list[str]:
    parts: list[str] = []
    depth = 0
    cur: list[str] = []
    for ch in args:
        if ch in "([{":
            depth += 1
        elif ch in ")]}":
            depth = max(0, depth - 1)
        if ch == "," and depth == 0:
            parts.append("".join(cur).strip())
            cur = []
        else:
            cur.append(ch)
    if cur:
        parts.append("".join(cur).strip())
    return [p for p in parts if p != ""]


def convert_for(line: str) -> str | None:
    line = line.strip()
    if line.endswith(":"):
        line = line[:-1].rstrip()
    m = re.match(r"for\s+(\w+)\s*,\s*(\w+)\s+in\s+enumerate\((.+)\)$", line)
    if m:
        xs = convert_expr(m.group(3).strip())
        idx, val = m.group(1), m.group(2)
        if xs in {"s", "word", "t", "pattern"} or val in {"c", "ch", "char"}:
            return f"{xs}.each_char.with_index do |{val}, {idx}|"
        return f"{xs}.each_with_index do |{val}, {idx}|"
    m = re.match(r"for\s+(\w+)\s+in\s+range\((.*)\)$", line)
    if m:
        return convert_range_loop(m.group(1), m.group(2))
    m = re.match(r"for\s+(\w+)\s*,\s*(\w+)\s+in\s+(\w+)\.items\(\)$", line)
    if m:
        return f"{m.group(3)}.each do |{m.group(1)}, {m.group(2)}|"
    m = re.match(r"for\s+(\w+)\s+in\s+(\w+)\.keys\(\)$", line)
    if m:
        return f"{m.group(2)}.each_key do |{m.group(1)}|"
    m = re.match(r"for\s+(\w+)\s+in\s+(\w+)\.values\(\)$", line)
    if m:
        return f"{m.group(2)}.each_value do |{m.group(1)}|"
    m = re.match(r"for\s+(\w+)\s+in\s+(.+)$", line)
    if m:
        var, xs = m.group(1), convert_expr(m.group(2).strip().rstrip(":"))
        if var in {"c", "ch", "char"} or xs in {"s", "word", "pattern", "t"}:
            if re.fullmatch(r"[A-Za-z_]\w*", xs):
                return f"{xs}.each_char do |{var}|"
        if xs in {"hm", "mp", "map", "freq", "idx", "cnt"}:
            return f"{xs}.each_key do |{var}|"
        return f"{xs}.each do |{var}|"
    return None


def convert_def(line: str) -> str | None:
    m = re.match(
        r"def\s+(\w+)\s*\((.*)\)\s*(?:->\s*[^:]+)?\s*:?\s*$",
        line,
    )
    if not m:
        return None
    name = camel_to_snake(m.group(1))
    params = convert_params(m.group(2))
    return f"def {name}({params})" if params else f"def {name}"


def convert_class(line: str) -> str | None:
    m = re.match(r"class\s+(\w+)\s*(?:\([^)]*\))?\s*:?\s*$", line)
    if not m:
        return None
    if m.group(1) == "Solution":
        return ""
    return f"class {m.group(1)}"


def convert_expr(expr: str) -> str:
    s = expr
    s = s.replace("None", "nil")
    s = s.replace("True", "true")
    s = s.replace("False", "false")
    # list comprehensions before `in` membership
    s = re.sub(
        r"\[\[\s*\]\s+for\s+\w+\s+in\s+range\(([^)]+)\)\]",
        r"Array.new(\1) { [] }",
        s,
    )
    s = re.sub(
        r"\[(.+?)\s+for\s+(\w+)\s+in\s+range\(([^)]+)\)\]",
        r"Array.new(\3) { |\2| \1 }",
        s,
    )
    s = re.sub(
        r"\[(.+?)\s+for\s+(\w+)\s+in\s+([^]]+)\]",
        r"\3.map { |\2| \1 }",
        s,
    )
    s = re.sub(r"float\(\s*['\"]inf['\"]\s*\)", "Float::INFINITY", s)
    s = re.sub(r"float\(\s*['\"]-inf['\"]\s*\)", "-Float::INFINITY", s)
    s = re.sub(r"\blen\s*\(([^)]+)\)", r"\1.length", s)
    s = re.sub(r"\bstr\s*\(([^)]+)\)", r"\1.to_s", s)
    s = re.sub(r"\bint\s*\(([^)]+)\)", r"\1.to_i", s)
    s = re.sub(r"\bord\s*\(([^)]+)\)", r"\1.ord", s)
    s = re.sub(r"\bchr\s*\(([^)]+)\)", r"\1.chr", s)
    s = re.sub(r"\babs\s*\(([^)]+)\)", r"\1.abs", s)
    s = re.sub(r"\bsorted\s*\(([^)]+)\)", r"\1.sort", s)
    s = re.sub(r"\breversed\s*\(([^)]+)\)", r"\1.reverse", s)
    s = re.sub(r"(?<![\w.])min\s*\(([^,]+),\s*([^)]+)\)", r"[\1, \2].min", s)
    s = re.sub(r"(?<![\w.])max\s*\(([^,]+),\s*([^)]+)\)", r"[\1, \2].max", s)
    s = re.sub(r"\[([^\]]+)\]\s*\*\s*(\w+|\d+)", r"Array.new(\2, \1)", s)
    s = re.sub(r"\.append\s*\(", ".push(", s)
    s = re.sub(r"\.add\s*\(", ".add(", s)
    s = re.sub(r"\.pop\s*\(\s*\)", ".pop", s)
    s = re.sub(r"\.pop\s*\(0\)", ".shift", s)
    s = re.sub(r"\.insert\s*\(0,\s*", ".unshift(", s)
    s = re.sub(r"\.sort\s*\(\s*\)", ".sort!", s)
    s = re.sub(r"\.reverse\s*\(\s*\)", ".reverse!", s)
    s = re.sub(r"\.items\s*\(\s*\)", "", s)
    s = re.sub(r"\.keys\s*\(\s*\)", ".keys", s)
    s = re.sub(r"\.values\s*\(\s*\)", ".values", s)
    s = re.sub(r"\.get\s*\(([^,]+),\s*([^)]+)\)", r".fetch(\1, \2)", s)
    s = re.sub(
        r"(\w+)\.setdefault\s*\(([^,]+),\s*([^)]+)\)\.append\s*\(([^)]+)\)",
        r"(\1[\2] ||= \3).push(\4)",
        s,
    )
    s = re.sub(r"\blist\s*\(([^)]+)\)", r"\1", s)
    s = re.sub(
        r"""['"]['"]\.join\((.+) for (\w+) in (\w+)\)""",
        r"\3.map { |\2| \1 }.join",
        s,
    )
    s = re.sub(r'\bf"([^"]*)"', _fstring, s)
    s = re.sub(r"\bf'([^']*)'", _fstring, s)
    s = re.sub(r"//", "/", s)
    s = re.sub(r"\bis not\b", "!=", s)
    s = re.sub(r"\bis\b", "==", s)
    s = convert_membership(s)
    s = convert_not(s)
    s = re.sub(r"\band\b", "&&", s)
    s = re.sub(r"\bor\b", "||", s)
    s = convert_dict_literals(s)
    s = re.sub(
        r"(.+?)\s+if\s+(.+?)\s+else\s+(.+)$",
        r"(\2 ? \1 : \3)",
        s,
    )
    s = re.sub(r"\bdeque\s*\(\s*\)", "[]", s)
    s = re.sub(r"\bself\.", "", s)
    return s


def convert_membership(s: str) -> str:
    # `x not in y` / `x in y`
    def repl_not_in(m: re.Match) -> str:
        x, y = m.group(1), m.group(2)
        if y in COLLECTIONS or y in {"hm", "mp", "map", "idx", "freq", "cnt"}:
            return f"!{y}.key?({x})"
        return f"!{y}.include?({x})"

    def repl_in(m: re.Match) -> str:
        x, y = m.group(1), m.group(2)
        if re.match(r"^['\"]", y):
            return f"{y}.include?({x})"
        if y in {"hm", "mp", "map", "idx", "freq", "cnt", "seen"} or y.endswith("map"):
            return f"{y}.key?({x})"
        return f"{y}.include?({x})"

    s = re.sub(r"(\S+)\s+not\s+in\s+(\S+)", repl_not_in, s)
    s = re.sub(r"(\S+)\s+in\s+(\S+)", repl_in, s)
    return s


def convert_not(s: str) -> str:
    s = re.sub(r"\bnot\s+(\w+)\s*\[", r"!\1[", s)

    def repl(m: re.Match) -> str:
        name = m.group(1)
        if name in COLLECTIONS:
            return f"{name}.empty?"
        if name in NODE_NAMES:
            return f"{name}.nil?"
        return f"!{name}"

    s = re.sub(r"\bnot\s+(\w+)\b", repl, s)
    return s


def _fstring(m: re.Match) -> str:
    inner = m.group(1)
    inner = re.sub(r"\{([^{}]+)\}", r"#{\1}", inner)
    return '"' + inner + '"'


def convert_dict_literals(s: str) -> str:
    return re.sub(r"""(['"](?:\\.|[^\\])*?['"])\s*:""", r"\1 =>", s)
    return re.sub(r"""(['"](?:\\.|[^\\])*?['"])\s*:""", r"\1 =>", s)


def is_block_header(py_line: str) -> bool:
    s = py_line.strip()
    return s.endswith(":") and not s.startswith("#")


def is_continuation(py_line: str) -> bool:
    s = py_line.strip()
    return s.startswith(("else:", "elif ", "except", "finally:", "elif:"))


def convert_header_or_stmt(line: str) -> str:
    raw = line.strip()
    if not raw:
        return ""
    if raw.startswith("#"):
        return convert_comment(raw)
    comment = ""
    if " #" in raw:
        raw, _, comment = raw.partition(" #")
        raw = raw.rstrip()
        comment = "  # " + comment
    # typed assignment: st: list[str] = []
    raw = re.sub(
        r"^(\w+)\s*:\s*(?:list|dict|set|tuple|Optional|int|str|bool|float)[\[\w\], \|]*\s*=",
        r"\1 =",
        raw,
    )
    raw = re.sub(r"^(\w+)\s*:\s*[A-Za-z_][\w\[\], \|]*\s*=", r"\1 =", raw)
    no_colon = raw[:-1].rstrip() if raw.endswith(":") else raw

    conv = convert_class(no_colon if raw.endswith(":") else raw)
    if conv is not None:
        return conv + comment
    conv = convert_def(no_colon if raw.endswith(":") else raw)
    if conv is not None:
        return conv + comment
    conv = convert_for(no_colon + (":" if raw.endswith(":") else ""))
    if conv is not None:
        return conv + comment

    if raw.startswith("elif "):
        rest = no_colon[len("elif ") :]
        return "elsif " + convert_expr(rest) + comment
    if raw == "else:" or no_colon == "else":
        return "else" + comment
    if raw.startswith("while "):
        rest = no_colon[len("while ") :]
        return "while " + convert_expr(rest) + comment
    if raw.startswith("if "):
        rest = no_colon[len("if ") :]
        return "if " + convert_expr(rest) + comment
    if no_colon == "pass":
        return "nil" + comment
    if raw.startswith("return "):
        return "return " + convert_expr(raw[len("return ") :]) + comment
    if no_colon == "return":
        return "return" + comment
    return convert_expr(no_colon if raw.endswith(":") else raw) + comment


def convert_comment(line: str) -> str:
    if "class ListNode" in line or "Definition for singly-linked" in line:
        return line  # replaced at block level
    if "class TreeNode" in line or "Definition for a binary tree" in line:
        return line
    line = line.replace("self.", "")
    line = re.sub(r"def __init__", "def initialize", line)
    return line


def unindent_solution_class(code: str) -> str:
    lines = code.split("\n")
    out: list[str] = []
    i = 0
    while i < len(lines):
        if re.match(r"^class Solution\s*:", lines[i].strip()):
            i += 1
            while i < len(lines):
                ln = lines[i]
                if ln.strip() and not ln.startswith((" ", "\t")) and not ln.strip().startswith("#"):
                    break
                if ln.startswith("    "):
                    out.append(ln[4:])
                elif ln.strip() == "":
                    out.append("")
                else:
                    out.append(ln)
                i += 1
            continue
        out.append(lines[i])
        i += 1
    return "\n".join(out)


def replace_node_comments(code: str) -> str:
    code = re.sub(
        r"(?:# Definition for singly-linked list\.\n)?(?:# class ListNode:[\s\S]*?(?:#\s*self\.next = next\n)+)",
        LISTNODE_COMMENT + "\n",
        code,
        count=1,
    )
    code = re.sub(
        r"(?:# Definition for a binary tree node\.\n)?(?:# class TreeNode:[\s\S]*?(?:#\s*self\.right = right\n)+)",
        TREENODE_COMMENT + "\n",
        code,
        count=1,
    )
    return code


def add_ends(py_code: str) -> str:
    lines = py_code.split("\n")
    out: list[str] = []
    stack: list[int] = []

    def indent_of(ln: str) -> int:
        if not ln.strip():
            return -1
        return len(ln) - len(ln.lstrip(" "))

    for idx, ln in enumerate(lines):
        stripped = ln.strip()
        if not stripped:
            out.append("")
            continue
        if stripped.startswith("#"):
            out.append(ln)
            continue
        indent = indent_of(ln)
        while stack and (
            indent < stack[-1]
            or (indent == stack[-1] and not is_continuation(stripped))
        ):
            out.append(" " * stack[-1] + "end")
            stack.pop()
        converted = convert_header_or_stmt(stripped)
        if converted == "" and stripped.startswith("class Solution"):
            continue
        out.append(" " * indent + converted if converted else "")
        if is_block_header(stripped) and not stripped.startswith("class Solution"):
            if is_continuation(stripped):
                continue
            stack.append(indent)
    while stack:
        out.append(" " * stack[-1] + "end")
        stack.pop()
    return "\n".join(out)


def tidy(code: str) -> str:
    lines = [ln.rstrip() for ln in code.split("\n")]
    # drop extra blank lines
    compact: list[str] = []
    blank = 0
    for ln in lines:
        if ln.strip() == "":
            blank += 1
            if blank <= 1:
                compact.append("")
        else:
            blank = 0
            compact.append(ln)
    # reindent
    indent = 0
    out: list[str] = []
    for ln in compact:
        s = ln.strip()
        if not s:
            out.append("")
            continue
        if s == "end" or s.startswith("else") or s.startswith("elsif "):
            indent = max(0, indent - 1)
        out.append("  " * indent + s)
        opens = (
            s.startswith("def ")
            or s.startswith("class ")
            or s.startswith("if ")
            or s.startswith("elsif ")
            or s.startswith("else")
            or s.startswith("while ")
            or s.startswith("unless ")
            or " do |" in s
            or s.endswith(" do")
        )
        postfix = bool(re.search(r"\s(?:if|unless)\s+\S+", s)) and not s.startswith(
            ("if ", "unless ", "elsif ")
        )
        if opens and not postfix:
            indent += 1
    text = "\n".join(out).strip() + "\n"
    if re.search(r"\bSet\.new\b", text) and "require 'set'" not in text:
        text = "require 'set'\n\n" + text
    return text


def looks_like_python(code: str) -> bool:
    return bool(
        re.search(r"^\s*(def |class |if |for |while ).*:\s*$", code, re.M)
        or "class Solution" in code
        or re.search(r"\b(self|None|True|False|elif |append\()", code)
    )


def looks_like_lc1_two_sum(code: str) -> bool:
    return bool(
        re.search(r"\btwoSum\b|\btwo_sum\b", code)
        and re.search(r"idx|unordered_map|dict|{}", code)
        and "two_sum_sorted" not in code
        and "twoSumSorted" not in code
        and re.search(r"enumerate|each_with_index|target -", code)
    )


def convert_python_to_ruby(code: str) -> str:
    if not looks_like_python(code) and ("def " in code and "end" in code):
        # already ruby-ish
        return code if code.endswith("\n") else code + "\n"
    result = code.replace("\t", "    ")
    result = re.sub(r"class Solution:\s*", "\n", result)
    result = re.sub(r"^from\s+\S+\s+import\s+.*\n", "", result, flags=re.M)
    result = re.sub(r"^import\s+\S+.*\n", "", result, flags=re.M)
    result = re.sub(r"\bdefaultdict\s*\(\s*int\s*\)", "Hash.new(0)", result)
    result = re.sub(r"\bdefaultdict\s*\(\s*list\s*\)", "Hash.new { |h, k| h[k] = [] }", result)
    result = re.sub(r"\bdefaultdict\s*\(\s*set\s*\)", "Hash.new { |h, k| h[k] = Set.new }", result)
    result = re.sub(r"\bCounter\s*\(([^)]+)\)", r"\1.tally", result)
    result = re.sub(r"\bdict\s*\(([^)]+)\)", r"\1", result)
    result = replace_node_comments(result)
    result = unindent_solution_class(result)
    result = add_ends(result)
    result = tidy(result)
    return result


def process_file(path: Path) -> bool:
    original = path.read_text(encoding="utf-8")
    content = original

    def repl(m: re.Match) -> str:
        lang, src = m.group(2).lower(), m.group(4)
        if looks_like_lc1_two_sum(src):
            return "```ruby\n" + TWO_SUM_RUBY + "```"
        if re.match(r"\s*Input:", src) or re.match(r"\s*Output:", src):
            return f"```\n{src.rstrip()}\n```"
        if lang == "ruby" and not looks_like_python(src):
            return m.group(0)
        ruby = convert_python_to_ruby(src)
        return f"```ruby\n{ruby}```"

    content = CODE_BLOCK_RE.sub(repl, content)
    content = content.replace("/blog_leetcode_python/", "/blog_leetcode_rust/")
    content = content.replace("/blog_leetcode/", "/blog_leetcode_rust/")
    content = content.replace(
        "https://robinali34.github.io/blog_leetcode_python/",
        "https://robinali34.github.io/blog_leetcode_rust/",
    )
    content = content.replace(
        "https://robinali34.github.io/blog_leetcode/",
        "https://robinali34.github.io/blog_leetcode_rust/",
    )
    content = re.sub(r"(categories:[^\n]*\s)(cpp|python)(\s)", r"\1ruby\3", content)
    content = re.sub(r"(categories:\s*\[[^\]]*?\b)(cpp|python)(\b)", r"\1ruby\3", content)
    content = re.sub(r"(tags:\s*\[[^\]]*?\b)(cpp|python)(\b)", r"\1ruby\3", content)

    if content != original:
        path.write_text(content, encoding="utf-8")
        return True
    return False


def main() -> int:
    targets = [Path(p) for p in sys.argv[1:]] if len(sys.argv) > 1 else []
    if not targets:
        targets.extend(ROOT.glob("_posts/*.md"))
        targets.extend(ROOT.glob("_templates/*.md"))
        for name in ("rust-guide.md", "python-guide.md", "cpp-guide.md"):
            p = ROOT / name
            if p.exists():
                targets.append(p)

    n = 0
    for path in targets:
        if path.name.endswith("cheatsheet.md"):
            continue
        if path.exists() and process_file(path):
            n += 1
            print(f"converted: {path.name}")
    leftover = 0
    for p in list(ROOT.glob("_posts/*.md")):
        t = p.read_text(encoding="utf-8")
        if "```python" in t or "```cpp" in t:
            leftover += 1
            print("leftover fence:", p.name)
    print(f"\nUpdated {n} files; leftover python/cpp fences: {leftover}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
