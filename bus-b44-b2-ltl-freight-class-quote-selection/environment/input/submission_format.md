# Submission format

Deliver exactly these two files, in `/app`:

- `quote_selection.xlsx` — the quote sheet.
- `results.json` — the headline figures.

## `quote_selection.xlsx`

A worksheet named `Quotes`. Its first row carries these column names, in this order:

`shipment_id`, `density_pcf`, `freight_class`, `carrier_id`, `linehaul_usd`, `accessorial_usd`, `total_cost_usd`

Below it, one row for every shipment being quoted (and no others), in the order `shipments.csv`
lists them, and nothing else on the sheet under the table.

- `density_pcf` — the shipment's density, to two decimals.
- `freight_class` — the class the shipment takes, as a number (`92.5`, `100`).
- `carrier_id` — the awarded carrier as it appears in the rate files, or `NONE`.
- `linehaul_usd`, `accessorial_usd`, `total_cost_usd` — to the cent; `0` on an unawarded
  shipment.

Write every number as a plain number: no thousands separators and no currency symbols.

## `results.json`

A JSON object with exactly these keys, each a number:

- `awarded_shipment_count`
- `linehaul_total_usd`
- `accessorial_total_usd`
- `quote_total_usd`

The figures are the ones the delivered sheet adds up to.
