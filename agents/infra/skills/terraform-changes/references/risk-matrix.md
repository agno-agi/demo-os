# Risk Matrix

Maps a planned action to the `ChangePlan.risk` value. When two rows apply, take the higher
risk. Anything in production is at least `medium`.

| Action  | Resource condition                          | Risk   |
|---------|---------------------------------------------|--------|
| scale   | within `max_replicas`, non-production       | low    |
| scale   | within `max_replicas`, production           | medium |
| scale   | beyond `max_replicas` (no headroom)         | high   |
| apply   | additive / in-place, non-production         | low    |
| apply   | in-place config on a production service     | medium |
| rotate  | credential on a staging system              | medium |
| rotate  | credential on a live production system      | high   |
| destroy | stateless resource with a clean rollback    | medium |
| destroy | stateful or shared resource                 | high   |

## Notes

- A `high` risk plan must route through the audit-trailed approval path, not just a plain
  confirmation.
- If `rollback_steps` cannot be written, treat the change as `high` regardless of the row
  above — an irreversible change is the highest risk there is.
- Number of affected services is a multiplier: a change touching three or more downstream
  services moves up one risk tier.
