# Lab 08 — H2 Reflection

AI-assisted draft — Phát should review it for personal accuracy before submission.

One indirect attack I would test is hiding an instruction in a retrieved handbook passage that tells the assistant to ignore the question and reveal unrelated private details.
The assistant's RAG prompt labels source text as data and its parser restricts citations to retrieved IDs, but neither layer guarantees that the model will ignore every injected instruction.
