#!/usr/bin/env python3
"""Convert Rust code blocks in markdown to LeetCode-style Ruby."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

CODE_BLOCK_RE = re.compile(
    r"(```)(rust)(\s*\n)(.*?)(```)",
    re.DOTALL,
)

TWO_SUM_RUBY = '''# @param {Integer[]} nums
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
'''


def split_params(params: str) -> list[str]:
    parts: list[str] = []
    depth = 0
    current: list[str] = []
    for ch in params:
        if ch in "<([":
            depth += 1
        elif ch in ">)]":
            depth = max(0, depth - 1)
        if ch == "," and depth == 0:
            part = "".join(current).strip()
            if part:
                parts.append(part)
            current = []
        else:
            current.append(ch)
    part = "".join(current).strip()
    if part:
        parts.append(part)
    return parts


def param_name(param: str) -> str:
    param = param.strip()
    if not param:
        return ""
    param = re.sub(r"\s*=\s*.+$", "", param)
    if ":" in param:
        name = param.split(":", 1)[0].strip()
        name = name.replace("&mut", "").replace("&", "").strip()
        return name
    tokens = param.replace("&mut", "").replace("&", "").split()
    return tokens[-1] if tokens else ""


def convert_rust_to_ruby(code: str) -> str:
    result = code.replace("\t", "    ")

    # Drop use / crate imports
    result = re.sub(r"^\s*use\s+[\w:]+(?:\s*::\s*\{[^}]+\})?\s*;\s*\n", "", result, flags=re.M)
    result = re.sub(r"^\s*use\s+[\w:]+;\s*\n", "", result, flags=re.M)

    # ListNode / TreeNode comments
    result = re.sub(
        r"// Definition for singly-linked list\..*?(?=\n(?:impl|pub|fn|class|\Z))",
        """# Definition for singly-linked list.
# class ListNode
#     attr_accessor :val, :next
#     def initialize(val = 0, _next = nil)
#         @val = val
#         @next = _next
#     end
# end
""",
        result,
        flags=re.S,
    )
    result = re.sub(
        r"// Definition for a binary tree node\..*?(?=\n(?:impl|pub|fn|class|\Z))",
        """# Definition for a binary tree node.
# class TreeNode
#     attr_accessor :val, :left, :right
#     def initialize(val = 0, left = nil, right = nil)
#         @val = val
#         @left = left
#         @right = right
#     end
# end
""",
        result,
        flags=re.S,
    )

    result = re.sub(
        r"#\[derive[^\]]*\]\s*pub struct ListNode\s*\{[^}]*\}",
        """class ListNode
    attr_accessor :val, :next
    def initialize(val = 0, _next = nil)
        @val = val
        @next = _next
    end
end""",
        result,
        flags=re.S,
    )
    result = re.sub(
        r"#\[derive[^\]]*\]\s*pub struct TreeNode\s*\{[^}]*\}",
        """class TreeNode
    attr_accessor :val, :left, :right
    def initialize(val = 0, left = nil, right = nil)
        @val = val
        @left = left
        @right = right
    end
