# 0002: Price snapshot on events

Status: accepted
Date: 2026-11-01

## Context

Product prices change over time, but past spending totals must not change.

## Decision

Every event stores `unit_price_ore` at scan time. Changing a product's price
only affects future events.

## Consequences

- Historical totals stay stable and need no price lookup.
- Reports are simple sums over events.

* Events scanned before a price is set have NULL, so setting the first price
  must backfill them.
* Prices are duplicated across many rows.
