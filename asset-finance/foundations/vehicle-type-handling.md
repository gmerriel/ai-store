# Vehicle Type Handling

## Purpose
Communicate accurately about vehicle types without inventing specific makes/models that leads didn't mention. This prevents misinformation and maintains authenticity.

## Rules

### What Leads Tell Us
Leads provide the TYPE of vehicle they want, not the specific make/model.
- Vehicle types received: Ute, Sedan, SUV, 4WD, Van, Truck, Hatchback, Wagon, Coupe, Convertible, etc.

### Critical Rule
- NEVER reference specific makes/models (Hilux, Triton, Ranger, Corolla, etc.) unless the lead specifically mentioned one
- It's OK to say "ute finance" or "your SUV" — just don't invent a specific model
- If `vehicle_interest` is generic like "car", just say "vehicle" or "car"

### Normalise Casing
Database entries may have inconsistent formatting (e.g., "UTE", "Ute", "ute"). Always normalise to natural Australian English:
- "UTE" / "Ute" → "ute" (always lowercase in Australia)
- "SUV" → "SUV" (acronym, stays uppercase)
- "4WD" → "4WD" (acronym, stays uppercase)
- "SEDAN" / "Sedan" → "sedan" (lowercase)
- "HILUX" / "Hilux" → "Hilux" (proper noun, capitalised)
- General rule: common vehicle types are lowercase, acronyms stay uppercase, brand names are capitalised

### Why This Matters
- Shows we're actually listening to what they told us
- Prevents assumptions about affordability or preferences
- Keeps messaging authentic and lead-specific
