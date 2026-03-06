# Lead Data Structure - Mortgage Brokers

## Purpose
Document the actual fields collected from leads and how to use them in analysis and messaging.

## Available Fields

- **first_name**: Their first name
- **email**: Email address
- **phone**: Phone number (Australian format, often 04xx xxx xxx)
- **property_type**: Type of property (House, Apartment, Townhouse, Unit, Land, etc.)
- **loan_purpose**: What the loan is for (Purchase, Refinance, Investment, Construction, etc.)
- **purchase_price**: Estimated purchase price or property value
- **deposit_amount**: How much deposit they have
- **loan_amount**: Requested loan amount
- **employment_status**: Their employment (Full-time 6+ months, Part-time, Self-employed, Casual, etc.)
- **annual_income**: Household income
- **state**: Australian state (NSW, VIC, QLD, WA, SA, TAS, NT, ACT)
- **first_home_buyer**: YES/NO
- **pipeline_stage_name**: Current stage in our pipeline
- **total_sends**: How many messages we've sent them
- **total_replies**: How many times they've replied
- **days_since_last_contact**: Days since last message
- **known_objections**: Any objections they've raised
- **comm_preference**: Preferred communication channel

## Using This Data

### Lead Segmentation Examples
- A first home buyer in Sydney on $95k salary wanting a $700k house is a standard lead
- Someone self-employed wanting to refinance an investment property needs a specialist approach
- A couple upgrading from an apartment to a house with 20% deposit is a strong lead
- High LVR (>80%) leads may have LMI concerns to address

### Personalisation
Use these fields to genuinely personalise analysis and messaging. Each field tells a story about what the lead needs and when they might be receptive to contact.

### Key Mortgage Metrics
- **LVR (Loan-to-Value Ratio)**: loan_amount / purchase_price - critical for lender selection
- **Serviceability**: Based on income vs loan amount - determines borrowing power
- **First Home Buyer**: Eligible for state grants and stamp duty concessions
