# Quoting rules — classing and awarding LTL shipments

These rules are the sole authority for this round of quoting. The files are the TMS extract
taken on 2026-09-27; pickup and deliver-by dates are the planned ones, and rate sheets are
filed with us as soon as a carrier announces them, which can be ahead of the date they take
effect. Dates are ISO `YYYY-MM-DD`, weights are pounds, dimensions are inches and money is US
dollars.

## 0. The files

- `shipments.csv` — one row per bill of lading: its pickup date, the date the consignee needs it
  by, the consignee, the bill's status in the TMS and the class the shipper wrote on the bill.
- `handling_units.csv` — the handling units (pallets, skids, crates, drums) on each bill, as
  keyed into the TMS: one row per line per revision of the bill. A line covers `pieces`
  identical units; `dimensions_in` gives one piece as the shipper measured it, as length x width
  x height, or as diameter and height for a drum; `weight_lb` is the whole line's weight;
  `handling_note` is the shipper's free-text note on the line and applies to every piece on it.
  Most shippers measure the loaded pallet or skid; a few measure only the goods and note what
  they ride on.
- `consignees.csv` — each consignee's delivery zone and receiving set-up.
- `classification_items.md` — the classification items our shippers bill under.
- `density_classes.csv` — the density scale.
- `rate_sheets.csv` — each carrier's rate sheets, with the date each takes effect, the
  discount off the sheet and the absolute minimum charge.
- `carrier_rates.csv` — the rates on each sheet, by class and weight group.
- `carrier_lanes.csv` — the delivery zones each carrier runs and its transit time to each.
- `carrier_profiles.md` — accessorial services and fees, terminal holidays and our routing guide.

## 1. What is being quoted

A shipment is one bill of lading (`shipment_id`). Only bills whose `status` is `BOOK` are
quoted; a cancelled bill is not quoted and does not go on the quote sheet.

The TMS keeps every revision of a bill. The freight on a bill is the handling units on its
highest `bol_revision`. `unit_id` is the label on the physical freight a line describes; the
export sometimes repeats a line, and a label repeated on the same revision is the same freight,
counted once.

`bol_class` is the class the shipper declared on the bill; the class a shipment takes is the
one section 3 gives.

## 2. Cube and density

Carriers bill on the space freight takes up on the trailer, and their dimensioners measure it
the same way every time:

- Each piece is measured over its overall length, width and height as it stands on the trailer
  floor — the smallest rectangular box that takes in everything that ships with it.
- Every dimension is taken to the next whole inch; a fraction of an inch counts as a full inch.
- The space above a piece that other freight may not be loaded onto — whether the note says it
  must not be stacked on (do not stack), or that it may only ride on top of the load — cannot be
  used for anything else, so that piece is measured to the trailer roof: its height counts as 96
  inches, the interior height of the trailers our carriers run. The handling note says whether
  this is so, in whatever words the shipper used.

A piece's cube is length × width × height ÷ 1728, in cubic feet. A shipment's weight and cube
are the totals over all the freight on the bill, and its density is its weight divided by its
cube, rounded to two decimals.

## 3. The class a shipment takes

Every unit on a bill carries the same `nmfc_item`. Look the item up in
`classification_items.md`.

- An item rated on the density scale takes its class from `density_classes.csv`: the shipment
  falls in the band whose `min_density_pcf` is at or below its density and whose
  `max_density_pcf` is above it (the densest band has no upper limit).
- An item with a fixed class takes that class, whatever its density.

## 4. Which carriers may be quoted

A carrier may be quoted for a shipment only where every one of these holds.

- **Its sheet in force publishes the class.** A carrier's sheet in force on a date is its sheet
  with the latest `effective_date` on or before that date; the shipment is priced on the sheet
  in force on its pickup date. That sheet must carry rates for the shipment's class — a carrier
  whose sheet does not carry the class cannot move it.
- **It runs the lane.** `carrier_lanes.csv` has a row for the carrier and the consignee's
  `delivery_zone`.
- **It picks up that day and delivers in time.** A carrier's business days are Monday to Friday,
  less the days its terminals are closed. The pickup date must be one of them. The delivery date
  is found by counting `transit_days` of the carrier's business days forward from the pickup
  date, the pickup day itself not counted, and it must be on or before the shipment's
  `deliver_by`.
- **It offers what the consignee needs.** A consignee whose `dock_available` is `NO` needs a
  liftgate; one whose `appointment_required` is `YES` needs an appointment delivery. The carrier
  must offer each service the shipment needs.

## 5. What a quote costs

Rates on a sheet are per hundredweight (100 lb) for a class, by weight group. A shipment is
rated in the group with the highest `weight_group_min_lb` at or below its weight: the charge is
that group's rate times the weight in hundredweight. It may instead be rated as though it
weighed the minimum weight of any heavier group on the same sheet and class, at that group's
rate; where that gives a lower charge, the lower charge is the tariff charge.

The discounted charge is the tariff charge less the sheet's `discount_pct` percent, rounded to
the cent. The linehaul is the greater of the discounted charge and the sheet's
`absolute_min_charge_usd`.

Accessorial fees are flat per shipment and come from `carrier_profiles.md`: the liftgate fee
where the shipment needs a liftgate and the appointment fee where it needs an appointment. The
total cost is the linehaul plus the accessorials.

## 6. The award

A shipment is awarded to the qualifying carrier with the lowest total cost. Where two or more
tie on total cost, the one with the earlier delivery date takes it; if they also deliver the
same day, the one ranked higher in the routing guide takes it.

A shipment no carrier qualifies for is left unawarded: it still goes on the quote sheet with its
density and class, with `NONE` as the carrier and `0` for each money column.

## 7. The reported figures

- `awarded_shipment_count` is the number of shipments on the quote sheet that found a carrier.
- `linehaul_total_usd`, `accessorial_total_usd` and `quote_total_usd` are the linehaul,
  accessorial and total-cost columns added across the awarded shipments.
