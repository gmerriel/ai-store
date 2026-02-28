# Lead Data Structure

## Purpose
Document the actual fields collected from leads and how to use them in analysis and messaging.

## Available Fields

- **first_name**: Their first name
- **email**: Email address
- **phone**: Phone number (Australian format, often 04xx xxx xxx)
- **vehicle_interest**: TYPE of vehicle (Ute, Sedan, SUV, 4WD, Van, etc.) — NOT a specific make/model
- **vehicle_purpose**: What they need it for (Personal/Family, Work, Business, etc.)
- **new_or_used**: Whether they want New or Used
- **price_range**: Their budget (e.g., 66000)
- **employment_status**: Their employment (Full-time 6+ months, Part-time, Self-employed, Casual, etc.)
- **state**: Australian state (NSW, VIC, QLD, WA, SA, TAS, NT, ACT)
- **permanent_resident**: YES/NO (Australian permanent resident or citizen)
- **pipeline_stage_name**: Current stage in our pipeline
- **total_sends**: How many messages we've sent them
- **total_replies**: How many times they've replied
- **days_since_last_contact**: Days since last message
- **known_objections**: Any objections they've raised
- **comm_preference**: Preferred communication channel

## Using This Data

### Lead Segmentation Examples
- A tradie in WA wanting a new Ute at $66k with full-time employment is a strong lead
- Someone self-employed wanting a used sedan with no price listed needs a softer approach
- A FIFO worker has different send time patterns than office workers
- High reply rate (total_replies / total_sends) indicates strong interest

### Personalisation
Use these fields to genuinely personalise analysis and messaging. Each field tells a story about what the lead needs and when they might be receptive to contact.
