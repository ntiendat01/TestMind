"""Token counters. The approximate counter is not a model tokenizer."""


class ApproximateTokenCounter:
    def count(self, text: str) -> int:
        stripped = text.strip()
        if not stripped:
            return 0
        return max(1, len(stripped) // 4)
