# Send Time Optimisation

## Purpose
Recommend optimal send times based on lead behavior patterns, employment type, and timezone awareness to maximize response rates while maintaining compliance.

## Rules

### Day of Week Patterns (Australian Market)
- **Tuesday-Thursday**: Generally best response rates for SMS
- **Monday**: OK but people are catching up on weekend backlog
- **Friday**: Lower engagement, people switching to weekend mode
- **Saturday**: Can work for casual SMS, avoid email
- **Sunday**: Generally avoid unless lead has shown weekend engagement

### Time of Day (AEST/AEDT)
- **Best SMS windows**: 9:00-11:30am, 1:00-3:00pm, 5:30-7:00pm
- **Best email windows**: 7:00-9:00am (morning check), 12:00-1:00pm (lunch), 7:00-9:00pm (evening)
- **NEVER send** before 8:00am or after 8:30pm (compliance + respect)
- **Lunch window** (12:00-1:00pm) works well for casual SMS

### Lead-Specific Factors
- **Employment type matters**: FIFO workers have unusual schedules
- **State timezone**: WA is 2-3 hours behind eastern states
- **Previous engagement**: If they replied at 7pm last time, target evenings
- **Tradies**: Early morning or after-work (before 7am avoid, 3:30-5pm good)

### Output Format
- `recommended_send_time`: "YYYY-MM-DD HH:MM" (in the lead's local timezone)
- `send_time_reasoning`: Brief explanation of why this time
- Must be within compliant hours (8am-8:30pm local time of the lead's state)
