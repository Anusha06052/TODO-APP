# PRD 

**Status:** Draft  
**Date:** 2026-04-01  
**Author:** GitHub Copilot (generated via generate-prd.prompt.md)

---

## Feature Title

AI-Powered Task Suggestion System

---

## Problem Statement

Users frequently struggle to translate high-level goals into a concrete, manageable set
of tasks. Manually decomposing objectives is time-consuming and often results in
incomplete or poorly prioritised task lists. This feature uses AI to instantly break
down any user-provided goal into actionable tasks and subtasks with suggested priorities,
dramatically reducing the effort required to plan and start working.

---

## User Stories

- **Given** I have a high-level goal in mind,  
  **When** I type it into the AI suggestion panel and submit,  
  **Then** the app generates a structured list of actionable tasks and subtasks that
  relate to my goal.

- **Given** AI suggestions have been generated,  
  **When** I review the suggestion list,  
  **Then** I can see each task's title, description, and priority level (High / Medium / Low).

- **Given** I am reviewing generated suggestions,  
  **When** I edit a task's title or description inline,  
  **Then** my changes are saved against that suggestion before I commit them to my task list.

- **Given** I am reviewing generated suggestions,  
  **When** I deselect one or more tasks using the checkbox,  
  **Then** those tasks are excluded when I accept the remaining suggestions.

- **Given** I have reviewed and edited my suggestions,  
  **When** I click "Add to My Tasks",  
  **Then** only the selected tasks are saved to my main todo list and I am redirected
  to the task list view.

- **Given** the AI service is unavailable or returns an error,  
  **When** I submit a goal,  
  **Then** a clear, user-friendly error message is shown and I can retry without losing
  my input.

---

## Acceptance Criteria

- [ ] A text input accepts a goal of 5–500 characters; shorter or longer inputs are
      rejected with an inline validation message.
- [ ] Submitting a valid goal calls the backend which returns 2–10 suggested tasks
      within 30 seconds.
- [ ] Each suggested task has a title (required), a description (optional), and a
      priority level: High, Medium, or Low.
- [ ] Subtasks are visually nested beneath their parent task in the review UI.
- [ ] The user can edit any task's title or description inline before saving.
- [ ] Each task has a checkbox; only checked tasks are saved when the user accepts.
- [ ] Clicking "Add to My Tasks" creates real Todo records and navigates to the task
      list, displaying the newly created todos.
- [ ] If the AI service fails, an error banner is shown; the generate button is
      re-enabled so the user can retry.
- [ ] If no tasks are selected when "Add to My Tasks" is clicked, a validation message
      prevents submission.
- [ ] The suggestion session is discarded when the user navigates away or dismisses the
      panel, and no partial data is persisted.

---

## Edge Cases & Error States

| Scenario | Expected Behaviour |
|---|---|
| Goal input is blank or whitespace-only | Inline validation error; submission blocked |
| Goal is fewer than 5 characters | Inline validation error; submission blocked |
| Goal exceeds 500 characters | Character counter shown; input truncated or blocked |
| AI provider returns an error or times out | Error banner displayed; retry button enabled |
| AI returns 0 tasks | Informational message "No suggestions generated — try rephrasing your goal" |
| User clicks "Add to My Tasks" with no tasks selected | Inline warning "Select at least one task" |
| User navigates away mid-review | Suggestion session data is discarded; no todos are created |
| Duplicate task title already exists in the todo list | Suggestion is still saved; no conflict error (deduplication is out of scope) |

---

## Out of Scope

- User authentication — this remains a single-user application.
- Saving or re-loading past suggestion sessions after the page is refreshed.
- Automatic scheduling or deadline assignment for suggested tasks.
- AI model selection or configuration by the user.
- Attaching file attachments or links to suggested tasks.
- Multi-language support for goal input / AI output.
- Deduplication of AI-suggested tasks against existing todos.

---

## Open Questions

1. **AI provider** — Which provider should be used (OpenAI, Azure OpenAI, Anthropic)?
   Does the organisation already have a preferred vendor or API key?
2. **Cost control** — Should there be a rate limit on how often a user can call the
   suggestion endpoint (e.g., 10 requests per hour)?
3. **Priority mapping** — Should suggested priority levels map directly to an existing
   priority field in the Todo model, or is priority a new field to be added?
4. **Subtask depth** — Should the AI be constrained to a maximum nesting depth
   (e.g., one level of subtasks only)?
5. **Category assignment** — Should the user be able to pre-select a category before
   generating suggestions, so the AI scopes tasks to that category?
