# Task 0001: Create Project Documentation

## Goal

Create the first documentation base for `mapping_Paris` so future product, architecture, backlog, and implementation tasks can be driven from stable project decisions.

## Scope

- Create the root README.
- Create the product brief.
- Create the first architecture decision record.
- Create the initial backlog.
- Create this traceability task.
- Create a repository `.gitignore`.
- Initialize Git if needed.
- Commit the documentation.
- Create and configure the GitHub repository if the environment allows it.

## Files created

- `README.md`
- `docs/product/product-brief.md`
- `docs/adr/0001-data-source-and-segment-model.md`
- `docs/backlog/0001-initial-backlog.md`
- `docs/tasks/0001-create-project-documentation.md`
- `.gitignore`

## Acceptance criteria

- The six requested files exist.
- Product and technical decisions are coherent across the documentation.
- No Android code, Gradle project, data pipeline, or dependency is created.
- V1 is clearly limited to manual validation without GPS.
- Paris intra-muros is the explicit geographic perimeter.
- The Bois de Boulogne and Bois de Vincennes are excluded.
- Segment source data and user progress data are explicitly separated.
- The repository is a valid Git repository on branch `main`.
- The initial documentation is committed with message `Initial project documentation`.
- The GitHub remote is configured if GitHub CLI and authentication are available.

## Validation steps

- List created files.
- Run `git status`.
- Run `git log --oneline -1` after the commit.
- Run `git remote -v` if a remote has been configured.
- Review the product brief and ADR for consistency.

## Non-goals

- Create Android source code.
- Initialize Gradle.
- Add dependencies.
- Build a Python or data pipeline implementation.
- Configure Play Store publication.
- Add backend, account, cloud sync, GPS validation, or offline maps for V1.