end""",
        result,
        flags=re.S,
    )

    # impl Solution { pub fn name(params) -> ret {
    def repl_impl_method(m: re.Match) -> str:
        name, params = m.group(1), m.group(2)
        names = [param_name(p) for p in split_params(params)]
        names = [n for n in names if n]
        return f"def {name}({', '.join(names)})"

    result = re.sub(r"\bimpl\s+Solution\s*\{", "", result)
    result = re.sub(
        r"^\s*pub fn (\w+)\s*\(([^)]*)\)\s*(?:->\s*[^{]+)?\s*\{",
        lambda m: repl_impl_method(m),
        result,
        flags=re.M,
    )
    result = re.sub(
        r"^\s*fn (\w+)\s*\(([^)]*)\)\s*(?:->\s*[^{]+)?\s*\{",
        lambda m: repl_impl_method(m),
        result,
        flags=re.M,
    )

    # Other impl blocks → class
    result = re.sub(r"\bimpl\s+(\w+)\s*\{", r"class \1", result)
    result = re.sub(
        r"^\s*pub fn new\s*\(([^)]*)\)\s*(?:->\s*Self)?\s*\{",
        lambda m: "def initialize(" + ", ".join(n for n in (param_name(p) for p in split_params(m.group(1))) if n) + ")",
        result,
        flags=re.M,
    )

    result = re.sub(r"\bpub struct\s+(\w+)\s*\{", r"class \1", result)
    result = re.sub(r"\bstruct\s+(\w+)\s*\{", r"class \1", result)

    # Types / constructors
    result = re.sub(r"\bHashMap::new\s*\(\s*\)", "{}", result)
    result = re.sub(r"\bHashSet::new\s*\(\s*\)", "Set.new", result)
    result = re.sub(r"\bBTreeMap::new\s*\(\s*\)", "{}", result)
    result = re.sub(r"\bBTreeSet::new\s*\(\s*\)", "Set.new", result)
    result = re.sub(r"\bVecDeque::new\s*\(\s*\)", "[]", result)
    result = re.sub(r"\bBinaryHeap::new\s*\(\s*\)", "[]", result)
    result = re.sub(r"\bVec::new\s*\(\s*\)", "[]", result)
    result = re.sub(r"\bString::new\s*\(\s*\)", '""', result)
    result = re.sub(r"\bString::from\s*\(([^)]+)\)", r"\1", result)
    result = re.sub(r"vec!\[([^\];]*)\s*;\s*([^\]]+)\]", r"Array.new(\2, \1)", result)
    result = re.sub(r"vec!\[([^\]]*)\]", r"[\1]", result)

    result = re.sub(r"\bSome\(Box::new\(ListNode::new\(([^)]*)\)\)\)", r"ListNode.new(\1)", result)
    result = re.sub(r"\bSome\(Rc::new\(RefCell::new\(TreeNode::new\(([^)]*)\)\)\)\)", r"TreeNode.new(\1)", result)
    result = re.sub(r"\bListNode::new\s*\(([^)]*)\)", r"ListNode.new(\1)", result)
    result = re.sub(r"\bTreeNode::new\s*\(([^)]*)\)", r"TreeNode.new(\1)", result)
    result = re.sub(r"\bNone\b", "nil", result)
    result = re.sub(r"\bunreachable!\s*\(\s*\)", "raise 'unreachable'", result)

    # let mut x = ...
    result = re.sub(r"\blet\s+mut\s+", "", result)
    result = re.sub(r"\blet\s+", "", result)

    # for loops
    result = re.sub(
        r"for\s+(\w+)\s+in\s+(\S+)\.\.=\s*(\S+)",
        r"(\2..\3).each do |\1|",
        result,
    )
    result = re.sub(
        r"for\s+(\w+)\s+in\s+\(0\.\.(\S+)\)\.rev\(\)",
        r"(\2 - 1).downto(0).each do |\1|",
        result,
    )
    result = re.sub(
        r"for\s+(\w+)\s+in\s+(\S+)\.\.(\S+)",
        r"(\2...\3).each do |\1|",
        result,
    )
    result = re.sub(
        r"for\s+&(\w+)\s+in\s+&(\w+)",
        r"\2.each do |\1|",
        result,
    )
    result = re.sub(
        r"for\s+(\w+)\s+in\s+&mut\s+(\w+)",
        r"\2.each do |\1|",
        result,
    )
    result = re.sub(
        r"for\s+(\w+)\s+in\s+&(\w+)",
        r"\2.each do |\1|",
        result,
    )
    result = re.sub(
        r"for\s+\((\w+),\s*&?(\w+)\)\s+in\s+(\w+)\.iter\(\)\.enumerate\(\)",
        r"\3.each_with_index do |\2, \1|",
        result,
    )
    result = re.sub(
        r"for\s*\((\w+),\s*&(\w+)\)\s+in\s+(\w+)\.iter\(\)\.enumerate\(\)",
        r"\3.each_with_index do |\2, \1|",
        result,
    )
    result = re.sub(
        r"for\s*\((\w+),\s*&(\w+)\)\s+in\s+(\w+)\.iter\(\)\.enumerate\(\)",
        r"\3.each_with_index do |\2, \1|",
        result,
    )
    result = re.sub(
        r"for\((\w+),\s*&(\w+)\)\s+in\s+(\w+)\.iter\(\)\.enumerate\(\)",
        r"\3.each_with_index do |\2, \1|",
        result,
    )
    result = re.sub(
        r"for\s+\((\w+),\s+(\w+)\)\s+in\s+&(\w+)",
        r"\3.each do |\1, \2|",
        result,
    )

    # comments
    result = re.sub(r"//", "#", result)

    # if let Some(...) = map.get(...)
    result = re.sub(
        r"if let Some\(&?(\w+)\)\s*=\s*(\w+)\.get\(&?\(?([^)]+)\)?\)\s*\{",
        r"if (\1 = \2[\3])",
        result,
    )
    result = re.sub(r"while let Some\(mut (\w+)\)\s*=\s*(\w+)", r"while (\1 = \2)", result)
    result = re.sub(r"\bSome\(([^)]+)\)", r"\1", result)

    # postfix single-line if { stmt }
    result = re.sub(
        r"\bif\s+([^{]+?)\s*\{\s*return\s+([^;}]+);\s*\}\s*(?!else)",
        r"return \2 if \1",
        result,
    )
    result = re.sub(
        r"\bif\s+([^{]+?)\s*\{\s*([^;}{]+);\s*\}\s*(?!else)",
        r"\2 if \1",
        result,
    )
    result = re.sub(r"\bwhile\s+([^;{]+)\s*\{", r"while \1", result)
    result = re.sub(r"\bif\s+([^;{]+)\s*\{", r"if \1", result)
    result = re.sub(r"\}\s*else if\s+", "\nelsif ", result)
    result = re.sub(r"\belse if\s+", "elsif ", result)
    result = re.sub(r"\}\s*else\s*\{", "\nelse", result)
    result = re.sub(r"\belse\s*\{", "else", result)

    # methods
    result = re.sub(r"\.is_empty\s*\(\s*\)", ".empty?", result)
    result = re.sub(r"\.len\s*\(\s*\)", ".length", result)
    result = re.sub(r"\.push_front\s*\(", ".unshift(", result)
    result = re.sub(r"\.push_back\s*\(", ".push(", result)
    result = re.sub(r"\.pop_front\s*\(\s*\)", ".shift", result)
    result = re.sub(r"\.pop_back\s*\(\s*\)", ".pop", result)
    result = re.sub(r"\.pop\s*\(\s*\)", ".pop", result)
    result = re.sub(r"\.push\s*\(", ".push(", result)
    result = re.sub(r"\.insert\s*\(([^,]+),\s*([^)]+)\)", r"[\1] = \2", result)
    result = re.sub(r"\.get\(&?\(?([^)]+)\)?\)", r"[\1]", result)
    result = re.sub(r"\.contains_key\(&?\(?([^)]+)\)?\)", r".key?(\1)", result)
    result = re.sub(r"\.contains\(&?\(?([^)]+)\)?\)", r".include?(\1)", result)
    result = re.sub(r"\.remove\(([^)]+)\)", r".delete(\1)", result)
    result = re.sub(r"\*(\w+)\.entry\(([^)]+)\)\.or_insert\(0\)\s*\+=\s*1", r"\1[\2] = (\1[\2] || 0) + 1", result)
    result = re.sub(r"(\w+)\.entry\(([^)]+)\)\.or_insert\(0\)", r"(\1[\2] ||= 0)", result)
    result = re.sub(r"\.front\(\)\.copied\(\)\.unwrap\(\)", "[0]", result)
    result = re.sub(r"\.last\(\)\.copied\(\)\.unwrap\(\)", "[-1]", result)
    result = re.sub(r"\.first\(\)", "[0]", result)
    result = re.sub(r"\.last\(\)", "[-1]", result)
    result = re.sub(r"\.peek\(\)", "[-1]", result)
    result = re.sub(r"\.sort_unstable\s*\(\s*\)", ".sort!", result)
    result = re.sub(r"\.sort\s*\(\s*\)", ".sort!", result)
    result = re.sub(r"\.sort_by\(\|a, b\| b\.cmp\(a\)\)", ".sort!.reverse!", result)
    result = re.sub(r"\.reverse\s*\(\s*\)", ".reverse!", result)
    result = re.sub(r"\.clear\s*\(\s*\)", ".clear", result)
    result = re.sub(r"\.iter\(\)\.sum::<i32>\(\)", ".sum", result)
    result = re.sub(r"\.iter\(\)\.max\(\)", ".max", result)
    result = re.sub(r"\.iter\(\)\.min\(\)", ".min", result)
    result = re.sub(r"\.iter\(\)\.rev\(\)", ".reverse_each", result)
    result = re.sub(r"\.iter\(\)", ".each", result)
    result = re.sub(r"\.enumerate\(\)", ".each_with_index", result)
    result = re.sub(r"\.binary_search\(&?([^)]+)\)\.is_ok\(\)", r".bsearch { |x| x >= \1 }", result)
    result = re.sub(r"\.to_string\s*\(\s*\)", ".to_s", result)
    result = re.sub(r"\.parse::<i32>\(\)\.unwrap\(\)", ".to_i", result)
    result = re.sub(r"\.parse::<i64>\(\)\.unwrap\(\)", ".to_i", result)
    result = re.sub(r"\.count_ones\s*\(\s*\)", ".to_s(2).count('1')", result)
    result = re.sub(r"\.abs\s*\(\s*\)", ".abs", result)
    result = re.sub(r"\.gcd\(([^)]+)\)", r".gcd(\1)", result)
    result = re.sub(r"\.is_none\s*\(\s*\)", ".nil?", result)
    result = re.sub(r"\.is_some\s*\(\s*\)", "", result)
    result = re.sub(r"\.as_ref\(\)", "", result)
    result = re.sub(r"\.take\(\)", "", result)
    result = re.sub(r"\.clone\(\)", ".dup", result)
    result = re.sub(r"\.borrow\(\)", "", result)
    result = re.sub(r"\.borrow_mut\(\)", "", result)

    result = re.sub(r"(\w+)\.max\(([^)]+)\)", r"[\1, \2].max", result)
    result = re.sub(r"(\w+)\.min\(([^)]+)\)", r"[\1, \2].min", result)
    result = re.sub(r"std::mem::swap\(&mut (\w+),\s*&mut (\w+)\)", r"\1, \2 = \2, \1", result)

    result = re.sub(r"\bi32::MAX\b", "(2**31 - 1)", result)
    result = re.sub(r"\bi32::MIN\b", "(-(2**31))", result)
    result = re.sub(r"\bi64::MAX\b", "(2**63 - 1)", result)
    result = re.sub(r"\bi64::MIN\b", "(-(2**63))", result)

    # casts and refs
    result = re.sub(r" as usize", "", result)
    result = re.sub(r" as i32", "", result)
    result = re.sub(r" as i64", "", result)
    result = re.sub(r" as u32", "", result)
    result = re.sub(r" as f64", "", result)
    result = re.sub(r"\b&mut\s+", "", result)
    result = re.sub(r"(?<![&\w])&(?!&)", "", result)

    # leftover type annotations in declarations
    result = re.sub(
        r"\b(?:Vec(?:<[^>]+>)?|HashMap(?:<[^>]+>)?|HashSet(?:<[^>]+>)?|VecDeque(?:<[^>]+>)?|BinaryHeap(?:<[^>]+>)?|BTreeMap(?:<[^>]+>)?|BTreeSet(?:<[^>]+>)?|Option(?:<[^>]+>)?|String|i32|i64|usize|bool|char)\s+(\w+)\s*=",
        r"\1 =",
        result,
    )

    # increment leftovers { x += 1; x }
    result = re.sub(r"\{\s*(\w+) \+= 1; \1\s*\}", r"(\1 += 1)", result)
    result = re.sub(r"\{\s*(?:let t = )?(\w+); \1 \+= 1; t\s*\}", r"(\1 += 1) - 1", result)
    result = re.sub(r"\{\s*let t = (\w+); \1 \+= 1; t\s*\}", r"(\1 += 1) - 1", result)
    result = re.sub(r"\{\s*(\w+) \-= 1; \1\s*\}", r"(\1 -= 1)", result)
    result = re.sub(r"\{\s*let t = (\w+); \1 \-= 1; t\s*\}", r"(\1 -= 1) + 1", result)
    result = re.sub(r"\(u8\)", "", result)
    result = re.sub(r"\(i32\)", "", result)

    # self. → @
    result = re.sub(r"\bself\.", "@", result)

    # closing braces of impl/fn — drop lone closing braces that were class end? keep as end
    # Convert remaining { } to Ruby end (best-effort, line-based)
    result = convert_braces_to_end(result)

    # cleanup
    result = re.sub(r"\btrue\b", "true", result)
    result = re.sub(r"\bfalse\b", "false", result)
    result = re.sub(r";\s*$", "", result, flags=re.M)
    result = re.sub(r"return ([^;\n]+);", r"return \1", result)
    result = re.sub(r"\n{3,}", "\n\n", result)
    result = re.sub(r"^\s*end\s*\nend\s*$", "end", result, flags=re.M)

    if "Set.new" in result or re.search(r"\bSet\b", result):
        if "require 'set'" not in result:
            result = "require 'set'\n\n" + result.lstrip("\n")

    return result.strip() + "\n"


def convert_braces_to_end(code: str) -> str:
    lines = code.split("\n")
    out: list[str] = []
    for line in lines:
        stripped = line.strip()
        # trailing { already removed from def/while/if
        if stripped == "{":
            continue
        if stripped == "}":
            indent = line[: len(line) - len(line.lstrip())]
            out.append(f"{indent}end")
            continue
        # inline { stmt }
        line = re.sub(r"\{\s*return ([^}]+);\s*\}", r"then return \1", line)
        line = re.sub(r"\{\s*([^}{]+);\s*\}", r"\n" + (" " * (len(line) - len(line.lstrip()) + 2)) + r"\1", line)
        if line.rstrip().endswith("{"):
            line = line.rstrip()[:-1].rstrip()
        if stripped.startswith("}") and "end" not in stripped:
            indent = line[: len(line) - len(line.lstrip())]
            rest = stripped[1:].strip()
            out.append(f"{indent}end" + (f" {rest}" if rest else ""))
            continue
        out.append(line)
    return "\n".join(out)


def looks_like_hash_two_sum(code: str) -> bool:
    return bool(
        re.search(r"\bfn two_sum\b|\bpub fn two_sum\b|\bdef two_sum\b", code)
        and "HashMap" in code
        or ("idx" in code and "target - x" in code)
    )


def process_file(path: Path) -> bool:
    original = path.read_text(encoding="utf-8")
    content = original

    def repl_block(m: re.Match) -> str:
        rust = m.group(4)
        if looks_like_hash_two_sum(rust) and "each_with_index" not in rust and ".len()" not in rust.replace("a.len()", ""):
            # classic LC 1 hash map two sum
            if "HashMap" in rust or "idx" in rust:
                return "```ruby\n" + TWO_SUM_RUBY + "```"
        ruby = convert_rust_to_ruby(rust)
        return f"```ruby\n{ruby}```"

    content = CODE_BLOCK_RE.sub(repl_block, content)

    # Front matter / prose language tags that are clearly code-related
    content = re.sub(r"(categories:[^\n]*\s)rust(\s)", r"\1ruby\2", content)
    content = re.sub(r"(categories:\s*\[[^\]]*?\b)rust(\b)", r"\1ruby\2", content)
    content = re.sub(r"(tags:\s*\[[^\]]*?\b)rust(\b)", r"\1ruby\2", content)

    if content != original:
        path.write_text(content, encoding="utf-8")
        return True
    return False


def main() -> int:
    targets: list[Path] = []
    if len(sys.argv) > 1:
        targets = [Path(p) for p in sys.argv[1:]]
    else:
        targets.extend(ROOT.glob("_posts/*.md"))
        targets.extend(ROOT.glob("_templates/*.md"))
        for name in ("rust-guide.md", "about.md", "README.md", "leetcode-questions-list.md"):
            p = ROOT / name
            if p.exists():
                targets.append(p)

    converted = 0
    for path in targets:
        if not path.exists():
            continue
        if process_file(path):
            converted += 1
            print(f"converted: {path}")
    leftover = 0
    for p in list(ROOT.glob("_posts/*.md")) + [ROOT / "rust-guide.md"]:
        if p.exists() and "```rust" in p.read_text(encoding="utf-8"):
            leftover += 1
            print(f"still rust: {p.name}")
    print(f"\nUpdated {converted} files; remaining ```rust files: {leftover}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
