# Writing

Orwell's rules ("Politics and the English Language", https://orwell.ru/library/essays/politics/english/e_polit/) for all prose you write for a person: replies, PRs, commits, comments, docs, notes, Slack and email drafts.

1. No stock metaphors, similes, or figures of speech
2. Use the short word when it will do
3. Cut every word you can
4. Use the active voice, not the passive
5. Use everyday English, not foreign phrases, science words, or jargon, when a plain word means the same
6. Break any of these rules rather than write something ugly or unclear

ASD-STE100 Simplified Technical English (https://asd-ste100.org/), the rules that fit outside a maintenance manual:

- Sentences: at most 20 words in steps, 25 in description; one topic per sentence
- Steps: command form ("Run the script"), one instruction per sentence, in a numbered list
- Paragraphs: one topic, at most 6 sentences
- One word, one meaning: pick one term for a thing and keep it; no synonyms for variety
- No noun stacks over 3 words ("job retry limit", not "prod batch job queue retry limit")
- Keep articles and verbs; don't drop words to save space
- Simple tenses (present, past, future); use -ing words only in names of things
- Passive only when the actor is unknown
- Start a warning with a plain command or condition ("Do not run this on prod")
- Orwell's rule 6 applies to these too

When `prose-lint` is on the PATH, run it on a PR body, a doc or a long message before you send it. Fix its findings. Read its warnings and decide.
