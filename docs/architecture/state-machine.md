# Session state machine

`created → running → paused → running` is the ordinary active path. Completing the final phase
moves to `completed`; cancellation from any non-terminal state moves to `cancelled`. Only the
explicit `restart` command moves a completed or cancelled session back to `created`.

Start requires `created`; pause requires `running`; resume requires `paused`; skip, extend, and
complete-phase require an active state. Every successful command increments `version` once and
emits one meaningful domain event. Invalid state and duration operations are typed domain errors.

`expected_end_at` is present only while running. A pause captures remaining seconds, and resume
creates a new expected end from that frozen duration. There are no server-side decrement loops.

