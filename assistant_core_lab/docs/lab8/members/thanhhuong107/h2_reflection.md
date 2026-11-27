# H2 - Reading reflection

I would watch for an indirect prompt injection in a retrieved campus notice that tries to steer the assistant toward an incorrect policy answer ([OWASP LLM01](https://genai.owasp.org/llmrisk/llm01-prompt-injection/)).
I would use the knowledge-base review layer to reject untrusted notices before indexing and verify with a pytest regression that unapproved content cannot become a source for an answer ([pytest Get Started](https://docs.pytest.org/en/stable/getting-started.html)).
