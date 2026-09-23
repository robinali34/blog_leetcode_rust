#!/usr/bin/env python3
"""Convert C++ code blocks in markdown to LeetCode-style Rust."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

CODE_BLOCK_RE = re.compile(
    r"(```)(cpp|c\+\+|C\+\+)(\s*\n)(.*?)(```)",
    re.DOTALL,
)


def camel_to_snake(name: str) -> str:
    if not name or name[0].isupper() and name.isidentifier() and "_" not in name and name.lower() != name:
        # Type names stay PascalCase
        if name[:1].isupper() and not any(c.islower() and i > 0 and name[i - 1].islower() for i, c in enumerate(name) if False):
            pass
    if name[:1].isupper() and re.match(r"^[A-Z][A-Za-z0-9]+$", name) and not re.search(r"[a-z][A-Z]", name):
        return name  # ALLCAPS-ish types like LRUCache still have mixed case
    if name[:1].isupper() and re.search(r"[a-z]", name):
        # PascalCase type: keep as-is for structs; methods that are PascalCase are rare
        return name
    s1 = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s1).lower()


def method_to_snake(name: str) -> str:
    if name in {"new", "drop"}:
        return name
    s1 = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s1).lower()


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


def convert_cpp_type(cpp_type: str, *, param: bool = False, mutating: bool = False) -> str:
    t = cpp_type.strip()
    t = re.sub(r"\bconst\s+", "", t)
    t = re.sub(r"\bstatic\s+", "", t)
    t = re.sub(r"\bunsigned\s+long\s+long\b", "u64", t)
    t = re.sub(r"\blong\s+long\b", "i64", t)
    t = re.sub(r"\bunsigned\s+int\b", "u32", t)
    t = re.sub(r"\bunsigned\s+long\b", "u64", t)
    t = re.sub(r"\bunsigned\s+char\b", "u8", t)
    is_ref = "&" in t
    is_ptr = "*" in t
    t = t.replace("&", "").replace("*", "")
    t = re.sub(r"\bstd::", "", t)
    t = re.sub(r"\s+", " ", t).strip()

    def vec_inner(inner: str) -> str:
        return convert_cpp_type(inner, param=False)

    # Nested containers — longest first
    replacements = [
        (r"vector<\s*vector<\s*vector<\s*int\s*>\s*>\s*>", "Vec<Vec<Vec<i32>>>"),
        (r"vector<\s*vector<\s*int\s*>\s*>", "Vec<Vec<i32>>"),
        (r"vector<\s*vector<\s*long\s*>\s*>", "Vec<Vec<i64>>"),
        (r"vector<\s*vector<\s*char\s*>\s*>", "Vec<Vec<char>>"),
        (r"vector<\s*vector<\s*string\s*>\s*>", "Vec<Vec<String>>"),
        (r"vector<\s*vector<\s*bool\s*>\s*>", "Vec<Vec<bool>>"),
        (r"vector<\s*vector<\s*double\s*>\s*>", "Vec<Vec<f64>>"),
        (r"vector<\s*string\s*>", "Vec<String>"),
        (r"vector<\s*int\s*>", "Vec<i32>"),
        (r"vector<\s*long\s*>", "Vec<i64>"),
        (r"vector<\s*char\s*>", "Vec<char>"),
        (r"vector<\s*bool\s*>", "Vec<bool>"),
        (r"vector<\s*double\s*>", "Vec<f64>"),
        (r"vector<\s*ListNode\s*>", "Vec<Option<Box<ListNode>>>"),
        (r"vector<\s*TreeNode\s*>", "Vec<Option<Rc<RefCell<TreeNode>>>>"),
        (r"unordered_map<\s*int\s*,\s*int\s*>", "HashMap<i32, i32>"),
        (r"unordered_map<\s*int\s*,\s*vector<\s*int\s*>\s*>", "HashMap<i32, Vec<i32>>"),
        (r"unordered_map<\s*string\s*,\s*int\s*>", "HashMap<String, i32>"),
        (r"unordered_map<\s*string\s*,\s*string\s*>", "HashMap<String, String>"),
        (r"unordered_map<\s*char\s*,\s*int\s*>", "HashMap<char, i32>"),
        (r"unordered_set<\s*int\s*>", "HashSet<i32>"),
        (r"unordered_set<\s*string\s*>", "HashSet<String>"),
        (r"unordered_set<\s*char\s*>", "HashSet<char>"),
        (r"unordered_set<\s*long\s*>", "HashSet<i64>"),
        (r"map<\s*int\s*,\s*int\s*>", "BTreeMap<i32, i32>"),
        (r"set<\s*int\s*>", "BTreeSet<i32>"),
        (r"set<\s*string\s*>", "BTreeSet<String>"),
        (r"multiset<\s*int\s*>", "BTreeMap<i32, i32>"),
        (r"queue<\s*int\s*>", "VecDeque<i32>"),
        (r"queue<\s*pair<\s*int\s*,\s*int\s*>\s*>", "VecDeque<(i32, i32)>"),
        (r"queue<\s*TreeNode\s*>", "VecDeque<Option<Rc<RefCell<TreeNode>>>>"),
        (r"queue<\s*ListNode\s*>", "VecDeque<Option<Box<ListNode>>>"),
        (r"stack<\s*int\s*>", "Vec<i32>"),
        (r"stack<\s*char\s*>", "Vec<char>"),
        (r"deque<\s*int\s*>", "VecDeque<i32>"),
        (r"priority_queue<\s*int\s*,\s*vector<\s*int\s*>\s*,\s*greater<\s*int\s*>\s*>", "BinaryHeap<Reverse<i32>>"),
        (r"priority_queue<\s*int\s*>", "BinaryHeap<i32>"),
        (r"pair<\s*int\s*,\s*int\s*>", "(i32, i32)"),
        (r"pair<\s*int\s*,\s*string\s*>", "(i32, String)"),
        (r"optional<\s*int\s*>", "Option<i32>"),
    ]
    for pat, repl in replacements:
        t = re.sub(pat, repl, t)

    t = re.sub(r"\bvector<\s*(\w+)\s*>", r"Vec<\1>", t)
    t = re.sub(r"\bunordered_map<\s*(\w+)\s*,\s*(\w+)\s*>", r"HashMap<\1, \2>", t)
    t = re.sub(r"\bunordered_set<\s*(\w+)\s*>", r"HashSet<\1>", t)
    t = re.sub(r"\bmap<\s*(\w+)\s*,\s*(\w+)\s*>", r"BTreeMap<\1, \2>", t)
    t = re.sub(r"\bset<\s*(\w+)\s*>", r"BTreeSet<\1>", t)
    t = re.sub(r"\bqueue<\s*(\w+)\s*>", r"VecDeque<\1>", t)
    t = re.sub(r"\bstack<\s*(\w+)\s*>", r"Vec<\1>", t)
    t = re.sub(r"\bdeque<\s*(\w+)\s*>", r"VecDeque<\1>", t)
    t = re.sub(r"\bpriority_queue<\s*(\w+)\s*>", r"BinaryHeap<\1>", t)
    t = re.sub(r"\bpair<\s*(\w+)\s*,\s*(\w+)\s*>", r"(\1, \2)", t)

    simple = {
        "void": "()",
        "int": "i32",
        "long": "i64",
        "bool": "bool",
        "double": "f64",
        "float": "f32",
        "char": "char",
        "string": "String",
        "size_t": "usize",
        "string_view": "&str",
        "uint32_t": "u32",
        "int64_t": "i64",
        "uint64_t": "u64",
        "int32_t": "i32",
    }
    if t in simple:
        t = simple[t]

    if is_ptr:
        if "ListNode" in t:
            t = "Option<Box<ListNode>>"
        elif "TreeNode" in t:
            t = "Option<Rc<RefCell<TreeNode>>>"
        elif "Node" in t and "ListNode" not in t and "TreeNode" not in t:
            t = f"Option<Rc<RefCell<{t}>>>"

    if param and mutating and is_ref and t.startswith("Vec"):
        t = f"&mut {t}"
    elif param and is_ref and t == "String":
        t = "String"
    elif param and is_ref and not t.startswith("&"):
        # LeetCode typically takes owned collections
        pass

    return t


def convert_param(param: str, *, mutating: bool = False) -> str:
    param = param.strip()
    if not param or param == "void":
        return ""
    # default arguments
    param = re.sub(r"\s*=\s*.+$", "", param)
    param = param.replace("...", "")
    tokens = param.split()
    if not tokens:
        return ""
    name = tokens[-1].replace("&", "").replace("*", "").strip()
    type_part = " ".join(tokens[:-1]) if len(tokens) > 1 else "i32"
    # catch `int& x` already split
    rust_ty = convert_cpp_type(type_part + ("&" if "&" in param and "&" not in type_part else ""), param=True, mutating=mutating)
    if name in {"this"}:
        return ""
    return f"{name}: {rust_ty}"


def convert_signature(ret: str, name: str, params: str) -> str:
    mutating = "void" in ret and "&" in params
    rust_ret = convert_cpp_type(ret)
    rust_name = method_to_snake(name)
    rust_params = []
    for p in split_params(params):
        converted = convert_param(p, mutating=mutating)
        if converted:
            rust_params.append(converted)
    param_str = ", ".join(rust_params)
    if rust_ret == "()":
        return f"pub fn {rust_name}({param_str}) {{"
    return f"pub fn {rust_name}({param_str}) -> {rust_ret} {{"


def convert_for_loops(code: str) -> str:
    # for (int i = 0; i < n; i++) / ++i
    code = re.sub(
        r"for\s*\(\s*(?:int|long|size_t|auto)\s+(\w+)\s*=\s*([^;]+);\s*\1\s*<\s*([^;]+);\s*(?:\+\+\1|\1\+\+|\1\s*\+=\s*1)\s*\)",
        r"for \1 in \2..\3",
        code,
    )
    code = re.sub(
        r"for\s*\(\s*(?:int|long|size_t|auto)\s+(\w+)\s*=\s*([^;]+);\s*\1\s*<=\s*([^;]+);\s*(?:\+\+\1|\1\+\+|\1\s*\+=\s*1)\s*\)",
        r"for \1 in \2..=\3",
        code,
    )
    # reverse: for (int i = n - 1; i >= 0; i--)
    code = re.sub(
        r"for\s*\(\s*(?:int|long)\s+(\w+)\s*=\s*([^;]+)\s*-\s*1;\s*\1\s*>=\s*0;\s*(?:--\1|\1--|\1\s*-=\s*1)\s*\)",
        r"for \1 in (0..\2).rev()",
        code,
    )
    code = re.sub(
        r"for\s*\(\s*(?:int|long)\s+(\w+)\s*=\s*([^;]+);\s*\1\s*>=\s*0;\s*(?:--\1|\1--)\s*\)",
        r"for \1 in (0..=\2).rev()",
        code,
    )
    # range-for
    code = re.sub(
        r"for\s*\(\s*(?:const\s+)?(?:auto|int|long|char|string|bool)\s*&\s*(\w+)\s*:\s*(\w+)\s*\)",
        r"for \1 in &mut \2",
        code,
    )
    code = re.sub(
        r"for\s*\(\s*(?:const\s+)?(?:auto|int|long|char|string|bool)\s+(\w+)\s*:\s*(\w+)\s*\)",
        r"for &\1 in &\2",
        code,
    )
    code = re.sub(
        r"for\s*\(\s*auto\s*&\s*\[(\w+)\s*,\s*(\w+)\]\s*:\s*(\w+)\s*\)",
        r"for (\1, \2) in &\3",
        code,
    )
    code = re.sub(
        r"for\s*\(\s*auto\s*\[(\w+)\s*,\s*(\w+)\]\s*:\s*(\w+)\s*\)",
        r"for (\1, \2) in &\3",
        code,
    )
    return code


def split_decl_list(decl: str) -> list[tuple[str, str | None]]:
    """Split `a = 0, b = n - 1` into [(name, init), ...]."""
    items: list[tuple[str, str | None]] = []
    depth = 0
    current: list[str] = []
    for ch in decl:
        if ch in "([{":
            depth += 1
        elif ch in ")]}":
            depth = max(0, depth - 1)
        if ch == "," and depth == 0:
            part = "".join(current).strip()
            if part:
                items.append(_parse_one_decl(part))
            current = []
        else:
            current.append(ch)
    part = "".join(current).strip()
    if part:
        items.append(_parse_one_decl(part))
    return items


def _parse_one_decl(part: str) -> tuple[str, str | None]:
    if "=" in part:
        name, init = part.split("=", 1)
        return name.strip().replace("&", "").replace("*", ""), init.strip()
    return part.strip().replace("&", "").replace("*", ""), None


def rust_lets_from_decl(type_name: str, decl: str, indent: str) -> str:
    defaults = {
        "i32": "0",
        "int": "0",
        "i64": "0",
        "long": "0",
        "usize": "0",
        "u32": "0",
        "u64": "0",
        "f64": "0.0",
        "double": "0.0",
        "bool": "false",
        "char": "'\\0'",
        "String": "String::new()",
        "string": "String::new()",
    }
    lines = []
    for name, init in split_decl_list(decl):
        if not name:
            continue
        value = init if init is not None else defaults.get(type_name, "Default::default()")
        lines.append(f"{indent}let mut {name} = {value};")
    return "\n".join(lines)


def convert_declarations(code: str) -> str:
    # vector / Vec sized init
    code = re.sub(
        r"^(\s*)Vec<i32>\s+(\w+)\s*\(\s*([^,]+)\s*,\s*([^)]+)\s*\)\s*;",
        r"\1let mut \2 = vec![\4; \3];",
        code,
        flags=re.M,
    )
    code = re.sub(
        r"^(\s*)Vec<i64>\s+(\w+)\s*\(\s*([^,]+)\s*,\s*([^)]+)\s*\)\s*;",
        r"\1let mut \2 = vec![\4; \3];",
        code,
        flags=re.M,
    )
    code = re.sub(
        r"^(\s*)Vec<bool>\s+(\w+)\s*\(\s*([^,]+)\s*,\s*(true|false)\s*\)\s*;",
        r"\1let mut \2 = vec![\4; \3];",
        code,
        flags=re.M,
    )
    code = re.sub(
        r"^(\s*)Vec<Vec<i32>>\s+(\w+)\s*\(\s*([^,]+)\s*,\s*Vec<i32>\s*\(\s*([^,]+)\s*,\s*([^)]+)\s*\)\s*\)\s*;",
        r"\1let mut \2 = vec![vec![\5; \4]; \3];",
        code,
        flags=re.M,
    )
    code = re.sub(
        r"^(\s*)Vec<(\w+)>\s+(\w+)\s*\(\s*([^)]+)\s*\)\s*;",
        r"\1let mut \3 = vec![Default::default(); \4];",
        code,
        flags=re.M,
    )
    code = re.sub(
        r"^(\s*)(Vec<[^>]+>|HashMap<[^>]+>|HashSet<[^>]+>|VecDeque<[^>]+>|BinaryHeap<[^>]+>|BTreeMap<[^>]+>|BTreeSet<[^>]+>)\s+(\w+)\s*;",
        lambda m: f"{m.group(1)}let mut {m.group(3)} = {m.group(2).split('<')[0]}::new();",
        code,
        flags=re.M,
    )

    def repl_prim(m: re.Match) -> str:
        return rust_lets_from_decl(m.group(2), m.group(3), m.group(1))

    code = re.sub(
        r"^(\s*)(int|i32|i64|long|usize|u32|u64|f64|double|float|bool|char|string|String)\s+([^;]+);",
        repl_prim,
        code,
        flags=re.M,
    )
    code = re.sub(
        r"^(\s*)Option<Box<ListNode>>\s+(\w+)\s*=\s*([^;]+);",
        r"\1let mut \2 = \3;",
        code,
        flags=re.M,
    )
    code = re.sub(
        r"^(\s*)Option<Rc<RefCell<TreeNode>>>\s+(\w+)\s*=\s*([^;]+);",
        r"\1let mut \2 = \3;",
        code,
        flags=re.M,
    )
    code = re.sub(
        r"^(\s*)Option<Box<ListNode>>\s+(\w+)\s*;",
        r"\1let mut \2 = None;",
        code,
        flags=re.M,
    )
    code = re.sub(
        r"^(\s*)Option<Rc<RefCell<TreeNode>>>\s+(\w+)\s*;",
        r"\1let mut \2 = None;",
        code,
        flags=re.M,
    )
    return code


def convert_if_while(code: str) -> str:
    # if (cond) {  / while (cond) {
    code = re.sub(r"\belse\s+if\s*\((.+)\)\s*\{", r"else if \1 {", code)
    code = re.sub(r"\bif\s*\((.+)\)\s*\{", r"if \1 {", code)
    code = re.sub(r"\bwhile\s*\((.+)\)\s*\{", r"while \1 {", code)
    code = re.sub(r"\bswitch\s*\((.+)\)\s*\{", r"match \1 {", code)
    # single-line if (cond) stmt;
    code = re.sub(
        r"\belse\s+if\s*\((.+)\)\s*(return\s+[^;]+;)",
        r"else if \1 { \2 }",
        code,
    )
    code = re.sub(
        r"\bif\s*\((.+)\)\s*(return\s+[^;]+;)",
        r"if \1 { \2 }",
        code,
    )
    code = re.sub(
        r"\bif\s*\((.+)\)\s*([^;{]+;)",
        r"if \1 { \2 }",
        code,
    )
    # else without braces
    code = re.sub(
        r"^(\s*)else\n(\s+)(?!if\b)([^;{]+;)",
        r"\1else {\n\2\3\n\1}",
        code,
        flags=re.M,
    )
    code = re.sub(
        r"\belse\s+(?!if\b)([^;{\n]+;)",
        r"else { \1 }",
        code,
    )
    return code


def convert_cpp_to_rust(code: str) -> str:
    result = code.replace("\t", "    ")

    # Includes / using
    result = re.sub(r"^\s*#include[^\n]*\n", "", result, flags=re.M)
    result = re.sub(r"^\s*using\s+namespace\s+std\s*;\s*\n", "", result, flags=re.M)
    result = re.sub(r"^\s*using\s+std::\w+\s*;\s*\n", "", result, flags=re.M)
    result = re.sub(r"^\s*#pragma[^\n]*\n", "", result, flags=re.M)
    result = re.sub(r"^\s*#define[^\n]*\n", "", result, flags=re.M)

    result = re.sub(r"^\s*(public|private|protected)\s*:\s*\n", "", result, flags=re.M)
    result = re.sub(r"\bstd::", "", result)

    # ListNode / TreeNode comments → Rust definitions
    result = re.sub(
        r"/\*\s*Definition for singly-linked list\..*?\*/",
        """// Definition for singly-linked list.
