# Lab 3 - AI extension review

Member: `chp0703`

1. Ask an AI coding assistant to extend your service with ONE feature, e.g.
   "Add an 'exam absence' answer that tells students the deadline from the handbook."

   Feature selected: Help / Supported Capabilities. It provides a deterministic answer to
   `help`, `What can you do?`, and `What services do you support?` without an LLM or API key.

2. Paste the prompt you used:

   "Implement a Help feature that allows users to ask what the Smart Virtual Assistant can do.
   Return a clear, deterministic response that explains the capabilities actually implemented in
   the current application."

3. Review the generated code manually. Document **at least three changes** you made:

| # | What the AI generated | Problem you found | What you changed | Why |
|---|---|---|---|---|
| 1 | Initial AI draft proposal: match the word `help` anywhere in a message. | It would classify a tuition or library request containing "help" as Help. | Used an exact normalized request set and added unrelated-message tests. | Prevents Help from replacing future domain intents. |
| 2 | Initial AI draft proposal: describe tuition, offices, and handbook rules in Help. | Those capabilities are not implemented in this skeleton. | Limited `HELP_RESPONSE` to Help, the only implemented capability. | Keeps user-facing claims accurate. |
| 3 | Initial AI draft proposal: select response text directly in the router. | Routing and response wording would be coupled. | Kept intent selection in `router.py`, deterministic messages in `responder.py`, and orchestration in `service.py`. | Preserves the intended router -> service -> responder separation. |

Checklist: interfaces respected? new dependencies? secrets? logging of user data? tests added and meaningful?

- Interfaces respected: yes; Help uses the new minimal router -> service -> responder flow.
- New dependencies: none.
- Secrets: no credentials are added, read, printed, or logged by the feature.
- Logging of user data: none.
- Tests: added routing, response-claim, and service tests; results are recorded in the AI-use log.

Limitations and personal verification required: The broader assistant capabilities are still
placeholders, so Help intentionally advertises only Help. Before submitting, personally review
the wording and confirm that the three documented review changes accurately represent your own
review of this AI-assisted work.
