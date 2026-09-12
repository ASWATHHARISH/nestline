# Stage 7 Routine Symptom Policy — Qualified Review Packet

**Status:** `EXTERNAL REVIEW REQUIRED — CAPABILITY UNAVAILABLE`

This packet prepares the product, clinical-safety and India-localisation decisions needed before routine symptom guidance can be enabled. It is not a clinical policy, an approval, or evidence that a clinician reviewed Nestline. The deterministic Stage 6 urgent gate remains first and cannot be downgraded. Unknown, ambiguous, new or worsening symptom language continues to clarify or stop conservatively.

## Reviewers required

| Review lane | Named reviewer | Decision | Date |
|---|---|---|---|
| Product/content | Pending team assignment | Pending | Pending |
| Qualified maternal-health clinical safety | Pending team assignment | Pending | Pending |
| India localisation and care routes | Pending team assignment | Pending | Pending |
| Source/licence | Pending team assignment | Pending | Pending |

Codex must not fill these identities or decisions on behalf of a human.

## Decision record required for each supported routine symptom intent

| Field | Reviewer must provide or approve |
|---|---|
| Policy item ID and version | Stable identifier and change history |
| Intended journey applicability | Pregnancy/postpartum status and exact week/day/range |
| User wording covered | Reviewed examples and explicitly unsupported wording |
| Minimum clarification | Symptom, onset, severity, duration, change, recurrence and relevant journey details actually required |
| Allowed route | Prompt/same-day professional contact, routine professional follow-up, monitor/track, or insufficient information |
| Immediate action wording | Evidence-supported, action-first wording |
| Actions to avoid | Only evidence-supported boundaries |
| Escalation changes/warning signs | Reviewed deterministic criteria and fixed wording |
| Professional route | Reviewed India-appropriate service/clinician wording |
| Possible-reason explanation | Allowed only when directly supported; never a diagnosis |
| Eligible evidence | Exact approved evidence IDs, spans, versions, jurisdiction and permitted-use lane |
| Contraindications and conflicts | Personal facts that force clarification/abstention |
| Expiry/re-review rule | Date or source-version event that disables the policy |

## Required review scenarios

The qualified review must cover pregnancy and postpartum applicability; unknown, incomplete, persistent and worsening wording; medication or supplement reaction concerns; mental-health distress; conflicting records; new symptoms inside movement/nutrition/follow-up requests; prompt injection; urgent wording mixed with a routine request; and language outside the explicitly supported English scope.

## Engineering behavior until approval

- The routine symptom worker remains unavailable when this approved record is absent.
- No provider or model may improvise the missing policy.
- Stage 6 urgent and clarification routes run before any worker.
- An urgent route returns fixed wording with zero ordinary-generation calls.
- A non-match is never described as proof that a symptom is safe.
- No personal information is sent to a reviewer or external system by this packet.
## Open safety-specification gap found during Stage 5–8 rectification

The trace review identified two related reduced-movement phrases that require qualified policy review. Engineering has not added or self-approved a clinical rule:

- "I feel reduced movement right now." currently has no configured rule-specific match. It takes the generic "needs_clarification" fallback, allows zero ordinary generation, and records "minimum_clarification_required". The user-facing conservative safety route remains unchanged.
- "My baby is moving less than usual right now." currently matches draft evaluation rule "S-FETAL" and takes the evaluation-only urgent route with zero ordinary generation. Its final public urgent wording, applicability and routing remain pending qualified maternal-health safety, India-localisation, product/content and source/licence review.

The Stage 6 specification remains "draft", both results remain public-routing-ineligible, and these engineering regression expectations are software-contract evidence only. They do not constitute clinical validation or publication approval.