// #[derive(PartialEq, Eq, Clone, Debug)]
// pub struct ListNode {
//   pub val: i32,
//   pub next: Option<Box<ListNode>>,
// }""",
        result,
        flags=re.S,
    )
    result = re.sub(
        r"/\*\s*Definition for a binary tree node\..*?\*/",
        """// Definition for a binary tree node.
// #[derive(Debug, PartialEq, Eq)]
// pub struct TreeNode {
//   pub val: i32,
//   pub left: Option<Rc<RefCell<TreeNode>>>,
//   pub right: Option<Rc<RefCell<TreeNode>>>,
// }""",
        result,
        flags=re.S,
    )

    # struct ListNode { ... } compact
    result = re.sub(
        r"struct\s+ListNode\s*\{[^}]*\}",
        """#[derive(PartialEq, Eq, Clone, Debug)]
pub struct ListNode {
    pub val: i32,
    pub next: Option<Box<ListNode>>,
}""",
        result,
        flags=re.S,
    )
    result = re.sub(
        r"struct\s+TreeNode\s*\{[^}]*\}",
        """#[derive(Debug, PartialEq, Eq)]
pub struct TreeNode {
    pub val: i32,
    pub left: Option<Rc<RefCell<TreeNode>>>,
    pub right: Option<Rc<RefCell<TreeNode>>>,
}""",
        result,
        flags=re.S,
    )

    # Convert types before rewriting class/methods
    nested_type_order = [
        (r"\bvector<\s*vector<\s*vector<\s*int\s*>\s*>\s*>", "Vec<Vec<Vec<i32>>>"),
        (r"\bvector<\s*vector<\s*int\s*>\s*>", "Vec<Vec<i32>>"),
        (r"\bvector<\s*vector<\s*long\s*>\s*>", "Vec<Vec<i64>>"),
        (r"\bvector<\s*vector<\s*char\s*>\s*>", "Vec<Vec<char>>"),
        (r"\bvector<\s*vector<\s*string\s*>\s*>", "Vec<Vec<String>>"),
        (r"\bvector<\s*vector<\s*bool\s*>\s*>", "Vec<Vec<bool>>"),
        (r"\bvector<\s*vector<\s*double\s*>\s*>", "Vec<Vec<f64>>"),
        (r"\bvector<\s*string\s*>", "Vec<String>"),
        (r"\bvector<\s*int\s*>", "Vec<i32>"),
        (r"\bvector<\s*long\s*>", "Vec<i64>"),
        (r"\bvector<\s*char\s*>", "Vec<char>"),
        (r"\bvector<\s*bool\s*>", "Vec<bool>"),
        (r"\bvector<\s*double\s*>", "Vec<f64>"),
        (r"\bvector<\s*ListNode\s*\*\s*>", "Vec<Option<Box<ListNode>>>"),
        (r"\bvector<\s*TreeNode\s*\*\s*>", "Vec<Option<Rc<RefCell<TreeNode>>>>"),
        (r"\bunordered_map<\s*int\s*,\s*vector<\s*int\s*>\s*>", "HashMap<i32, Vec<i32>>"),
        (r"\bunordered_map<\s*int\s*,\s*int\s*>", "HashMap<i32, i32>"),
        (r"\bunordered_map<\s*long\s*,\s*int\s*>", "HashMap<i64, i32>"),
        (r"\bunordered_map<\s*string\s*,\s*int\s*>", "HashMap<String, i32>"),
        (r"\bunordered_map<\s*string\s*,\s*string\s*>", "HashMap<String, String>"),
        (r"\bunordered_map<\s*char\s*,\s*int\s*>", "HashMap<char, i32>"),
        (r"\bunordered_map<\s*int\s*,\s*string\s*>", "HashMap<i32, String>"),
        (r"\bunordered_set<\s*int\s*>", "HashSet<i32>"),
        (r"\bunordered_set<\s*long\s*>", "HashSet<i64>"),
        (r"\bunordered_set<\s*string\s*>", "HashSet<String>"),
        (r"\bunordered_set<\s*char\s*>", "HashSet<char>"),
        (r"\bmap<\s*int\s*,\s*int\s*>", "BTreeMap<i32, i32>"),
        (r"\bset<\s*int\s*>", "BTreeSet<i32>"),
        (r"\bset<\s*string\s*>", "BTreeSet<String>"),
        (r"\bmultiset<\s*int\s*>", "BTreeMap<i32, i32>"),
        (r"\bqueue<\s*pair<\s*int\s*,\s*int\s*>\s*>", "VecDeque<(i32, i32)>"),
        (r"\bqueue<\s*int\s*>", "VecDeque<i32>"),
        (r"\bqueue<\s*TreeNode\s*\*\s*>", "VecDeque<Option<Rc<RefCell<TreeNode>>>>"),
        (r"\bqueue<\s*ListNode\s*\*\s*>", "VecDeque<Option<Box<ListNode>>>"),
        (r"\bstack<\s*int\s*>", "Vec<i32>"),
        (r"\bstack<\s*char\s*>", "Vec<char>"),
        (r"\bstack<\s*TreeNode\s*\*\s*>", "Vec<Option<Rc<RefCell<TreeNode>>>>"),
        (r"\bdeque<\s*int\s*>", "VecDeque<i32>"),
        (r"\bdeque<\s*pair<\s*int\s*,\s*int\s*>\s*>", "VecDeque<(i32, i32)>"),
        (
            r"\bpriority_queue<\s*pair<\s*int\s*,\s*int\s*>\s*,\s*vector<\s*pair<\s*int\s*,\s*int\s*>\s*>\s*,\s*greater<>\s*>",
            "BinaryHeap<Reverse<(i32, i32)>>",
        ),
        (
            r"\bpriority_queue<\s*int\s*,\s*vector<\s*int\s*>\s*,\s*greater<\s*(?:int)?\s*>\s*>",
            "BinaryHeap<Reverse<i32>>",
        ),
        (r"\bpriority_queue<\s*int\s*>", "BinaryHeap<i32>"),
        (r"\bpair<\s*int\s*,\s*int\s*>", "(i32, i32)"),
        (r"\blist<\s*int\s*>", "VecDeque<i32>"),
        (r"\boptional<\s*int\s*>", "Option<i32>"),
    ]
    for pat, repl in nested_type_order:
        result = re.sub(pat, repl, result)

    result = re.sub(r"\bvector<\s*(\w+)\s*>", r"Vec<\1>", result)
    result = re.sub(r"\bunordered_map<\s*(\w+)\s*,\s*(\w+)\s*>", r"HashMap<\1, \2>", result)
    result = re.sub(r"\bunordered_set<\s*(\w+)\s*>", r"HashSet<\1>", result)
    result = re.sub(r"\bmap<\s*(\w+)\s*,\s*(\w+)\s*>", r"BTreeMap<\1, \2>", result)
    result = re.sub(r"\bset<\s*(\w+)\s*>", r"BTreeSet<\1>", result)
    result = re.sub(r"\bqueue<\s*(\w+)\s*>", r"VecDeque<\1>", result)
    result = re.sub(r"\bstack<\s*(\w+)\s*>", r"Vec<\1>", result)
    result = re.sub(r"\bdeque<\s*(\w+)\s*>", r"VecDeque<\1>", result)
    result = re.sub(r"\bpriority_queue<\s*(\w+)\s*>", r"BinaryHeap<\1>", result)
    result = re.sub(r"\bpair<\s*(\w+)\s*,\s*(\w+)\s*>", r"(\1, \2)", result)

    result = re.sub(r"\blong\s+long\b", "i64", result)
    result = re.sub(r"\bunsigned\s+long\s+long\b", "u64", result)
    result = re.sub(r"\bunsigned\s+int\b", "u32", result)
    result = re.sub(r"\bunsigned\s+char\b", "u8", result)
    result = re.sub(r"\bsize_t\b", "usize", result)
    result = re.sub(r"\bint64_t\b", "i64", result)
    result = re.sub(r"\buint64_t\b", "u64", result)
    result = re.sub(r"\bint32_t\b", "i32", result)
    result = re.sub(r"\bstring_view\b", "&str", result)
    result = re.sub(r"\bstring\b", "String", result)
    result = re.sub(r"\bnullptr\b", "None", result)
    result = re.sub(r"\bNULL\b", "None", result)
    result = re.sub(r"\bINT_MAX\b", "i32::MAX", result)
    result = re.sub(r"\bINT_MIN\b", "i32::MIN", result)
    result = re.sub(r"\bLLONG_MAX\b", "i64::MAX", result)
    result = re.sub(r"\bLLONG_MIN\b", "i64::MIN", result)
    result = re.sub(r"numeric_limits<\s*int\s*>::max\s*\(\s*\)", "i32::MAX", result)
    result = re.sub(r"numeric_limits<\s*int\s*>::min\s*\(\s*\)", "i32::MIN", result)
    result = re.sub(r"numeric_limits<\s*i64\s*>::max\s*\(\s*\)", "i64::MAX", result)
    result = re.sub(r"__builtin_popcountll\s*\(", "(", result)  # placeholder, fixed below
    result = re.sub(r"__builtin_popcount\s*\(([^)]+)\)", r"(\1).count_ones()", result)
    result = re.sub(r"__builtin_clz\s*\(([^)]+)\)", r"(\1).leading_zeros()", result)
    result = re.sub(r"__builtin_ctz\s*\(([^)]+)\)", r"(\1).trailing_zeros()", result)

    # Pointer types
    result = re.sub(r"\bListNode\s*\*\s*", "Option<Box<ListNode>> ", result)
    result = re.sub(r"\bTreeNode\s*\*\s*", "Option<Rc<RefCell<TreeNode>>> ", result)
    result = re.sub(r"\bNode\s*\*\s*", "Option<Rc<RefCell<Node>>> ", result)

    result = re.sub(r"\bconst\s+", "", result)
    result = re.sub(r"(\w)\s*&\s+(\w)", r"\1 \2", result)
    result = re.sub(r"(\w)\s*&\s*\)", r"\1)", result)
    result = re.sub(r"(\w)\s*&\s*,", r"\1,", result)

    # class Solution { ... } → impl Solution
    result = re.sub(r"\bclass\s+Solution\s*\{", "impl Solution {", result)

    # Other classes → struct + impl (best-effort: keep as impl Block)
    def class_to_impl(m: re.Match) -> str:
        name = m.group(1)
        return f"impl {name} {{"

    result = re.sub(r"\bclass\s+(\w+)\s*\{", class_to_impl, result)
    result = re.sub(r"\bstruct\s+(\w+)\s*\{", r"struct \1 {", result)

    # Constructors: Foo(int x) { → pub fn new(x: i32) -> Self {
    def convert_ctor(m: re.Match) -> str:
        name, params = m.group(1), m.group(2)
        rust_params = []
        for p in split_params(params):
            converted = convert_param(p)
            if converted:
                rust_params.append(converted)
        return f"pub fn new({', '.join(rust_params)}) -> Self {{"

    result = re.sub(
        r"^(\s+)(\w+)\s*\(([^)]*)\)\s*\{",
        lambda m: (
            m.group(1) + convert_ctor(type("M", (), {"group": lambda self, i: m.group(i + 1) if i else m.group(0)})())
            if False
            else (
                m.group(1) + f"pub fn new({', '.join(filter(None, (convert_param(p) for p in split_params(m.group(3)))))}) -> Self {{"
                if m.group(2)[:1].isupper() and m.group(2) not in {"Vec", "String", "Option", "HashMap", "HashSet", "VecDeque", "BinaryHeap", "BTreeMap", "BTreeSet", "ListNode", "TreeNode", "Solution"}
                else m.group(0)
            )
        ),
        result,
        flags=re.M,
    )

    # Method signatures
    method_re = re.compile(
        r"^(\s+)(?:static\s+)?(void|bool|int|i32|i64|long|double|float|char|String|&str|usize|u32|u64|f64|"
        r"Vec(?:<[^;{]+>)?|HashMap(?:<[^;{]+>)?|HashSet(?:<[^;{]+>)?|Option(?:<[^;{]+>)?|"
        r"VecDeque(?:<[^;{]+>)?|BinaryHeap(?:<[^;{]+>)?|BTreeMap(?:<[^;{]+>)?|BTreeSet(?:<[^;{]+>)?|"
        r"ListNode|TreeNode|Node)\s+(\w+)\s*\(([^)]*)\)\s*(?:const\s*)?\{",
        re.M,
    )

    def repl_method(m: re.Match) -> str:
        indent, ret, name, params = m.group(1), m.group(2), m.group(3), m.group(4)
        if name in {"if", "for", "while", "switch", "new"}:
            return m.group(0)
        mutating = ret == "void" and "&" in m.group(0)
        rust_ret = convert_cpp_type(ret)
        # ret may already be converted
        if ret.startswith("Vec") or ret.startswith("Hash") or ret.startswith("Option") or ret.startswith("BTree") or ret.startswith("VecDeque") or ret.startswith("Binary"):
            rust_ret = ret
        elif ret == "int":
            rust_ret = "i32"
        elif ret == "long":
            rust_ret = "i64"
        elif ret == "void":
            rust_ret = "()"
        elif ret == "String":
            rust_ret = "String"
        elif ret == "ListNode":
            rust_ret = "Option<Box<ListNode>>"
        elif ret == "TreeNode":
            rust_ret = "Option<Rc<RefCell<TreeNode>>>"
        rust_name = method_to_snake(name)
        rust_params = []
        for p in split_params(params):
            converted = convert_param(p, mutating=mutating)
            if converted:
                rust_params.append(converted)
        param_str = ", ".join(rust_params)
        if rust_ret == "()":
            return f"{indent}pub fn {rust_name}({param_str}) {{"
        return f"{indent}pub fn {rust_name}({param_str}) -> {rust_ret} {{"

    result = method_re.sub(repl_method, result)

    # Standalone functions (templates)
    result = re.sub(
        r"^(\s*)(?:static\s+)?(void|bool|int|i32|i64|long|double|String)\s+(\w+)\s*\(([^)]*)\)\s*\{",
        lambda m: (
            m.group(1)
            + (
                f"fn {method_to_snake(m.group(3))}({', '.join(filter(None, (convert_param(p) for p in split_params(m.group(4)))))})"
                + ("" if m.group(2) == "void" else f" -> {convert_cpp_type(m.group(2))}")
                + " {"
            )
        ),
        result,
        flags=re.M,
    )

    result = convert_for_loops(result)
    result = convert_declarations(result)
    result = convert_if_while(result)

    # Container methods
    result = re.sub(r"\.push_back\s*\(", ".push(", result)
    result = re.sub(r"\.emplace_back\s*\(", ".push(", result)
    result = re.sub(r"\.pop_back\s*\(\s*\)", ".pop()", result)
    result = re.sub(r"\.pop_front\s*\(\s*\)", ".pop_front()", result)
    result = re.sub(r"\.push_front\s*\(", ".push_front(", result)
    result = re.sub(r"\.empty\s*\(\s*\)", ".is_empty()", result)
    result = re.sub(r"\.size\s*\(\s*\)", ".len()", result)
    result = re.sub(r"\.length\s*\(\s*\)", ".len()", result)
    result = re.sub(r"\.front\s*\(\s*\)", ".front().copied().unwrap()", result)
    result = re.sub(r"\.back\s*\(\s*\)", ".last().copied().unwrap()", result)
    result = re.sub(r"\.top\s*\(\s*\)", ".last().copied().unwrap()", result)  # stack as Vec
    result = re.sub(r"\.count\s*\(([^)]+)\)", r".contains_key(&\1) as i32", result)
    result = re.sub(r"\.find\s*\(([^)]+)\)", r".get(&\1)", result)
    result = re.sub(r"\.insert\s*\(", ".insert(", result)
    result = re.sub(r"\.erase\s*\(", ".remove(", result)
    result = re.sub(r"\.clear\s*\(\s*\)", ".clear()", result)
    result = re.sub(r"\.substr\s*\(([^,]+),\s*([^)]+)\)", r"[\1..(\1+\2)].to_string()", result)
    result = re.sub(r"\.substr\s*\(([^)]+)\)", r"[\1..].to_string()", result)
    result = re.sub(r"\.pop\s*\(\s*\)", ".pop()", result)

    # Algorithms
    result = re.sub(
        r"sort\s*\(\s*(\w+)\.begin\(\)\s*,\s*\1\.end\(\)\s*,\s*greater<>\(\)\s*\)",
        r"\1.sort_by(|a, b| b.cmp(a))",
        result,
    )
    result = re.sub(
        r"sort\s*\(\s*(\w+)\.begin\(\)\s*,\s*\1\.end\(\)\s*\)",
        r"\1.sort()",
        result,
    )
    result = re.sub(
        r"reverse\s*\(\s*(\w+)\.begin\(\)\s*,\s*\1\.end\(\)\s*\)",
        r"\1.reverse()",
        result,
    )
    result = re.sub(
        r"lower_bound\s*\(\s*(\w+)\.begin\(\)\s*,\s*\1\.end\(\)\s*,\s*([^)]+)\)\s*-\s*\1\.begin\(\)",
        r"\1.partition_point(|&x| x < \2)",
        result,
    )
    result = re.sub(
        r"upper_bound\s*\(\s*(\w+)\.begin\(\)\s*,\s*\1\.end\(\)\s*,\s*([^)]+)\)\s*-\s*\1\.begin\(\)",
        r"\1.partition_point(|&x| x <= \2)",
        result,
    )
    result = re.sub(
        r"binary_search\s*\(\s*(\w+)\.begin\(\)\s*,\s*\1\.end\(\)\s*,\s*([^)]+)\)",
        r"\1.binary_search(&\2).is_ok()",
        result,
    )
    result = re.sub(
        r"accumulate\s*\(\s*(\w+)\.begin\(\)\s*,\s*\1\.end\(\)\s*,\s*([^)]+)\)",
        r"\1.iter().sum::<i32>()",
        result,
    )
    result = re.sub(
        r"max_element\s*\(\s*(\w+)\.begin\(\)\s*,\s*\1\.end\(\)\s*\)",
        r"\1.iter().max()",
        result,
    )
    result = re.sub(
        r"min_element\s*\(\s*(\w+)\.begin\(\)\s*,\s*\1\.end\(\)\s*\)",
        r"\1.iter().min()",
        result,
    )
    result = re.sub(r"\bmake_pair\s*\(([^,]+),\s*([^)]+)\)", r"(\1, \2)", result)
    result = re.sub(r"\bto_string\s*\(([^)]+)\)", r"\1.to_string()", result)
    result = re.sub(r"\bstoi\s*\(([^)]+)\)", r"\1.parse::<i32>().unwrap()", result)
    result = re.sub(r"\bstoll\s*\(([^)]+)\)", r"\1.parse::<i64>().unwrap()", result)
    result = re.sub(r"\babs\s*\(([^)]+)\)", r"(\1).abs()", result)
    result = re.sub(r"(?<![\w.])max\s*\(([^,]+),\s*([^)]+)\)", r"\1.max(\2)", result)
    result = re.sub(r"(?<![\w.])min\s*\(([^,]+),\s*([^)]+)\)", r"\1.min(\2)", result)
    result = re.sub(r"\bswap\s*\(([^,]+),\s*([^)]+)\)", r"std::mem::swap(&mut \1, &mut \2)", result)
    result = re.sub(r"\bgcd\s*\(([^,]+),\s*([^)]+)\)", r"\1.gcd(\2)", result)
    result = re.sub(r"\bpow\s*\(([^,]+),\s*([^)]+)\)", r"\1.pow(\2 as u32)", result)
    result = re.sub(r"\bsqrt\s*\(([^)]+)\)", r"(\1 as f64).sqrt()", result)
    result = re.sub(r"\bfloor\s*\(([^)]+)\)", r"(\1).floor()", result)
    result = re.sub(r"\bceil\s*\(([^)]+)\)", r"(\1).ceil()", result)
    result = re.sub(r"\bnext_permutation\s*\(\s*(\w+)\.begin\(\)\s*,\s*\1\.end\(\)\s*\)", r"/* next_permutation(\1) */ true", result)

    # Hash map increment
    result = re.sub(
        r"(\w+)\[(\w+)\]\+\+\s*;",
        r"*\1.entry(\2).or_insert(0) += 1;",
        result,
    )
    result = re.sub(
        r"\+\+(\w+)\[(\w+)\]\s*;",
        r"*\1.entry(\2).or_insert(0) += 1;",
        result,
    )

    # Member access
    result = re.sub(r"(\w+)\s*->\s*(\w+)", r"\1.\2", result)

    # Casts
    result = re.sub(r"\(int\)\s*", "", result)
    result = re.sub(r"\(i32\)\s*", "", result)
    result = re.sub(r"\(long\)\s*", "", result)
    result = re.sub(r"\(i64\)\s*", "", result)
    result = re.sub(r"static_cast<\s*int\s*>\s*\(([^)]+)\)", r"(\1 as i32)", result)
    result = re.sub(r"static_cast<\s*i64\s*>\s*\(([^)]+)\)", r"(\1 as i64)", result)
    result = re.sub(r"static_cast<\s*double\s*>\s*\(([^)]+)\)", r"(\1 as f64)", result)
    result = re.sub(r"static_cast<\s*usize\s*>\s*\(([^)]+)\)", r"(\1 as usize)", result)

    # Statement-level increments first
    result = re.sub(r"^(\s*)\+\+(\w+)\s*;", r"\1\2 += 1;", result, flags=re.M)
    result = re.sub(r"^(\s*)(\w+)\+\+\s*;", r"\1\2 += 1;", result, flags=re.M)
    result = re.sub(r"^(\s*)--(\w+)\s*;", r"\1\2 -= 1;", result, flags=re.M)
    result = re.sub(r"^(\s*)(\w+)--\s*;", r"\1\2 -= 1;", result, flags=re.M)
    # Remaining expression increments
    result = re.sub(r"\+\+(\w+)", r"{ \1 += 1; \1 }", result)
    result = re.sub(r"(\w+)\+\+", r"{ let t = \1; \1 += 1; t }", result)
    result = re.sub(r"--(\w+)", r"{ \1 -= 1; \1 }", result)
    result = re.sub(r"(\w+)--", r"{ let t = \1; \1 -= 1; t }", result)

    # Ternary
    result = re.sub(
        r"(\b[\w.\(\)\[\]]+)\s*\?\s*([^:]+?)\s*:\s*([^;,\n]+)",
        r"if \1 { \2 } else { \3 }",
        result,
    )

    # nullptr comparisons already None
    result = re.sub(r"(\w+)\s*==\s*None", r"\1.is_none()", result)
    result = re.sub(r"(\w+)\s*!=\s*None", r"\1.is_some()", result)
    result = re.sub(r"!\s*(\w+)\.is_none\(\)", r"\1.is_some()", result)

    # this->
    result = re.sub(r"\bthis\.", "self.", result)
    result = re.sub(r"\bthis\b", "self", result)

    # Trailing class semicolon
    result = re.sub(r"\};\s*$", "}", result, flags=re.M)
    result = re.sub(r"\};\s*\n", "}\n", result)

    # int leftover in types
    result = re.sub(r"\bint\b", "i32", result)
    result = re.sub(r"\blong\b", "i64", result)
    result = re.sub(r"\bdouble\b", "f64", result)
    result = re.sub(r"\bfloat\b", "f32", result)
    result = re.sub(r"\bauto\s+", "let mut ", result)

    # .begin() leftovers
    result = re.sub(r"\.begin\(\)", ".iter()", result)
    result = re.sub(r"\.end\(\)", "/* end */", result)
    result = re.sub(r"\.rbegin\(\)", ".iter().rev()", result)
    result = re.sub(r"\.rend\(\)", "/* rend */", result)

    # new Foo → Foo::new / Box::new
    result = re.sub(r"\bnew\s+ListNode\s*\(([^)]*)\)", r"Some(Box::new(ListNode::new(\1)))", result)
    result = re.sub(r"\bnew\s+TreeNode\s*\(([^)]*)\)", r"Some(Rc::new(RefCell::new(TreeNode::new(\1))))", result)
    result = re.sub(r"\bnew\s+(\w+)\s*\(([^)]*)\)", r"\1::new(\2)", result)

    # delete
    result = re.sub(r"^\s*delete\s+[^;]+;\s*\n", "", result, flags=re.M)

    # true/false already valid

    # else without extra brace issues: "} else {" is fine in Rust; "else {" after if
    result = re.sub(r"^(\s+)\} else if", r"\1} else if", result, flags=re.M)

    # Index as i32 vs usize: nums[i] often needs `i as usize` — add a comment-free cast for common names
    result = re.sub(r"(\w+)\[(\w+)\]", r"\1[\2 as usize]", result)
    # Don't cast usize literals / already-cast
    result = re.sub(r" as usize as usize", " as usize", result)
    result = re.sub(r"\[(\d+) as usize\]", r"[\1]", result)

    # HashMap[k as usize] is wrong — revert map-style if we can detect .entry nearby later
    # Revert `mp[key as usize] =` back to insert for identifiers that look like maps
    result = re.sub(
        r"\b(mp|map|um|freq|cnt|count|seen|idx|index|memo|dp_map|dict|hash)\[([^\]]+) as usize\]\s*=\s*([^;]+);",
        r"\1.insert(\2, \3);",
        result,
    )

    # comments: // stay

    result = inject_uses(result)
    result = cleanup_rust(result)
    return result.strip() + "\n"


