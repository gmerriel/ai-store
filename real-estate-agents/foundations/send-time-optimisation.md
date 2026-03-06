# Send Time Optimisation

## Purpose
Recommend optimal send times based on lead behavior patterns, employment type, and timezone awareness to maximize response rates while maintaining compliance.

## Rules

### Day of Week Patterns (Australian Market)
- **Tuesday-Thursday**: Generally best response rates for SMS
- **Monday**: OK but people are catching up on weekend backlog
- **Friday**: Lower engagement, people switching to weekend mode
- **Saturday**: Good for property-related SMS - people are often at open homes or thinking about property on weekends
- **Sunday**: Can work for casual property SMS, avoid email

### Time of Day (AEST/AEDT)
- **Best SMS windows**: 9:00-11:30am, 1:00-3:00pm, 5:30-7:00pm
- **Best email windows**: 7:00-9:00am (morning check), 12:00-1:00pm (lunch), 7:00-9:00pm (evening)
- **NEVER send** before 8:00am or after 8:30pm (compliance + respect)
- **Saturday morning** (9:00-11:00am) is prime time for property leads - open home season

### Lead-Specific Factors
- **Sellers**: Often more available during business hours, urgent timeline
- **Buyers**: May be working full-time, evenings and weekends better
- **State timezone**: WA is 2-3 hours behind eastern states
- **Previous engagement**: If they replied at 7pm last time, target evenings
- **Investors**: Often prefer business hours, more transactional mindset

### Output Format
- `recommended_send_time`: "HH:MM" — time only, 24-hour format, in the lead's local timezone
- `send_time_reasoning`: Brief explanation of why this time
- The system will schedule for today or the next valid send day automatically. You only need to recommend the optimal TIME of day.
- Must be within compliant hours (9am-7pm local time of the lead's state)
- Pick natural-looking times (e.g. 10:17, 14:42) not round numbers (10:00, 15:00)
