class ResumeExtractionPrompt:
    @staticmethod
    def prompt(raw_text: str) -> str:
        return """
            You are an expert resume parser. Extract the following fields from the provided resume text.
            Return STRICT JSON ONLY, following EXACTLY this structure that can be parsed using json.loads() and loaded into a python dict.
            Don't include code block json formatting like json ````json ... ````

            Input Resume Text:
            RAW_TEXT_PLACEHOLDER

            Output JSON Structure:
            {
                "name": "string or null",
                "email": "string or null",
                "phone": "string or null",
                "summary": "string or null",
                "skills": ["skill1", "skill2", ...],
                "experience": [
                    {
                        "company": "string or null",
                        "role": "string or null",
                        "start_date": "string or null",
                        "end_date": "string or null",
                        "description": "string or null"
                    }
                ],
                "education": [
                    {
                        "institution": "string or null",
                        "degree": "string or null",
                        "start_year": "string or null",
                        "end_year": "string or null"
                    }
                ]
            }
            """.replace("RAW_TEXT_PLACEHOLDER", raw_text)
