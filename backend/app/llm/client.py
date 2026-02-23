from openai import OpenAI
from app.config import settings
from typing import Dict, List, Any
from app.schemas.models import VulnerabilityType, SupportedLanguage


class LLMClient:
    """OpenRouter LLM client for explanation, fixing, and test generation"""
    
    def __init__(self):
        self.client = OpenAI(
            base_url=settings.openrouter_base_url,
            api_key=settings.openrouter_api_key,
            default_headers={
                # FIX: OpenRouter requires these headers
                "HTTP-Referer": "http://localhost:3000",
                "X-Title": "Secure Code Reviewer",
            }
        )
        self.model = settings.openrouter_model

    def _chat(self, system: str, user: str, temperature: float = 0.3, max_tokens: int = 1500) -> str:
        """Central chat method with error handling"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user",   "content": user}
                ],
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            raise RuntimeError(f"LLM request failed: {str(e)}")

    def generate_explanation(
        self,
        code: str,
        vulnerability_type: VulnerabilityType,
        evidence: str,
        similar_examples: List[Dict]
    ) -> Dict[str, str]:

        examples_text = "\n\n".join([
            f"Example {i+1}:\nVulnerable: {ex['vulnerable_code']}\n"
            f"Secure: {ex['secure_code']}\nDescription: {ex['description']}"
            for i, ex in enumerate(similar_examples[:3])
        ])

        prompt = f"""You are a security expert. Explain the following vulnerability clearly.

**Code:**
```
{code}
```

**Vulnerability Type:** {vulnerability_type.value}
**Evidence:** {evidence}

**Similar Examples from Knowledge Base:**
{examples_text if examples_text else "No similar examples found"}

Provide:
1. **What the vulnerability is** (2-3 sentences)
2. **How it can be exploited** (2-3 sentences with example attack)
3. **Security impact** (potential damage)

Keep it concise and developer-friendly."""

        try:
            content = self._chat(
                system="You are a security expert explaining vulnerabilities to developers.",
                user=prompt,
                temperature=0.3,
                max_tokens=800
            )

            security_impact = "This vulnerability could allow attackers to compromise system security."
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if "security impact" in line.lower() or "3." in line:
                    security_impact = '\n'.join(lines[i:i+4]).strip()
                    break

            return {
                "explanation": content.strip(),
                "security_impact": security_impact.strip()
            }
        except Exception as e:
            print(f"Error generating explanation: {e}")
            return {
                "explanation": f"A {vulnerability_type.value} vulnerability was detected in the code.",
                "security_impact": "This could allow attackers to compromise the application."
            }

    def generate_fix(
        self,
        code: str,
        vulnerability_type: VulnerabilityType,
        language: SupportedLanguage,
        intent: Dict,
        secure_examples: List[Dict]
    ) -> Dict[str, str]:

        examples_text = "\n\n".join([
            f"**Example {i+1}:**\nVulnerable:\n```{ex.get('language','')}\n{ex['vulnerable_code']}\n```\n"
            f"Secure:\n```{ex.get('language','')}\n{ex['secure_code']}\n```\nExplanation: {ex['description']}"
            for i, ex in enumerate(secure_examples[:2])
        ])

        valid_cases = "\n".join([
            f"  - Input: {case['input']}, Expected: {case['expected']}"
            for case in intent.get('valid_cases', [])
        ])

        invalid_cases = "\n".join([
            f"  - Input: {case['input']}, Expected: {case['expected']}"
            for case in intent.get('invalid_cases', [])
        ])

        prompt = f"""You are a security engineer. Fix the {vulnerability_type.value} vulnerability while respecting developer intent.

**Original Code ({language.value}):**
```{language.value}
{code}
```

**Vulnerability:** {vulnerability_type.value}

**Developer Intent:**
- Purpose: {intent.get('purpose', 'Not specified')}
- Valid Cases:
{valid_cases if valid_cases else '  - None specified'}
- Invalid Cases:
{invalid_cases if invalid_cases else '  - None specified'}
- Security Constraints: {', '.join(intent.get('security_constraints', ['None']))}
- Side Effects: {', '.join(intent.get('side_effects', ['None']))}

**Secure Patterns from Knowledge Base:**
{examples_text if examples_text else 'Use security best practices'}

**STRICT RULES:**
1. Fix ONLY the {vulnerability_type.value} vulnerability
2. Preserve the original function signature
3. Maintain same code style
4. Do NOT add unnecessary features

Format response EXACTLY as:
FIXED_CODE:
```{language.value}
[fixed code here]
```