def inject_uses(code: str) -> str:
    uses = []
    if re.search(r"\bHashMap\b", code):
        uses.append("use std::collections::HashMap;")
    if re.search(r"\bHashSet\b", code):
        uses.append("use std::collections::HashSet;")
    if re.search(r"\bVecDeque\b", code):
        uses.append("use std::collections::VecDeque;")
    if re.search(r"\bBinaryHeap\b", code):
        uses.append("use std::collections::BinaryHeap;")
    if re.search(r"\bBTreeMap\b", code):
        uses.append("use std::collections::BTreeMap;")
    if re.search(r"\bBTreeSet\b", code):
        uses.append("use std::collections::BTreeSet;")
    if re.search(r"\bReverse\b", code):
        uses.append("use std::cmp::Reverse;")
    if re.search(r"\bRc\b", code):
        uses.append("use std::rc::Rc;")
    if re.search(r"\bRefCell\b", code):
        uses.append("use std::cell::RefCell;")
    if not uses:
        return code
    header = "\n".join(dict.fromkeys(uses))
    return header + "\n\n" + code


def cleanup_rust(code: str) -> str:
    result = code
    result = re.sub(r"\bVec<i32>::default\(\)", "0", result)
    result = re.sub(r"let mut (\w+) = Vec<([^>]+>::new\(\);)", r"let mut \1 = Vec::new();", result)
    result = re.sub(
        r"let mut (\w+) = (Vec<[^>]+>|HashMap<[^>]+>|HashSet<[^>]+>|VecDeque<[^>]+>|BinaryHeap<[^>]+>|BTreeMap<[^>]+>|BTreeSet<[^>]+>)::new\(\);",
        lambda m: f"let mut {m.group(1)} = {m.group(2).split('<')[0]}::new();",
        result,
    )
    # Fix doubled else braces
    result = re.sub(r"\}\s*else if", "} else if", result)
    result = re.sub(r"\bvoid\b", "()", result)
    result = re.sub(r"::new\(\);", "::new();", result)
    # leftover C++ refs
    result = re.sub(r"\bendl\b", "", result)
    result = re.sub(r"\bcout\s*<<", "print!(", result)
    result = re.sub(r"Option<Box<ListNode>> (\w+) = None;", r"let mut \1 = None;", result)
    result = re.sub(r"Option<Rc<RefCell<TreeNode>>> (\w+) = None;", r"let mut \1 = None;", result)
    result = re.sub(r"Option<Box<ListNode>> (\w+) = ", r"let mut \1 = ", result)
    result = re.sub(r"Option<Rc<RefCell<TreeNode>>> (\w+) = ", r"let mut \1 = ", result)
    # `if !head` pointer checks
    result = re.sub(r"if !(\w+) \{", r"if \1.is_none() {", result)
    result = re.sub(r"while (\w+) \{\s*$", r"while \1.is_some() {", result, flags=re.M)
    # return {};
    result = re.sub(r"return \{\};", "return vec![];", result)
    result = re.sub(r"return \{([^}]+)\};", r"return vec![\1];", result)
    # .contains() C++20 map
    result = re.sub(r"\.contains\s*\(([^)]+)\)", r".contains_key(&\1)", result)
    # Fix impl Solution extra semicolon already handled
    result = re.sub(r"\n{3,}", "\n\n", result)
    return result


