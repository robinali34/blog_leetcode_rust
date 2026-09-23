---
layout: page
title: Rust Guide
permalink: /rust-guide/
---

# Rust Guide: From Basics to LeetCode-Ready

A practical reference for writing LeetCode and interview solutions in Rust. Pick **Rust** in the LeetCode language dropdown when submitting. Submissions are an `impl Solution` block: the judge already provides `struct Solution`, and you fill in the method.

> **New to LeetCode?** Start with the [Beginner's Guide](/blog_leetcode_rust/2026/06/25/leetcode-beginners-guide/) for the platform, difficulty levels, and which problems to solve first.

The language facts below follow the [Rust Book](https://doc.rust-lang.org/book/), [`std::collections`](https://doc.rust-lang.org/std/collections/), and the [Rust 2024 edition](https://doc.rust-lang.org/edition-guide/rust-2024/) (stable since Rust 1.85, February 2025). Let chains need Rust 1.88 or newer and `edition = "2024"`.

<svg viewBox="0 0 740 200" xmlns="http://www.w3.org/2000/svg" style="max-width: 100%; height: auto; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;">
  <defs>
    <marker id="guide-arr" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto">
      <polygon points="0 0, 8 3, 0 6" fill="#8B8680"/>
    </marker>
  </defs>

  <text x="370" y="22" font-size="13" fill="#5A5752" font-weight="700" text-anchor="middle">How This Guide Is Organized</text>

  <rect x="10" y="38" width="120" height="52" rx="8" fill="#E8D5D0" stroke="#C08070" stroke-width="1.8"/>
  <text x="70" y="60" font-size="11" fill="#5A5752" font-weight="700" text-anchor="middle">Part 1</text>
  <text x="70" y="78" font-size="9" fill="#7A7772" text-anchor="middle">Language Basics</text>

  <rect x="145" y="38" width="120" height="52" rx="8" fill="#D4D8D0" stroke="#6B8B6B" stroke-width="1.8"/>
  <text x="205" y="60" font-size="11" fill="#5A5752" font-weight="700" text-anchor="middle">Part 2</text>
  <text x="205" y="78" font-size="9" fill="#7A7772" text-anchor="middle">std Collections</text>

  <rect x="280" y="38" width="120" height="52" rx="8" fill="#D4D8E0" stroke="#7080A0" stroke-width="1.8"/>
  <text x="340" y="60" font-size="11" fill="#5A5752" font-weight="700" text-anchor="middle">Part 3</text>
  <text x="340" y="78" font-size="9" fill="#7A7772" text-anchor="middle">Patterns</text>

  <rect x="415" y="38" width="120" height="52" rx="8" fill="#E8E3D8" stroke="#B8A880" stroke-width="1.8"/>
  <text x="475" y="60" font-size="11" fill="#5A5752" font-weight="700" text-anchor="middle">Part 4</text>
  <text x="475" y="78" font-size="9" fill="#7A7772" text-anchor="middle">Solution Template</text>

  <line x1="130" y1="64" x2="143" y2="64" stroke="#8B8680" stroke-width="1.5" marker-end="url(#guide-arr)"/>
  <line x1="265" y1="64" x2="278" y2="64" stroke="#8B8680" stroke-width="1.5" marker-end="url(#guide-arr)"/>
  <line x1="400" y1="64" x2="413" y2="64" stroke="#8B8680" stroke-width="1.5" marker-end="url(#guide-arr)"/>

  <rect x="145" y="115" width="150" height="52" rx="8" fill="#E8D5D0" stroke="#C08070" stroke-width="1.8"/>
  <text x="220" y="137" font-size="11" fill="#5A5752" font-weight="700" text-anchor="middle">Part 5</text>
  <text x="220" y="155" font-size="9" fill="#7A7772" text-anchor="middle">Learning Path</text>

  <rect x="320" y="115" width="150" height="52" rx="8" fill="#D4D8D0" stroke="#6B8B6B" stroke-width="1.8"/>
  <text x="395" y="137" font-size="11" fill="#5A5752" font-weight="700" text-anchor="middle">Part 6</text>
  <text x="395" y="155" font-size="9" fill="#7A7772" text-anchor="middle">Modern Rust</text>

  <rect x="495" y="115" width="150" height="52" rx="8" fill="#D4D8E0" stroke="#7080A0" stroke-width="1.8"/>
  <text x="570" y="137" font-size="11" fill="#5A5752" font-weight="700" text-anchor="middle">Quick Ref</text>
  <text x="570" y="155" font-size="9" fill="#7A7772" text-anchor="middle">Cheat Sheet</text>

  <line x1="205" y1="90" x2="220" y2="113" stroke="#8B8680" stroke-width="1.2" stroke-dasharray="4"/>
  <line x1="340" y1="90" x2="395" y2="113" stroke="#8B8680" stroke-width="1.2" stroke-dasharray="4"/>
  <line x1="475" y1="90" x2="570" y2="113" stroke="#8B8680" stroke-width="1.2" stroke-dasharray="4"/>

  <text x="370" y="192" font-size="10" fill="#9A9792" text-anchor="middle">Top row: learn in order. Bottom row: reference anytime.</text>
</svg>

---

## Why Rust for Algorithms

<svg viewBox="0 0 740 180" xmlns="http://www.w3.org/2000/svg" style="max-width: 100%; height: auto; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;">
  <rect x="275" y="10" width="190" height="44" rx="22" fill="#D4D8E0" stroke="#7080A0" stroke-width="2"/>
  <text x="370" y="37" font-size="14" fill="#3A3530" font-weight="700" text-anchor="middle">Rust for Algorithms</text>

  <line x1="275" y1="32" x2="145" y2="80" stroke="#B8B5B0" stroke-width="1.5"/>
  <line x1="325" y1="54" x2="295" y2="80" stroke="#B8B5B0" stroke-width="1.5"/>
  <line x1="415" y1="54" x2="445" y2="80" stroke="#B8B5B0" stroke-width="1.5"/>
  <line x1="465" y1="32" x2="595" y2="80" stroke="#B8B5B0" stroke-width="1.5"/>

  <rect x="40" y="78" width="150" height="40" rx="8" fill="#E8D5D0" stroke="#B8B5B0" stroke-width="1.2"/>
  <text x="115" y="97" font-size="11" fill="#5A5752" font-weight="700" text-anchor="middle">Native Speed</text>
  <text x="115" y="112" font-size="9" fill="#9A9792" text-anchor="middle">no garbage collector</text>

  <rect x="220" y="78" width="150" height="40" rx="8" fill="#D4D8D0" stroke="#B8B5B0" stroke-width="1.2"/>
  <text x="295" y="97" font-size="11" fill="#5A5752" font-weight="700" text-anchor="middle">std Collections</text>
  <text x="295" y="112" font-size="9" fill="#9A9792" text-anchor="middle">Vec, HashMap, heaps</text>

  <rect x="400" y="78" width="150" height="40" rx="8" fill="#D4D8E0" stroke="#B8B5B0" stroke-width="1.2"/>
  <text x="475" y="97" font-size="11" fill="#5A5752" font-weight="700" text-anchor="middle">Ownership</text>
  <text x="475" y="112" font-size="9" fill="#9A9792" text-anchor="middle">borrow checker</text>

  <rect x="560" y="78" width="150" height="40" rx="8" fill="#E8E3D8" stroke="#B8B5B0" stroke-width="1.2"/>
  <text x="635" y="97" font-size="11" fill="#5A5752" font-weight="700" text-anchor="middle">Iterators</text>
  <text x="635" y="112" font-size="9" fill="#9A9792" text-anchor="middle">zero-cost pipelines</text>

  <rect x="80" y="140" width="580" height="28" rx="14" fill="#FAF8F5" stroke="#D4D1CC" stroke-width="1.2"/>
  <text x="370" y="159" font-size="11" fill="#5A5752" font-weight="600" text-anchor="middle">Safe memory, predictable cost, and a standard library built for this work</text>
</svg>

| Strength | What it means on LeetCode |
|---|---|
| **Ownership** | Each value has one owner. The compiler rejects use-after-move and dangling references before the code runs. |
| **Borrowing** | `&T` and `&mut T` share data without copying it. Large vectors stay in place. |
| **`Vec` and `HashMap`** | The [collections guide](https://doc.rust-lang.org/std/collections/) says these two cover most storage. Sorted maps, deques, and heaps are there when you need them. |
| **Iterators** | `map`, `filter`, `fold`, and `windows` compile down to tight loops. |
| **No hidden GC pause** | `drop` runs when a value goes out of scope, so allocation cost stays visible. |

The cost is the borrow checker. Most early compile errors are about who owns a value and who is allowed to mutate it. Parts 1 and 5 are built around that.

---

## Part 1: Language Essentials

### Hello World and the Compiler

```rust
fn main() {
    println!("Hello, World!");
}
```

Run a single file with `rustc`, or a Cargo project when you want tests:

```bash
rustc solution.rs -o solution && ./solution
cargo new practice --bin
cargo run
cargo test
```

| Command | Purpose |
|---|---|
| `rustc solution.rs` | Compile one file. LeetCode compiles your `impl Solution` itself. |
| `cargo run` | Build and run a binary crate |
| `cargo test` | Run `#[test]` functions |
| `rustfmt solution.rs` | Format to the standard style |
| `cargo clippy` | Extra lints |

On your machine, set the edition in `Cargo.toml`:

```toml
[package]
edition = "2024"
```

### Types You Will Actually Use

```rust
let x: i32 = 42;                         // LeetCode's default integer
let y: i64 = 1_000_000_000_000;          // products, prefix sums, MOD math
let n: usize = 10;                       // lengths and indices
let pi: f64 = 3.14159;
let c: char = 'A';                       // one Unicode scalar value
let flag: bool = true;
let s: String = String::from("hello");   // owned, growable, UTF-8
let t: &str = "hello";                   // borrowed string slice
```

| Type | Width | Range you should remember |
|---|---|---|
| `i32` | 32-bit | $-2^{31}$ … $2^{31}-1$ (`i32::MIN` … `i32::MAX`) |
| `i64` | 64-bit | about $\pm 9.2 \times 10^{18}$ |
| `u32` | 32-bit | $0$ … $4\,294\,967\,295$ |
| `usize` | pointer-sized | indices into `Vec` and slices. 64-bit on typical judges. |
| `f64` | 64-bit | binary search on answers, geometry |
| `char` | 4 bytes | one Unicode scalar, so `'é'` is one `char` |
| `String` / `&str` | UTF-8 bytes | `s.len()` is a **byte** count |

**Overflow.** In debug builds, `i32` overflow panics. In release builds it wraps. LeetCode compiles in release mode, so a wrapping product can pass locally in `--release` and still be the wrong answer. Be explicit:

```rust
let area = (width as i64) * (height as i64);
let safe = a.checked_add(b);          // Option<i32>
let wrapped = a.wrapping_add(b);       // two's complement, every build
let clamped = a.saturating_add(b);     // sticks at MIN / MAX
```

`i32::midpoint(a, b)` (stable since 1.87) computes the average rounded toward zero without overflowing. Use it for binary-search midpoints when both ends are signed.

### Control Flow

```rust
if x > 0 {
    // positive
} else if x < 0 {
    // negative
} else {
    // zero
}

for i in 0..n {
    // i is usize: 0, 1, ..., n - 1
}
for i in 0..=n {
    // inclusive end
}

let mut i = 0;
while i < n {
    i += 1;
}

loop {
    if done {
        break;
    }
}
```

`0..n` is exclusive. `0..=n` is inclusive. A reverse loop is `(0..n).rev()`.

`match` is the way to take `Option` and `Result` apart:

```rust
match map.get(&key) {
    Some(value) => *value,
    None => 0,
}
```

`if let` covers the one pattern you care about:

```rust
if let Some(&j) = seen.get(&need) {
    return vec![j, i as i32];
}
```

### Functions, Moves, and Copies

```rust
fn add(a: i32, b: i32) -> i32 {
    a + b // last expression is the return value; no semicolon
}

fn sum_of(nums: &[i32]) -> i32 {
    nums.iter().sum()
}

fn scale(x: &mut i32) {
    *x *= 2;
}
```

Integers, `bool`, `char`, and shared references implement `Copy`: assignment duplicates the bits, and the original stays usable. `String`, `Vec<T>`, and `HashMap<K, V>` do **not**. Assignment moves them:

```rust
let s1 = String::from("hello");
let s2 = s1;          // s1 is moved
// println!("{s1}");  // compile error: s1 was moved
let n1 = 5_i32;
let n2 = n1;          // Copy: n1 is still 5
```

When a non-`Copy` value goes out of scope, Rust calls `drop` and frees its heap buffer. You do not write `free`.

Clone when you truly need a second owned value: `let s3 = s2.clone();`. On a hot LeetCode path, prefer a borrow.

### References and the Borrow Checker

A reference is an address the compiler proves is valid for its whole lifetime.

```rust
fn length(s: &str) -> usize {
    s.len()
}

fn push_bang(s: &mut String) {
    s.push('!');
}

fn main() {
    let mut name = String::from("rust");
    let n = length(&name);   // shared borrow
    push_bang(&mut name);    // exclusive borrow, after n is done
    println!("{n} {name}");
}
```

Rules that show up in every solution:

1. You may have many shared borrows (`&T`), **or** one exclusive borrow (`&mut T`).
2. A borrow must not outlive the value it points at.
3. Holding `&nums[0]` and then calling `nums.push(...)` is rejected: `push` may reallocate and invalidate the reference.

Pass large inputs as slices (`&[i32]`, `&mut [i32]`) in your own helpers. LeetCode signatures usually take ownership (`Vec<i32>`, `String`); move those into the helper or reborrow with `nums.as_slice()` / `&nums`.

### `Option` Instead of Null

Rust has no null. Absence is `Option<T>`: `Some(value)` or `None`.

```rust
let first: Option<&i32> = nums.get(0); // index may be out of range
let value = first.copied().unwrap_or(0);
```

`nums[i]` panics when `i` is out of range. `nums.get(i)` returns `Option<&i32>`. In a solution you have already proved the index, indexing is fine and clearer.

---

## Part 2: `std` Collections

The standard library's own advice: start with `Vec` or `HashMap`. Reach for the others when their extra operation is the one you need. Import them explicitly; only `Vec` is in the prelude.

```rust
use std::collections::{BTreeMap, BTreeSet, BinaryHeap, HashMap, HashSet, VecDeque};
use std::cmp::Reverse;
```

LeetCode accepts the standard library. Third-party crates such as a faster hasher are not available in the submission box.

### Which Collection?

| You need | Use |
|---|---|
| Indexed sequence, stack, sort, binary search | `Vec<T>` |
| Queue or deque (push/pop both ends) | `VecDeque<T>` |
| Expected $O(1)$ lookup by key | `HashMap<K, V>` / `HashSet<T>` |
| Keys in sorted order, successor, or a key range | `BTreeMap<K, V>` / `BTreeSet<T>` |
| Repeated min or max extraction | `BinaryHeap<T>` (max-heap; wrap in `Reverse` for a min-heap) |
| A linked list | Almost never. `Vec` and `VecDeque` are the interview answer. |

### Complexity (from the [`std::collections` performance table](https://doc.rust-lang.org/std/collections/))

| Operation | `Vec` | `VecDeque` | `HashMap` | `BTreeMap` | `BinaryHeap` |
|---|---|---|---|---|---|
| Index / get by key | $O(1)$ | $O(1)$ | $O(1)$ average | $O(\log n)$ | peek $O(1)$ |
| Push back / insert | amortized $O(1)$ | amortized $O(1)$ at ends | $O(1)$ average | $O(\log n)$ | $O(\log n)$ |
| Remove at index / key | $O(n)$ | $O(\min(i, n-i))$ | $O(1)$ average | $O(\log n)$ | pop $O(\log n)$ |
| Sorted range | sort, then slice | — | — | `range` $O(\log n)$ to start | — |

`HashMap` is average-case. The default hasher is SipHash-1-3, chosen to resist hash-flooding attacks. It is correct for interviews. For tiny integer keys it is slower than a raw open-addressed table, and that is the tradeoff you accept inside `std`.

### `Vec` — the Default Sequence

```rust
let mut nums: Vec<i32> = Vec::new();
nums.push(1);
nums.push(2);
let last = nums.pop();             // Option<i32>
let n = nums.len();
let first = nums[0];               // panics if empty

let ready = vec![0; n];            // n zeros
let known = vec![1, 2, 3];
nums.reserve(n);                   // one allocation when you know the size
```

| Method | Effect |
|---|---|
| `push` / `pop` | stack |
| `len` / `is_empty` | size |
| `sort` / `sort_unstable` | ascending. `sort_unstable` is faster when equal elements may reorder |
| `binary_search` | on a sorted vec. `Ok(index)` or `Err(insertion_point)` |
| `windows(k)` | overlapping slices of length `k` |
| `reverse` / `swap(i, j)` | in place |
| `iter` / `iter_mut` / `into_iter` | shared, mutable, or consuming |

```rust
for (i, &x) in nums.iter().enumerate() {
    println!("{i} {x}");
}
for x in &mut nums {
    *x += 1;
}
```

`enumerate` yields `usize`. LeetCode often wants `i as i32` in the returned vector.

### `String` and `&str`

`String` owns its UTF-8 bytes. `&str` borrows them. Indexing with `s[i]` does not compile, because a byte offset is not always a character boundary.

```rust
let mut s = String::from("rust");
s.push('!');
s.push_str("ace");
let bytes = s.len();                 // byte length
let chars = s.chars().count();       // scalar count, O(n)
let b = s.as_bytes();                // &[u8], O(1) random access for ASCII
let head = &s[..4];                  // byte range; must be on a char boundary
assert!(s.starts_with("rust"));
assert!(s.ends_with("ace"));
```

LeetCode strings are usually ASCII, so `s.as_bytes()[i]` is the $O(1)$ read. Use `chars()` when the problem talks about Unicode characters. Build an answer with `String::with_capacity(n)` and `push`.

`split_whitespace`, `split`, and `lines` return iterators of `&str`.

### `HashMap` and `HashSet`

```rust
let mut seen: HashMap<i32, i32> = HashMap::new();
seen.insert(nums[0], 0);
if let Some(&j) = seen.get(&key) {
    // j is the stored index
}
seen.contains_key(&key);
seen.remove(&key);

*seen.entry(key).or_insert(0) += 1;   // frequency count
```

`entry` returns a mutable slot: insert the default when the key is missing, then update it. That is the frequency-map and memoization idiom.

`get` returns `Option<&V>`. `seen[&key]` panics when the key is absent, so keep it for keys you just inserted.

```rust
let mut set = HashSet::new();
set.insert(42);
set.contains(&42);
```

Keys must be `Eq + Hash`. `i32`, `i64`, `String`, `&str`, and tuples of those all qualify. A `Vec<i32>` key works when you own it; a borrowed slice key needs the stored key to match.

Iteration order of a `HashMap` is arbitrary. Sort the keys when the problem wants a stable order.

### `BTreeMap` and `BTreeSet`

Use these when the algorithm needs order: predecessor, successor, or every key inside an interval.

```rust
let mut book: BTreeMap<i32, i32> = BTreeMap::new();
book.insert(10, 1);
book.insert(30, 2);

let floor = book.range(..=15).next_back(); // greatest key <= 15
let ceil = book.range(15..).next();         // least key >= 15
for (&k, &v) in book.range(10..40) {        // 10 <= key < 40
    println!("{k} {v}");
}
```

`BTreeSet<i32>` has the same ordered queries via `range`. First and last keys are `iter().next()` and `iter().next_back()`.

### `BinaryHeap`

`BinaryHeap` is a **max-heap**: `pop` returns the greatest item.

```rust
let mut max_heap: BinaryHeap<i32> = BinaryHeap::new();
max_heap.push(3);
max_heap.push(1);
assert_eq!(max_heap.peek(), Some(&3));
assert_eq!(max_heap.pop(), Some(3));

let mut min_heap: BinaryHeap<Reverse<i32>> = BinaryHeap::new();
min_heap.push(Reverse(3));
min_heap.push(Reverse(1));
assert_eq!(min_heap.pop(), Some(Reverse(1)));
```

`Reverse` comes from `std::cmp`. For a Dijkstra heap of `(dist, node)`, store `Reverse((dist, node))` so the smallest distance comes out first. `dist` should be a type whose order matches what you want; `i64` is the usual choice.

### `VecDeque` — Queues

```rust
let mut q = VecDeque::new();
q.push_back(start);
while let Some(u) = q.pop_front() {
    q.push_back(u + 1);
}
```

`push_back` + `pop_front` is a queue. `push_back` + `pop_back` is a stack; `Vec` is the simpler stack.

---

## Part 3: Patterns You'll Use Every Day

### Sorting

```rust
nums.sort();                                    // ascending, stable
nums.sort_unstable();                           // faster when ties may reorder
nums.sort_by(|a, b| b.cmp(a));                  // descending
nums.sort_by_key(|&x| x.abs());

let mut pairs = vec![(1, 5), (1, 2), (0, 9)];
pairs.sort_by(|a, b| a.0.cmp(&b.0).then(a.1.cmp(&b.1)));
```

`sort_by_key(|&x| -x)` overflows on `i32::MIN`. Prefer `sort_by(|a, b| b.cmp(a))`.

Closures borrow their environment. `|x: &i32| *x + 1` is a closure. Add `move` when it must own captured values: `move |x| owned + x`.

### Binary Search

`binary_search` requires a sorted slice and returns `Result<usize, usize>`.

```rust
match nums.binary_search(&target) {
    Ok(i) => i,          // found
    Err(i) => i,         // first index where target could be inserted
}
```

Lower bound ("first index with value ≥ target") on a sorted slice:

```rust
let i = nums.partition_point(|&x| x < target);
```

Upper bound ("first index with value > target"):

```rust
let i = nums.partition_point(|&x| x <= target);
```

Search on the answer (minimum feasible speed, capacity, day):

```rust
let mut lo: i64 = 1;
let mut hi: i64 = 1_000_000_000;
while lo < hi {
    let mid = lo.midpoint(hi);          // no overflow
    if feasible(mid) {
        hi = mid;
    } else {
        lo = mid + 1;
    }
}
```

### Iterators

```rust
let sum: i32 = nums.iter().sum();
let doubled: Vec<i32> = nums.iter().map(|x| x * 2).collect();
let positives: Vec<i32> = nums.into_iter().filter(|x| *x > 0).collect();
let best = nums.iter().copied().max();                 // Option<i32>
let any = nums.iter().any(|x| *x < 0);
let pos = nums.iter().position(|&x| x == target);      // Option<usize>

let total = nums.iter().fold(0_i64, |acc, &x| acc + x as i64);
```

| Adapter | Yields |
|---|---|
| `iter()` | `&T`, collection stays |
| `iter_mut()` | `&mut T` |
| `into_iter()` | owned `T`, collection is consumed |
| `enumerate` | `(usize, item)` |
| `zip` | pairs until the shorter iterator ends |
| `take(k)` / `skip(k)` | a prefix or the tail |
| `collect` | build a `Vec`, `HashSet`, `String`, … |

`windows` and `chunks` are the slice forms of a sliding window and a blocked scan:

```rust
for w in nums.windows(3) {
    // w: &[i32] of length 3
}
```

### Counting, Prefix Sums, and Differences

```rust
let mut freq: HashMap<i32, i32> = HashMap::new();
for &x in &nums {
    *freq.entry(x).or_insert(0) += 1;
}

let mut prefix = vec![0_i64; nums.len() + 1];
for (i, &x) in nums.iter().enumerate() {
    prefix[i + 1] = prefix[i] + x as i64;
}
let range_sum = prefix[right + 1] - prefix[left];
```

Cast to `i64` before the multiply or the running sum when $n \cdot \max|a_i|$ can exceed $2^{31}-1$.

### Graph Adjacency and DFS

```rust
let mut adj = vec![Vec::<usize>::new(); n];
adj[u].push(v);

fn dfs(u: usize, adj: &[Vec<usize>], seen: &mut [bool]) {
    if seen[u] {
        return;
    }
    seen[u] = true;
    for &v in &adj[u] {
        dfs(v, adj, seen);
    }
}
```

The slice arguments are shared (`adj`) and exclusive (`seen`). That split is what lets the recursive call compile: `seen` is reborrowed for the call and returned when it ends.

BFS uses the `VecDeque` loop from Part 2, with the same `seen` array marked on **push** so a node is enqueued once.

### Two Pointers

```rust
let mut i = 0;
let mut j = nums.len() - 1;
while i < j {
    let sum = nums[i] + nums[j];
    if sum == target {
        break;
    } else if sum < target {
        i += 1;
    } else {
        j -= 1;
    }
}
```

`nums.len() - 1` underflows when the vector is empty. Guard with `if nums.len() < 2`.

---

## Part 4: LeetCode Solution Template

The judge defines `struct Solution`. You submit the `impl` and any helpers. A `main` function is for local runs only.

```rust
use std::collections::HashMap;

impl Solution {
    pub fn two_sum(nums: Vec<i32>, target: i32) -> Vec<i32> {
        let mut seen = HashMap::new();
        for (i, &num) in nums.iter().enumerate() {
            let need = target - num;
            if let Some(&j) = seen.get(&need) {
                return vec![j, i as i32];
            }
            seen.insert(num, i as i32);
        }
        vec![]
    }
}
```

Local harness:

```rust
struct Solution;

fn main() {
    let ans = Solution::two_sum(vec![2, 7, 11, 15], 9);
    assert_eq!(ans, vec![0, 1]);
}
```

### Signature Habits

| LeetCode type | Rust |
|---|---|
| `int` | `i32` |
| `long` | `i64` |
| `int[]` | `Vec<i32>` |
| `string` | `String` on input and output; take `&str` in helpers |
| `ListNode*` | `Option<Box<ListNode>>` |
| `TreeNode*` | `Option<Rc<RefCell<TreeNode>>>` |
| boolean | `bool` |
| index you computed with `enumerate` | `i as i32` |

Linked list and tree stubs from the judge already declare the node types. Use those names; do not invent a second `ListNode`.

```rust
// List helpers, once the judge's ListNode is in scope.
fn push_front(head: Option<Box<ListNode>>, val: i32) -> Option<Box<ListNode>> {
    Some(Box::new(ListNode { val, next: head }))
}
```

Trees share a node across parent links, so the judge uses `Rc<RefCell<TreeNode>>`: `Rc` for shared ownership, `RefCell` for interior mutability checked at runtime.

```rust
use std::cell::RefCell;
use std::rc::Rc;

fn dfs(node: &Option<Rc<RefCell<TreeNode>>>) -> i32 {
    let Some(n) = node else {
        return 0;
    };
    let n = n.borrow();
    n.val + dfs(&n.left) + dfs(&n.right)
}
```

`borrow()` and `borrow_mut()` panic if you already hold the other kind of borrow on that `RefCell`. Finish the borrow (end the scope) before you borrow the same node again.

### Patterns Mapped to Rust

| Pattern | Shape |
|---|---|
| Frequency / index map | `HashMap` + `entry().or_insert` |
| Sliding window | two indices, or `windows(k)` when the width is fixed |
| Monotonic stack | `Vec<i32>` with `push` / `pop` |
| Heap top-k | `BinaryHeap<Reverse<T>>` of size `k` |
| Ordered multiset | `BTreeMap<i32, i32>` of value → count |
| Union-find | `parent: Vec<usize>`, `find` with path compression |
| DP row | `let mut dp = vec![0_i64; n + 1];` |
| Backtracking | recursive `fn` taking `&mut Vec<i32>` and `&mut Vec<Vec<i32>>` |

```rust
fn subsets(start: usize, nums: &[i32], path: &mut Vec<i32>, out: &mut Vec<Vec<i32>>) {
    out.push(path.clone());
    for i in start..nums.len() {
        path.push(nums[i]);
        subsets(i + 1, nums, path, out);
        path.pop();
    }
}
```

---

## Part 5: Learning Path

<svg viewBox="0 0 740 120" xmlns="http://www.w3.org/2000/svg" style="max-width: 100%; height: auto; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;">
  <rect x="16" y="36" width="120" height="48" rx="8" fill="#E8D5D0" stroke="#C08070" stroke-width="1.5"/>
  <text x="76" y="56" font-size="11" fill="#5A5752" font-weight="700" text-anchor="middle">1. Syntax</text>
  <text x="76" y="72" font-size="9" fill="#7A7772" text-anchor="middle">types, match</text>

  <rect x="164" y="36" width="120" height="48" rx="8" fill="#E8D5D0" stroke="#C08070" stroke-width="1.5"/>
  <text x="224" y="56" font-size="11" fill="#5A5752" font-weight="700" text-anchor="middle">2. Ownership</text>
  <text x="224" y="72" font-size="9" fill="#7A7772" text-anchor="middle">&amp; and &amp;mut</text>

  <rect x="312" y="36" width="120" height="48" rx="8" fill="#D4D8D0" stroke="#6B8B6B" stroke-width="1.5"/>
  <text x="372" y="56" font-size="11" fill="#5A5752" font-weight="700" text-anchor="middle">3. Collections</text>
  <text x="372" y="72" font-size="9" fill="#7A7772" text-anchor="middle">Vec, HashMap</text>

  <rect x="460" y="36" width="120" height="48" rx="8" fill="#D4D8E0" stroke="#7080A0" stroke-width="1.5"/>
  <text x="520" y="56" font-size="11" fill="#5A5752" font-weight="700" text-anchor="middle">4. Iterators</text>
  <text x="520" y="72" font-size="9" fill="#7A7772" text-anchor="middle">sort, search</text>

  <rect x="608" y="36" width="116" height="48" rx="8" fill="#E8E3D8" stroke="#B8A880" stroke-width="1.5"/>
  <text x="666" y="56" font-size="11" fill="#5A5752" font-weight="700" text-anchor="middle">5. Patterns</text>
  <text x="666" y="72" font-size="9" fill="#7A7772" text-anchor="middle">graphs, DP</text>
</svg>

### Stage 1 — Syntax (about a week)

Read chapters 1–3 and 6 of [the Book](https://doc.rust-lang.org/book/). Write small `fn main` programs that use `i32`, `i64`, `for`, `while`, and `match`.

Check that you can:

- Explain `0..n` versus `0..=n`
- Return a value without `return` by leaving the semicolon off
- Call `i32::MAX`, `checked_add`, and a cast `as i64`

### Stage 2 — Ownership and Borrowing (one to two weeks)

Read [chapter 4](https://doc.rust-lang.org/book/ch04-01-what-is-ownership.html). This is the stage that makes later solutions compile.

Check that you can:

- Say which of `i32` and `String` is `Copy`
- Write a function that takes `&[i32]` and one that takes `&mut Vec<i32>`
- Read a borrow-checker error and shorten the borrow (end the scope, clone, or index instead of holding a reference)

### Stage 3 — Collections (one to two weeks)

Read [chapter 8](https://doc.rust-lang.org/book/ch08-01-vectors.html). Solve array, string, and hash-map problems: Two Sum, Group Anagrams, Valid Anagram, Contains Duplicate.

Check that you can:

- Build a frequency map with `entry`
- Decide `HashMap` versus `BTreeMap` from the table in Part 2
- Walk a `String` with `as_bytes` for ASCII and `chars` for Unicode

### Stage 4 — Iterators, Sort, and Search (ongoing)

Solve binary search, sliding window, and sorting problems. Keep [iterator docs](https://doc.rust-lang.org/std/iter/trait.Iterator.html) open.

Check that you can:

- Choose `iter`, `iter_mut`, or `into_iter` on purpose
- Write a lower bound with `partition_point`
- Implement a min-heap with `BinaryHeap<Reverse<_>>`

### Stage 5 — Algorithm Templates (ongoing)

Use the [templates index](/blog_leetcode_rust/leetcode-templates/) and implement each pattern once in Rust: BFS, DFS, union-find, prefix sums, monotonic stack, interval sweep, and top-k. The Rust shapes are in Part 4.

---

## Part 6: Modern Rust Worth Knowing

Rust 2024 is the current edition, stabilized in **Rust 1.85.0** (20 February 2025). Editions are opt-in: a 2024 crate still links with older crates. New code should set `edition = "2024"`.

### Let Chains (Rust 1.88, edition 2024)

Stable since 26 June 2025, and only in edition 2024. `if` and `while` conditions can mix `let` patterns and booleans with `&&`. Bindings from an earlier pattern are visible later in the chain.

```rust
let release = Some((1, 88));
if let Some((major, minor)) = release && major == 1 && minor >= 88 {
    println!("let chains are available");
}
```

On edition 2021 the same code is a compile error. Nested `if let` still works everywhere.

### `let` … `else`

```rust
let Some(node) = head else {
    return None;
};
```

When the pattern fails, the `else` block must diverge (`return`, `break`, `continue`, or `panic`).

### Matches That Stay Short

```rust
let digit = matches!(c, '0'..='9');
let value = option.unwrap_or(0);
let value = option.unwrap_or_else(|| expensive());
```

### Overflow-Safe Midpoint

```rust
let mid = lo.midpoint(hi);   // signed: stable since 1.87; unsigned: since 1.85
```

This is `(lo + hi) / 2` rounded toward zero, computed so the addition cannot overflow. Binary search on `i64` bounds should use it.

### What to Leave Alone on LeetCode

- `async`, threads, and channels. Solutions are single-threaded and synchronous.
- `unsafe`. Safe `std` is enough, and `unsafe` drops the guarantees you are practicing.
- Nightly-only syntax (`gen` blocks, the `!` type as a fully stable alias in older toolchains). If it needs `#![feature(...)]`, the judge will reject it.
- External crates. `std` is the whole toolbox inside the editor.

`dbg!(expr)` prints the file, line, and value to stderr and returns the value. Strip those calls before you submit if the problem is strict about stdout.

---

## Quick Reference Card

### Collection Costs

| Operation | `Vec` | `HashMap` | `BTreeMap` | `BinaryHeap` |
|---|---|---|---|---|
| Read | $O(1)$ index | $O(1)$ avg `get` | $O(\log n)$ | $O(1)$ `peek` |
| Insert | amortized $O(1)$ `push` | $O(1)$ avg | $O(\log n)$ | $O(\log n)$ `push` |
| Delete | $O(n)$ in the middle, $O(1)$ `pop` | $O(1)$ avg | $O(\log n)$ | $O(\log n)$ `pop` |
| Order | after `sort` | arbitrary | sorted keys | max (or min via `Reverse`) |

### Integer Limits

| Constant | Value |
|---|---|
| `i32::MIN` / `i32::MAX` | $-2\,147\,483\,648$ / $2\,147\,483\,647$ |
| `i64::MIN` / `i64::MAX` | $-9\,223\,372\,036\,854\,775\,808$ / $9\,223\,372\,036\,854\,775\,807$ |
| `u32::MAX` | $4\,294\,967\,295$ |

```rust
const MOD: i64 = 1_000_000_007;
let sum = (a + b) % MOD;
```

### Snippets

```rust
use std::cmp::Reverse;
use std::collections::{BinaryHeap, HashMap, VecDeque};

let mut freq = HashMap::new();
*freq.entry(x).or_insert(0) += 1;

let mut heap = BinaryHeap::new();
heap.push(Reverse(dist));

let mut q = VecDeque::new();
q.push_back(0);

let i = nums.partition_point(|&x| x < target);
let area = (w as i64) * (h as i64);
```

---

## Resources

- [The Rust Programming Language](https://doc.rust-lang.org/book/) — ownership, `Vec`, `String`, and `HashMap` in the official book
- [`std` documentation](https://doc.rust-lang.org/std/) — method-level reference
- [`std::collections`](https://doc.rust-lang.org/std/collections/) — which collection to pick, plus the complexity table
- [Rust by Example](https://doc.rust-lang.org/rust-by-example/) — short runnable snippets
- [Rust 2024 edition guide](https://doc.rust-lang.org/edition-guide/rust-2024/) — edition changes, including the temporary-scope rules let chains rely on
- [Rust 1.85 announcement](https://blog.rust-lang.org/2025/02/20/Rust-1.85.0/) — Rust 2024 becomes stable
- [Rust 1.88 announcement](https://blog.rust-lang.org/2025/06/26/Rust-1.88.0/) — let chains
- [Rustlings](https://github.com/rust-lang/rustlings) — small exercises for ownership and iterators
- [LeetCode templates on this blog](/blog_leetcode_rust/leetcode-templates/) — algorithm patterns
- [LeetCode Beginner's Guide](/blog_leetcode_rust/2026/06/25/leetcode-beginners-guide/) — the platform itself
