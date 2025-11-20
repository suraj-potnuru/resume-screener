import json

class SummarizePrompt:
    @staticmethod
    def prompt(question: str, search_results) -> str:
        return """
            You are an expert at summarizing information. Given the following search results from a resume vector database using semantic search,
            provide a concise and informative summary that answers the question below.

            Question:
            QUESTION_PLACEHOLDER

            Search Results:
            SEARCH_RESULTS_PLACEHOLDER

            """.replace("QUESTION_PLACEHOLDER", question).replace("SEARCH_RESULTS_PLACEHOLDER", json.dumps(search_results))