def wrap_raw_if_needed(block: str) -> str:
    inner = block
    if "{{" in inner or "{%" in inner:
        return "{% raw %}\n" + inner + "{% endraw %}\n"
    return inner


def convert_prose(text: str) -> str:
    """Rewrite C++-centric prose/links for the Rust blog."""
    # Paths first
    text = text.replace("https://robinali34.github.io/blog_leetcode/", "https://robinali34.github.io/blog_leetcode_rust/")
    text = text.replace("/blog_leetcode/", "/blog_leetcode_rust/")
    text = text.replace("blog_leetcode/", "blog_leetcode_rust/")

    # File / page names
    text = text.replace("cpp-guide", "rust-guide")
    text = text.replace("cpp-cheatsheet", "rust-cheatsheet")
    text = text.replace("C++ Guide", "Rust Guide")
    text = text.replace("C++ STL", "Rust std")
    text = text.replace("C++20 Optimized", "Rust Optimized")
    text = text.replace("C++20 Version", "Rust Version")
    text = text.replace("Optimized C++20", "Idiomatic Rust")
    text = text.replace("Modern C++20", "Modern Rust")
    text = text.replace("Modern C++", "Modern Rust")
    text = text.replace("modern C++", "modern Rust")
    text = text.replace("C++23", "Rust 2024")
    text = text.replace("C++20", "Rust")
    text = text.replace("C++17", "Rust")
    text = text.replace("C++14", "Rust")
    text = text.replace("C++11", "Rust")
    text = text.replace("```cpp", "```rust")
    text = text.replace("```c++", "```rust")

    # Language mentions — avoid breaking "C++" inside already-converted rust? do last
    text = re.sub(r"\bC\+\+\b", "Rust", text)
    text = re.sub(r"\bcpp\b", "rust", text)
    text = re.sub(r"\bSTL\b", "std", text)
    text = text.replace("std::", "")  # leftover prose

    # Common API names in prose
    text = text.replace("`unordered_map`", "`HashMap`")
    text = text.replace("`unordered_set`", "`HashSet`")
    text = text.replace("`priority_queue`", "`BinaryHeap`")
    text = text.replace("`vector`", "`Vec`")
    text = text.replace("`std::vector`", "`Vec`")
    text = text.replace("`push_back`", "`push`")
    text = text.replace("`pop_back`", "`pop`")
    text = text.replace("`nullptr`", "`None`")
    text = text.replace("`INT_MAX`", "`i32::MAX`")
    text = text.replace("`INT_MIN`", "`i32::MIN`")
    text = text.replace("`string`", "`String`")
    text = text.replace("`queue`", "`VecDeque`")
    text = text.replace("`stack`", "`Vec` (as stack)")
    text = text.replace("`map`", "`BTreeMap`")
    text = text.replace("`set`", "`BTreeSet`")
    text = text.replace("next_permutation", "next permutation")

    return text


