# Maps known sector name variants (e.g. mixed apostrophe types) to their
# canonical form as stored in the database.
#
# Use case: when a sector lookup fails, try resolving it through this dict
# before giving up. Add new entries here as mismatches are discovered.
#
# Format:
#   "variant name as it appears in the source data": "canonical name in DB"

SECTOR_ALIASES: dict[str, str] = {
    "Gare routière à l'intérieur ou à proximité du marché": "Gare routière à l’intérieur ou à proximité du marché",
    "Lits de maternité et d'hospitalisation": "Lits de maternité et d’hospitalisation",
    "Bureau d'école primaire" : "Bureau d’école primaire",
}
