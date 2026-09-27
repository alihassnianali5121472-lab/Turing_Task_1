"""Shipment case table for generate_fixture.py (build-time only).

Each case: ship = (shipment_id, pickup_date, deliver_by, consignee_id, bol_class[, status])
units = (bol_revision, unit_id, nmfc_item, unit_type, dimensions_in, pieces, weight_lb, handling_note)
dimensions_in is "L x W x H" for one piece, or "D dia x H h" for a drum.
"""

CASES = [
    # plain palletised hardware, deficit-weight band
    {"ship": ("BOL-40817", "2026-10-08", "2026-10-16", "CN-104", "70"),
     "units": [(1, "PU-88213", "24150", "PALLET", "48 x 40 x 46", 1, "455", ""),
               (1, "PU-88214", "24150", "PALLET", "48 x 40 x 44", 1, "455", "")]},
    # drums: overall box vs cylinder; one line covering four drums
    {"ship": ("BOL-40952", "2026-10-09", "2026-10-19", "CN-141", "70"),
     "units": [(1, "DR-3301", "48620", "DRUM", "22.5 dia x 34.25 h", 4, "560", "")]},
    {"ship": ("BOL-41306", "2026-10-13", "2026-10-20", "CN-117", "50"),
     "units": [(1, "DR-3390", "158850", "DRUM", "23.5 dia x 34.5 h", 1, "520", "keep upright"),
               (1, "DR-3391", "158850", "DRUM", "23.5 dia x 34.5 h", 1, "520", "keep upright")]},
    # top load only
    {"ship": ("BOL-40633", "2026-10-08", "2026-10-15", "CN-156", "125"),
     "units": [(1, "PU-87740", "79260", "PALLET", "48 x 40 x 44", 2, "600", "Top load only")]},
    # no freight on top
    {"ship": ("BOL-41178", "2026-10-12", "2026-10-16", "CN-192", "175"),
     "units": [(1, "CR-5120", "82240", "CRATE", "60 x 36 x 50", 1, "260",
                "Fragile - no freight on top")]},
    # do not stack
    {"ship": ("BOL-40721", "2026-10-09", "2026-10-16", "CN-122", "65"),
     "units": [(1, "PU-88002", "61320", "PALLET", "42 x 42 x 30", 1, "850", "DO NOT STACK"),
               (1, "PU-88003", "61320", "PALLET", "42 x 42 x 30", 1, "850", "DO NOT STACK")]},
    # fractional inches
    {"ship": ("BOL-41022", "2026-10-13", "2026-10-19", "CN-185", "70"),
     "units": [(1, "PU-88390", "24150", "PALLET", "47.5 x 39.5 x 40.25", 1, "670", "")]},
    {"ship": ("BOL-40588", "2026-10-08", "2026-10-15", "CN-163", "65"),
     "units": [(1, "SK-2210", "110550", "SKID", "96.5 x 24.25 x 18.5", 1, "580", "stack max 2 high")]},
    # mixed-density units on one bill
    {"ship": ("BOL-41290", "2026-10-14", "2026-10-21", "CN-104", "125"),
     "units": [(1, "PU-88611", "24150", "PALLET", "48 x 40 x 30", 1, "900", ""),
               (1, "PU-88612", "24150", "PALLET", "48 x 40 x 48", 1, "380", "")]},
    # revised bill
    {"ship": ("BOL-40864", "2026-10-09", "2026-10-16", "CN-138", "175"),
     "units": [(1, "PU-87901", "79260", "PALLET", "48 x 40 x 50", 1, "310", ""),
               (1, "PU-87902", "79260", "PALLET", "48 x 40 x 50", 1, "310", ""),
               (1, "PU-87903", "79260", "PALLET", "48 x 40 x 40", 1, "220", ""),
               (2, "PU-87901", "79260", "PALLET", "48 x 40 x 50", 1, "310", ""),
               (2, "PU-87903", "79260", "PALLET", "48 x 40 x 46", 1, "240", "")]},
    # export repeated a row
    {"ship": ("BOL-41145", "2026-10-13", "2026-10-20", "CN-141", "70"),
     "units": [(1, "PU-88740", "133330", "PALLET", "48 x 48 x 42", 1, "1160", ""),
               (1, "PU-88741", "133330", "PALLET", "48 x 48 x 42", 1, "1160", ""),
               (1, "PU-88741", "133330", "PALLET", "48 x 48 x 42", 1, "1160", "")]},
    # density exactly on a bound
    {"ship": ("BOL-40779", "2026-10-08", "2026-10-15", "CN-185", "85"),
     "units": [(1, "PU-88120", "61320", "PALLET", "48 x 40 x 36", 1, "600", "")]},
    {"ship": ("BOL-41233", "2026-10-14", "2026-10-21", "CN-156", "175"),
     "units": [(1, "PU-88655", "79260", "PALLET", "48 x 40 x 54", 1, "360", "")]},
    # fixed-class items
    {"ship": ("BOL-40996", "2026-10-09", "2026-10-16", "CN-117", "85"),
     "units": [(1, "PU-88298", "87730", "PALLET", "40 x 48 x 36", 1, "500", "")]},
    {"ship": ("BOL-41061", "2026-10-13", "2026-10-20", "CN-192", "85"),
     "units": [(1, "PU-88431", "116030", "PALLET", "48 x 45 x 48", 1, "780", "")]},
    # Monday pickup, holiday carriers closed
    {"ship": ("BOL-41187", "2026-10-12", "2026-10-19", "CN-185", "70"),
     "units": [(1, "PU-88502", "110550", "SKID", "96 x 24 x 20", 1, "615", "")]},
    {"ship": ("BOL-41199", "2026-10-12", "2026-10-19", "CN-163", "150"),
     "units": [(1, "PU-88518", "156610", "PALLET", "48 x 48 x 60", 1, "212", "")]},
    # deliver-by on the edge
    {"ship": ("BOL-40701", "2026-10-08", "2026-10-13", "CN-192", "85"),
     "units": [(1, "PU-87995", "24150", "PALLET", "48 x 40 x 40", 1, "700", "")]},
    # light shipment, minimum charges tie
    {"ship": ("BOL-40912", "2026-10-09", "2026-10-15", "CN-192", "70"),
     "units": [(1, "PU-88260", "24150", "PALLET", "40 x 48 x 24", 1, "260", "")]},
    # liftgate + appointment
    {"ship": ("BOL-41354", "2026-10-14", "2026-10-22", "CN-170", "85"),
     "units": [(1, "PU-88790", "82240", "CRATE", "72 x 40 x 44", 2, "1380", "")]},
    {"ship": ("BOL-40680", "2026-10-08", "2026-10-15", "CN-117", "60"),
     "units": [(1, "PU-87950", "110550", "SKID", "96 x 30 x 16", 1, "1480", ""),
               (1, "PU-87951", "110550", "SKID", "96 x 30 x 16", 1, "1480", "")]},
    # cancelled
    {"ship": ("BOL-40745", "2026-10-09", "2026-10-16", "CN-122", "70", "CANCELLED"),
     "units": [(1, "PU-88040", "24150", "PALLET", "48 x 40 x 40", 1, "820", "")]},
    {"ship": ("BOL-41267", "2026-10-14", "2026-10-21", "CN-138", "125"),
     "units": [(1, "PU-88601", "79260", "PALLET", "48 x 40 x 60", 1, "420", "No stacking"),
               (1, "PU-88602", "79260", "PALLET", "48 x 40 x 60", 1, "420", "")]},
    # cartons on a larger pallet: overall footprint is the pallet's, height adds the deck
    {"ship": ("BOL-40826", "2026-10-08", "2026-10-15", "CN-104", "85"),
     "units": [(1, "PU-87811", "24150", "PALLET", "44 x 36 x 40", 1, "690",
                "cartons on a 48 x 40 pallet with 5 in deck")]},
    {"ship": ("BOL-41318", "2026-10-13", "2026-10-20", "CN-122", "100"),
     "units": [(1, "PU-88760", "82240", "PALLET", "40 x 30 x 48", 2, "620",
                "cartons on a 48 x 40 pallet with 6 in deck - top load only")]},
    # goods longer than the skid they ride on
    {"ship": ("BOL-40943", "2026-10-09", "2026-10-16", "CN-185", "70"),
     "units": [(1, "SK-2244", "110550", "SKID", "105 x 22 x 18", 1, "560",
                "steel uprights on a 96 x 24 skid with 4 in deck")]},
    # drums, one of them may not be stacked on
    {"ship": ("BOL-41342", "2026-10-14", "2026-10-21", "CN-141", "70"),
     "units": [(1, "DR-3420", "48620", "DRUM", "23 dia x 35 h", 2, "708", ""),
               (1, "DR-3421", "48620", "DRUM", "23 dia x 35 h", 1, "320", "open-head drum - nothing on top")]},
]
