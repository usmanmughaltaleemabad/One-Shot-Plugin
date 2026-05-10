#!/usr/bin/env python3
"""
v1.1.0: Optional Test-First (TDD) Mode

When the user passes ``--tdd``, the generator emits failing tests first,
then implementation. This module produces structured TDD output and an
explanation block (when ``--explain-tdd`` is also passed — v1.3.2).

Public API:
    tdd = TDDGenerator(framework='fastapi', language='python', explain=True)
    output = tdd.compose(
        feature_name='Rate Limiter',
        tests=[{'name': 'test_drops_excess_messages', 'body': '...'}],
        implementation='class RateLimiter: ...',
    )
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class TDDTest:
    name: str
    body: str
    intent: str = ''  # Why this test exists
    edge_case: str = ''  # What edge case it guards
    failure_mode: str = ''  # What it prevents


class TDDGenerator:
    """Composes test-first output (failing tests + implementation + explanation)."""

    def __init__(self, framework: str = 'fastapi', language: str = 'python', explain: bool = False):
        self.framework = framework.lower()
        self.language = language.lower()
        self.explain = explain

    def compose(self,
                feature_name: str,
                tests: List[Dict],
                implementation: str,
                test_filename: Optional[str] = None,
                impl_filename: Optional[str] = None) -> str:
        test_filename = test_filename or self._default_test_filename(feature_name)
        impl_filename = impl_filename or self._default_impl_filename(feature_name)

        parts = []
        parts.append(f"# Test-First Generation: {feature_name}\n")
        parts.append("This output follows the TDD workflow. Run tests **before** copying the "
                     "implementation — they should all fail. Then copy the implementation and "
                     "rerun: every test should pass.\n")

        # Step 1 — failing tests
        parts.append(f"## 1. Tests (run these first; expect failures)\n")
        parts.append(f"### `{test_filename}`\n")
        parts.append(f"```{self.language}\n{self._render_test_file(tests)}```\n")

        # Step 2 — implementation
        parts.append(f"## 2. Implementation (copy after seeing tests fail)\n")
        parts.append(f"### `{impl_filename}`\n")
        parts.append(f"```{self.language}\n{implementation}\n```\n")

        # Step 3 — verification
        parts.append("## 3. Verify\n")
        parts.append(self._verify_block(test_filename))

        # Step 4 — explanation (if --explain-tdd)
        if self.explain:
            parts.append("## 4. Why each test exists\n")
            for i, t in enumerate(tests, 1):
                tt = self._coerce(t)
                parts.append(f"**Test {i}: `{tt.name}`**")
                if tt.intent:
                    parts.append(f"- Intent: {tt.intent}")
                if tt.edge_case:
                    parts.append(f"- Edge case: {tt.edge_case}")
                if tt.failure_mode:
                    parts.append(f"- Prevents: {tt.failure_mode}")
                parts.append("")

        return "\n".join(parts)

    # ---- helpers -----------------------------------------------------------

    def _default_test_filename(self, feature_name: str) -> str:
        slug = feature_name.lower().replace(' ', '_')
        if self.language == 'python':
            return f"tests/test_{slug}.py"
        if self.language in ('javascript', 'typescript'):
            return f"tests/{slug}.test.ts"
        if self.language == 'go':
            return f"{slug}_test.go"
        if self.language == 'java':
            return f"src/test/java/{feature_name.title().replace(' ', '')}Test.java"
        return f"tests/{slug}_test"

    def _default_impl_filename(self, feature_name: str) -> str:
        slug = feature_name.lower().replace(' ', '_')
        if self.language == 'python':
            return f"{slug}.py"
        if self.language in ('javascript', 'typescript'):
            return f"{slug}.ts"
        if self.language == 'go':
            return f"{slug}.go"
        if self.language == 'java':
            return f"src/main/java/{feature_name.title().replace(' ', '')}.java"
        return slug

    def _render_test_file(self, tests: List[Dict]) -> str:
        if self.language == 'python':
            header = "import pytest\n\n"
            body = "\n\n".join(
                f"def {self._coerce(t).name}():\n    {self._indent(self._coerce(t).body)}"
                for t in tests
            )
            return header + body + "\n"
        if self.language in ('javascript', 'typescript'):
            return "\n\n".join(
                f"test('{self._coerce(t).name}', () => {{\n  {self._coerce(t).body}\n}});"
                for t in tests
            ) + "\n"
        if self.language == 'go':
            return "\n\n".join(
                f"func {self._coerce(t).name.title().replace('_', '')}(t *testing.T) {{\n\t{self._coerce(t).body}\n}}"
                for t in tests
            ) + "\n"
        return "\n\n".join(self._coerce(t).body for t in tests)

    def _verify_block(self, test_filename: str) -> str:
        if self.language == 'python':
            return f"```bash\npytest {test_filename} -v\n# Expected: all tests pass\n```\n"
        if self.language in ('javascript', 'typescript'):
            return f"```bash\nnpm test -- {test_filename}\n```\n"
        if self.language == 'go':
            return f"```bash\ngo test ./...\n```\n"
        return f"```bash\n# run your test suite\n```\n"

    @staticmethod
    def _indent(text: str, spaces: int = 4) -> str:
        pad = ' ' * spaces
        return text.replace('\n', '\n' + pad)

    @staticmethod
    def _coerce(t) -> TDDTest:
        if isinstance(t, TDDTest):
            return t
        return TDDTest(
            name=t.get('name', 'test_case'),
            body=t.get('body', 'assert False  # not implemented'),
            intent=t.get('intent', ''),
            edge_case=t.get('edge_case', ''),
            failure_mode=t.get('failure_mode', ''),
        )


def main():
    tdd = TDDGenerator(language='python', explain=True)
    out = tdd.compose(
        feature_name='Rate Limiter',
        tests=[
            {'name': 'test_drops_excess', 'body': 'limiter = RateLimiter(10)\nfor i in range(15): limiter.take()\nassert limiter.dropped == 5',
             'intent': 'verify the limiter actually rejects requests above the cap',
             'edge_case': 'request count exactly equal to limit', 'failure_mode': 'silent over-admission'},
            {'name': 'test_resets_after_window', 'body': 'pass',
             'intent': 'window must reset', 'edge_case': 'second window allows full quota'},
        ],
        implementation="class RateLimiter:\n    def __init__(self, n): self.n = n; self.dropped = 0\n",
    )
    print(out)


if __name__ == '__main__':
    main()
