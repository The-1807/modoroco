# Modoroco v0.1 Foundation project plan

The intended GitHub Project uses Backlog, Ready, In Progress, Review, Blocked, and Done. Fields are
Type, Priority, Area, Milestone, Effort, Release, and Owner. Milestones are: repository/architecture,
domain engine, persistence/migrations, API, worker, authentication/isolation, Docker/CI, integration
contract, first system test, and first container release.

The authoritative remote is `https://github.com/The-1807/modoroco.git`. The organization project
was created at <https://github.com/orgs/The-1807/projects/5> and contains issues 6–20 from the
manifest. Status, Priority, Area, Effort, Release, Owner, and built-in Milestone values are assigned.

GitHub reserves the field name `Type` for its organization issue-type feature, and rejected creation
of a custom project field with that exact name. Repository `type:*` labels therefore remain the
authoritative type taxonomy until organization issue types are configured. GitHub's public Projects
CLI and GraphQL schema did not expose creation of the requested custom views; the project retains
its default view with the full six-option Status workflow.
