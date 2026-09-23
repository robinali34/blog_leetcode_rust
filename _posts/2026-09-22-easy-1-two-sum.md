---
layout: post
title: "[Easy] 1. Two Sum"
date: 2026-09-22
categories: [leetcode, easy, array, hash, ruby]
tags: [leetcode, easy, array, hash, two-sum]
permalink: /2026/09/22/easy-1-two-sum/
---
Given an array of integers `nums` and an integer `target`, return *the indices of the two numbers such that they add up to `target`*.

You may assume that each input has **exactly one solution**, and you may not use the same element twice.

You can return the answer in any order.

> **Pattern:** Hash map complementary lookup

## Examples

**Example 1:**

```
Input: nums = [2,7,11,15], target = 9
Output: [0,1]
Explanation: Because nums[0] + nums[1] == 9, we return [0, 1].
```

**Example 2:**

```
Input: nums = [3,2,4], target = 6
Output: [1,2]
```

**Example 3:**

```
Input: nums = [3,3], target = 6
Output: [0,1]
```

## Constraints

- `2 <= nums.length <= 10^4`
- `-10^9 <= nums[i] <= 10^9`
- `-10^9 <= target <= 10^9`
- Only one valid answer exists.

## Common Approaches

| Approach | Time | Space | Notes |
|----------|------|-------|-------|
| **Hash map of index** *(this problem)* | O(n) | O(n) | Store value → index while scanning |
| Two pointers on a sorted copy | O(n log n) | O(n) | Must keep original indices |
| Brute force | O(n²) | O(1) | Check every pair |

## Thinking Process

For each value `x` at index `j`, the complement is `target - x`. If we have already seen that complement, we are done. Otherwise remember `x` at `j`.

- Signal: two numbers that add up to a target on an unsorted array
- Key idea: one pass, hash map of values already seen
- Edge cases: the complement at index `0`; duplicates (`[3,3]`, target `6`); negatives

## Solution — O(n) time, O(n) space

```rust
use std::collections::HashMap;

impl Solution {
    pub fn two_sum(nums: Vec<i32>, target: i32) -> Vec<i32> {
        let mut idx = HashMap::new();
        for(j, &x) in nums.iter().enumerate() {
            if let Some(&i) = idx.get(&(target - x)) {
                return vec![i as i32, j as i32];
            }
            idx.insert(x, j);
        }
        unreachable!()
    }
}
```

### Solution Explanation

Walk `nums` once. `idx` maps a value to the index where we last saw it.

At index `j` with value `x`, look up `target - x`. If that index `i` exists, `[i, j]` is the pair. If not, record `idx[x] = j` and continue.

Check `unless i.nil?` rather than `if i`, because index `0` is falsey in Ruby.

**Walkthrough** — `nums = [2,7,11,15]`, `target = 9`:

| j | x | `target - x` | `idx` before | action |
|---|---|--------------|--------------|--------|
| 0 | 2 | 7 | `{}` | miss, set `idx[2] = 0` |
| 1 | 7 | 2 | `{2=>0}` | hit `i = 0`, return `[0, 1]` |

**Time:** O(n) · **Space:** O(n)

## Common Mistakes

- Recording `idx[x] = j` before the lookup — that matches an element with itself when `2 * x == target`
- Returning values instead of indices
- Using `return [i, j] if i` — fails when the complement lives at index `0`

## Key Takeaways

- Unsorted two-sum is a hash map problem, not two pointers
- Store the complement you still need, keyed by value, with the index as the payload

## Related Problems

- [LC 15: 3Sum](https://www.leetcode.com/problems/3sum/)
- [LC 167: Two Sum II - Input Array Is Sorted](https://www.leetcode.com/problems/two-sum-ii-input-array-is-sorted/)
- [LC 217: Contains Duplicate](https://www.leetcode.com/problems/contains-duplicate/)
- [LC 560: Subarray Sum Equals K](https://www.leetcode.com/problems/subarray-sum-equals-k/)

## References

- [LC 1: Two Sum on LeetCode](https://www.leetcode.com/problems/two-sum/)
- [LeetCode Discuss](https://www.leetcode.com/problems/two-sum/discuss/)
- [LeetCode Editorial](https://www.leetcode.com/problems/two-sum/editorial/)
