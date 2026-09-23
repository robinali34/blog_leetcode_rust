---
layout: post
title: "Ruby Quick Reference for LeetCode"
date: 2025-09-23 23:33:00 -0000
categories: leetcode algorithm ruby data-structures reference cheat-sheet programming std containers iterators algorithms competitive-programming
permalink: /posts/2025-09-23-rust-cheatsheet/
---

# Ruby Quick Reference for LeetCode

Pick **Ruby** in the LeetCode language dropdown when submitting.

---

## Strings

```ruby
s = "abc"
s.length
s.empty?
s[i]                 # character (or nil)
s[start, len]        # substring
s.index("ab")        # Integer or nil
s << "def"           # append
s.include?("ab")
42.to_s
"42".to_i
```

---

## Arrays

```ruby
v = []
v.push(x)
v << x
v.pop
v[i]
v.first
v.last
v.clear
v.sort!
v.reverse!
v.length
v.empty?
filled = Array.new(n, 0)
```

---

## Hash / Set

```ruby
require 'set'

m = {}
m[key] = val
m[key]               # value or nil
m[key] ||= 0
m[key] += 1
m.key?(key)
m.each { |k, v| }

s = Set.new
s.add(x)
s.include?(x)
```

---

## Stack / Queue

```ruby
stack = []
stack.push(x)
stack.pop
stack.last

q = []
q.push(x)            # enqueue
q.shift              # dequeue
q.first
```

---

## Heap (priority queue)

```ruby
# Max-heap via sort (fine for small n). For true heaps, keep an array
# and re-sort, or use a gem. LeetCode Ruby often sorts.
heap = []
heap << x
heap.sort!
heap.pop             # largest if sorted ascending then pop from end
```

---

## Sorting & searching

```ruby
v.sort!
v.sort!.reverse!
v.bsearch { |x| x >= target }
[a, b].max
[a, b].min
x.abs
v.sum
v.max
```

---

## Bit tricks

```ruby
x.to_s(2).count('1')
x & (x - 1)          # clear lowest set bit
x & -x               # isolate lowest set bit
```

---

## Common LeetCode structures

| Concept   | Ruby equivalent |
|-----------|-----------------|
| Hash map  | `Hash` (`{}`) |
| Hash set  | `Set` |
| Stack     | `Array` (`push` / `pop`) |
| Queue     | `Array` (`push` / `shift`) |
| String    | `String` |
| Graph     | `Array` of arrays |

---

## Two Sum

```ruby
# @param {Integer[]} nums
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
```

---

## LeetCode node types

```ruby
# ListNode
class ListNode
  attr_accessor :val, :next
  def initialize(val = 0, _next = nil)
    @val = val
    @next = _next
  end
end

# TreeNode
class TreeNode
  attr_accessor :val, :left, :right
  def initialize(val = 0, left = nil, right = nil)
    @val = val
    @left = left
    @right = right
  end
end
```
