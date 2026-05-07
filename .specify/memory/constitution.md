<!--
Sync Impact Report
Version change: N/A -> 1.0.0
Modified principles:
- Placeholder Principle 1 -> I. Code Quality Is a Release Gate
- Placeholder Principle 2 -> II. Testing Proves Behavior
- Placeholder Principle 3 -> III. User Experience Stays Consistent
- Placeholder Principle 4 -> IV. Performance Budgets Are Explicit
- Placeholder Principle 5 -> V. Simplicity and Maintainability
Added sections:
- Engineering Standards
- Development Workflow and Review Gates
Removed sections:
- None
Templates requiring updates:
- Updated: .specify/templates/plan-template.md
- Updated: .specify/templates/spec-template.md
- Updated: .specify/templates/tasks-template.md
- Reviewed: .specify/templates/checklist-template.md
- Not present: .specify/templates/commands/
Follow-up TODOs:
- None
-->

# Edge Constitution

## Core Principles

### I. Code Quality Is a Release Gate

All production code MUST be clear, cohesive, and maintainable before it is
accepted. Implementations MUST follow the repository's established patterns,
use typed or schema-validated boundaries where the stack supports them, and
avoid speculative abstractions. Any added complexity MUST be justified in the
implementation plan with the simpler alternative that was rejected. Rationale:
features are cheaper to change when the code is readable, localized, and
consistent with the system around it.

### II. Testing Proves Behavior

Every feature or bug fix MUST include automated tests for the behavior it
changes, with coverage at the lowest useful level and at least one integration,
contract, or end-to-end test for user-visible workflows or cross-module
contracts. Tests MUST be written or updated before implementation is considered
complete, MUST fail for the defect or missing behavior when practical, and MUST
run in documented commands. Rationale: untested behavior is not a durable
deliverable.

### III. User Experience Stays Consistent

User-facing work MUST preserve interaction patterns, terminology, accessibility,
visual density, and error handling conventions already present in the product.
New UI states MUST cover loading, empty, error, disabled, and success paths
where applicable. Interfaces MUST be responsive across supported viewports and
MUST avoid layout shifts, overlapping text, or controls that resize unpredictably
with dynamic content. Rationale: consistency reduces user learning cost and
prevents regressions in everyday workflows.

### IV. Performance Budgets Are Explicit

Each feature MUST define measurable performance expectations before
implementation, including latency, throughput, memory, bundle size, render
smoothness, startup time, or other domain-relevant budgets. Plans MUST identify
the measurement method and the risk areas most likely to affect the budget.
Performance regressions MUST be fixed or explicitly documented with approval.
Rationale: performance is a product requirement, not an after-the-fact polish
task.

### V. Simplicity and Maintainability

The default solution MUST be the smallest design that satisfies the validated
requirements while leaving a clear path for known near-term change. Code MUST
keep ownership boundaries explicit, avoid hidden global state, and make failure
modes observable through errors, logs, or user-visible feedback as appropriate.
Rationale: simple systems are easier to test, review, operate, and improve.

## Engineering Standards

- Specifications MUST include measurable success criteria for behavior, UX, and
  performance when the feature affects users or runtime characteristics.
- Plans MUST include concrete test commands and performance validation methods.
- Shared contracts, schemas, and public interfaces MUST be versioned or migrated
  deliberately, with compatibility impact documented.
- Error handling MUST be explicit at system boundaries and MUST avoid silent
  data loss or silent user-facing failure.
- Generated, copied, or third-party code MUST be identified and reviewed against
  the same quality, test, UX, and performance gates as hand-written code.

## Development Workflow and Review Gates

1. Specifications define independent user journeys, measurable acceptance
   criteria, UX expectations, and performance outcomes.
2. Plans pass the Constitution Check before design work continues and again
   after design artifacts are created.
3. Tasks include test work, implementation work, UX state coverage, and
   performance validation for each affected user journey.
4. Reviews MUST verify code quality, test evidence, UX consistency, and
   performance evidence before completion.
5. Any exception to a principle MUST be recorded in the plan's Complexity
   Tracking table with rationale, risk, and the simpler alternative rejected.

## Governance

This constitution supersedes conflicting project guidance. Amendments require a
documented change to this file, a semantic version update, and review of the
dependent Spec Kit templates for alignment. Versioning follows:

- MAJOR: Backward-incompatible governance changes, removed principles, or
  redefined compliance expectations.
- MINOR: New principles, new required sections, or materially expanded gates.
- PATCH: Clarifications, wording improvements, and non-semantic corrections.

Compliance is reviewed during specification, planning, task generation, code
review, and release validation. If a feature cannot satisfy a principle, the
plan MUST document the exception before implementation begins.

**Version**: 1.0.0 | **Ratified**: 2026-05-06 | **Last Amended**: 2026-05-06
