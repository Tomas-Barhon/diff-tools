""""This module contains the RegexCollector class, which is responsible for collecting results from other scripts std
out using regular expressions."""

class RegexCollector:
    """The RegexCollector class is responsible for collecting results from other scripts std out using regular expressions."""

    def __init__(self, regex: str):
        """Initializes the RegexCollector with a regular expression.

        Args:
            regex (str): The regular expression to use for collecting results.
        """
        self.regex = regex

    def collect(self, output: str) -> list[str]:
        """Collects results from the given output using the regular expression.

        Args:
            output (str): The output to collect results from.


