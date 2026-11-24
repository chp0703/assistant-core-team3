# Lab 7 homework — 10-minute usability test

Tester (not in your team, first name only): none — internal walkthrough by the author (the instructor allowed an internal test for this lab)  Date: 2026-11-22
Task you gave them: "Find out if you can register your thesis with 118 credits, and where to replace a lost student card."

Rule: do not help or explain. Watch and write down what happens.

Method: the page was run for real (`streamlit run ui/app.py` on `main` at `d30efed`, API with `RAG_ENABLED=true`) and used like a first-time student: the whole task typed as one message, then short keyword questions. The observations below come from what the page actually showed. Observation 1 was repeated by hand in the browser by the author, with the same reply. No person outside the team took part.

| # | What the tester did or said | What they expected | Why the system/UI caused it | Fix idea |
|---|---|---|---|---|
| 1 | Typed the whole task as one message: "Can I register my thesis with 118 credits, and where do I replace a lost student card?" The reply covered only the student card (Student Affairs, room I.102). | Both answers, or a note that one part was left out. | The assistant returns one best-matching passage, and the page shows no sign that the thesis part was skipped. The welcome message did not say to ask one question at a time. | Tell users to ask one question at a time (done, see below); later, split the message or say which part was not answered. |
| 2 | Asked "thesis 118 credits". The reply quoted the rule: "at least 120 accumulated credits and a cumulative GPA of at least 2.0". | A yes or no for 118 credits. | The retrieval path quotes the document passage and does not compare it with the number the student gave, so the student has to work out that 118 is below 120. | Let the answer state the result ("No: you need 120 credits") when the question contains a number. |
| 3 | After a wrong or incomplete answer (observation 1), looked for a way to say so. At that time each answer had only a 👍 button. "tuition fee" returned "How many credits?" with a 👍 as well. | A way to mark an answer as bad. | The 👎 button was still a TODO in `ui/app.py` (F1), so a student could only praise answers. F1 is now merged (#72), and 👎 sends rating -1. | Done for 👎; later hide the rating buttons on clarifying questions. |

The one change we made (commit link): observation 1, the welcome message now says "Ask one question at a time." in `ui/logic.py` — commit 9ba1724, PR #74.
Before / after screenshot: `docs/lab7/evidence/h1_before_welcome.png` and `docs/lab7/evidence/h1_after_welcome.png`; the problem itself is in `docs/lab7/evidence/h1_before_two_part_question.png`.
