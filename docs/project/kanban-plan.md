# Modoroco v0.1 Foundation project plan

The intended GitHub Project uses Backlog, Ready, In Progress, Review, Blocked, and Done. Fields are
Type, Priority, Area, Milestone, Effort, Release, and Owner. Milestones are: repository/architecture,
domain engine, persistence/migrations, API, worker, authentication/isolation, Docker/CI, integration
contract, first system test, and first container release.

Creation is blocked in this checkout because `git remote -v` returns no repository remote. GitHub
CLI is authenticated with `repo`, `workflow`, and `project`, but selecting or mutating an assumed
organization repository would be unsafe. After adding the authoritative remote, run `gh repo view`
to verify ownership, create the ten milestones and issues from `issue-manifest.md`, then create the
organization project and add each issue with its documented status and fields.