EXPLANATION:
[what changed and why]"""

        try:
            content = self._chat(
                system="You are a security engineer fixing vulnerabilities while preserving developer intent.",
                user=prompt,
                temperature=0.2,
                max_tokens=1500
            )

            fixed_code = code
            explanation = "Fix generated successfully"
            changes_summary = f"Fixed {vulnerability_type.value} vulnerability"

            if "FIXED_CODE:" in content and "EXPLANATION:" in content:
                parts = content.split("EXPLANATION:")
                code_part = parts[0].replace("FIXED_CODE:", "").strip()
                explanation = parts[1].strip()

                if "```" in code_part:
                    blocks = code_part.split("```")
                    if len(blocks) >= 3:
                        raw = blocks[1].strip()
                        lines = raw.split('\n')
                        if lines and lines[0].strip().lower() in [l.value.lower() for l in SupportedLanguage]:
                            raw = '\n'.join(lines[1:])
                        fixed_code = raw.strip()
            else:
                # fallback: extract any code block
                if "```" in content:
                    blocks = content.split("```")
                    if len(blocks) >= 3:
                        raw = blocks[1].strip()
                        lines = raw.split('\n')
                        if lines and lines[0].strip().lower() in [l.value.lower() for l in SupportedLanguage]:
                            raw = '\n'.join(lines[1:])
                        fixed_code = raw.strip()
                    explanation = content.split("```")[-1].strip() or explanation

            return {
                "fixed_code": fixed_code,
                "explanation": explanation,
                "changes_summary": changes_summary
            }
        except Exception as e:
            print(f"Error generating fix: {e}")
            return {
                "fixed_code": code,
                "explanation": f"Error generating fix: {str(e)}",
                "changes_summary": "Fix generation failed"
            }

    def generate_tests(
        self,
        original_code: str,
        fixed_code: str,
        language: SupportedLanguage,
        vulnerability_type: VulnerabilityType,
        intent: Dict
    ) -> Dict[str, Any]:

        test_frameworks = {
            SupportedLanguage.PYTHON:     "pytest",
            SupportedLanguage.JAVASCRIPT: "Jest",
            SupportedLanguage.JAVA:       "JUnit",
            SupportedLanguage.CPP:        "Google Test",
            SupportedLanguage.CSHARP:     "NUnit",
            SupportedLanguage.GO:         "testing package",
            SupportedLanguage.PHP:        "PHPUnit"
        }
        framework = test_frameworks.get(language, "pytest")

        valid_cases = "\n".join([
            f"  - Input: {case['input']}, Expected: {case['expected']}"
            for case in intent.get('valid_cases', [])
        ])

        invalid_cases = "\n".join([
            f"  - Input: {case['input']}, Expected: {case['expected']}"
            for case in intent.get('invalid_cases', [])
        ])

        prompt = f"""Generate unit tests for the fixed code below.

**Fixed Code ({language.value}):**
```{language.value}
{fixed_code}
```

**Original Vulnerable Code (reference):**
```{language.value}
{original_code}
```

**Developer Intent:**
- Purpose: {intent.get('purpose', 'Not specified')}
- Valid Cases:
{valid_cases if valid_cases else '  - None specified'}
- Invalid Cases:
{invalid_cases if invalid_cases else '  - None specified'}
- Security Constraints: {', '.join(intent.get('security_constraints', []))}

**Vulnerability Type:** {vulnerability_type.value}

IMPORTANT REQUIREMENTS:
1. Use {framework} syntax
2. Tests MUST be self-contained - NO external dependencies, NO database connections, NO network calls
3. Use mocking/patching for any database or external calls
4. Include tests for: valid inputs, invalid inputs, {vulnerability_type.value} attack prevention
5. For Python: use unittest.mock to mock sqlite3/database calls

Format response EXACTLY as:
TEST_CODE:
```{language.value}
[complete self-contained test file]
```

TEST_DESCRIPTIONS:
- [test 1 description]
- [test 2 description]
- [test 3 description]"""

        try:
            content = self._chat(
                system="You are a security testing expert. Write self-contained tests that use mocking - never real database connections.",
                user=prompt,
                temperature=0.3,
                max_tokens=2000
            )

            tests = ""
            descriptions = []

            if "TEST_CODE:" in content:
                parts = content.split("TEST_DESCRIPTIONS:")
                code_part = parts[0].replace("TEST_CODE:", "").strip()

                if "```" in code_part:
                    blocks = code_part.split("```")
                    if len(blocks) >= 3:
                        raw = blocks[1].strip()
                        lines = raw.split('\n')
                        if lines and lines[0].strip().lower() in [l.value.lower() for l in SupportedLanguage]:
                            raw = '\n'.join(lines[1:])
                        tests = raw.strip()

                if len(parts) > 1:
                    for line in parts[1].strip().split('\n'):
                        stripped = line.strip()
                        if stripped.startswith(('-', '*', '•')):
                            descriptions.append(stripped[1:].strip())
                        elif stripped and stripped[0].isdigit() and '.' in stripped[:3]:
                            descriptions.append(stripped.split('.', 1)[1].strip())

            if not tests:
                tests = "# Test generation failed - LLM did not follow format"

            if not descriptions:
                descriptions = [
                    "Valid input behavior tests",
                    "Invalid input handling tests",
                    f"{vulnerability_type.value} exploit prevention tests"
                ]

            return {"tests": tests, "test_descriptions": descriptions}

        except Exception as e:
            print(f"Error generating tests: {e}")
            return {
                "tests": f"# Error generating tests: {str(e)}",
                "test_descriptions": ["Test generation failed"]
            }


# Global instance
_llm_client = None

def get_llm_client() -> LLMClient:
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient()
    return _llm_client
