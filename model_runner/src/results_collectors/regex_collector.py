import re
from results_collectors.base_collector import BaseCollector


class RegexCollector(BaseCollector):
    def __init__(self, regex: str):
        self.regex = regex
        self._compiled = re.compile(regex, re.MULTILINE)

    def collect(self, output: str) -> list[str]:
        matches = self._compiled.findall(output)
        if not matches:
            return []

        first_match = matches[0]
        if isinstance(first_match, tuple):
            return [match[0] for match in matches if match]

        return matches