def process_file(path: Path) -> bool:
    original = path.read_text(encoding="utf-8")
    content = original

    def repl_block(m: re.Match) -> str:
        cpp = m.group(4)
        rust = convert_cpp_to_rust(cpp)
        block = f"```rust\n{rust}```"
        return wrap_raw_if_needed(block)

    content = CODE_BLOCK_RE.sub(repl_block, content)
    content = convert_prose(content)

    # Front matter categories: cpp → rust
    content = re.sub(
        r"(categories:\s*\[[^\]]*?\b)cpp(\b)",
        r"\1rust\2",
        content,
    )
    content = re.sub(r"(categories:[^\n]*\s)cpp(\s)", r"\1rust\2", content)
    content = re.sub(r"(tags:\s*\[[^\]]*?\b)cpp(\b)", r"\1rust\2", content)

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
        for name in ("cpp-guide.md", "rust-guide.md", "about.md", "README.md", "leetcode-questions-list.md"):
            p = ROOT / name
            if p.exists():
                targets.append(p)

    converted = 0
    for path in targets:
        if not path.exists():
            print(f"skip missing: {path}")
            continue
        if process_file(path):
            converted += 1
            print(f"converted: {path}")
    print(f"\nUpdated {converted} files")
    remaining = list(ROOT.glob("_posts/*.md")) + [ROOT / "cpp-guide.md", ROOT / "rust-guide.md"]
    leftover = 0
    for p in remaining:
        if p.exists() and re.search(r"```cpp", p.read_text(encoding="utf-8")):
            leftover += 1
            print(f"still has ```cpp: {p.name}")
    print(f"files still containing ```cpp: {leftover}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
