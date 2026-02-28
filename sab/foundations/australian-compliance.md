# Australian Compliance Rules

## Purpose
Ensure all outbound communications comply with Australian financial services regulations and consumer protection laws.

## Rules by Regulation

### ASIC RG 234: Advertising Financial Products

#### RULE ASIC-01 | Rate Disclosure Prohibition
- **Constraint**: MUST NOT contain specific interest rates (e.g., "5.9%", "from 4.5%")
- **Test**: Scan for any number followed by %, or words "rate", "interest rate", "comparison rate", "APR"
- **Severity**: CRITICAL

#### RULE ASIC-02 | Approval Certainty Prohibition
- **Constraint**: MUST NOT imply guaranteed, certain, or highly likely approval
- **Test**: Scan for "guaranteed", "approved", "100%", "definitely", "certain", "assured", "no questions asked"
- **Severity**: CRITICAL

#### RULE ASIC-03 | Misleading Comparison Prohibition
- **Constraint**: MUST NOT use unsubstantiated superlatives
- **Test**: Scan for "cheapest", "best rates", "lowest", "#1", "unbeatable"
- **Severity**: HIGH

#### RULE ASIC-04 | False Urgency Prohibition
- **Constraint**: MUST NOT create artificial deadlines on finance offers
- **Test**: Scan for "expires", "limited time", "act now", "offer ends", "last chance"
- **Exception**: Genuine seasonal references (EOFY, new model year) with factual basis permitted
- **Severity**: HIGH

#### RULE ASIC-05 | Factual Claims
- **Constraint**: Claims MUST be reasonable, representative, non-misleading
- **Severity**: MEDIUM

### SPAM Act 2003

#### RULE SPAM-01 | Sender Identification
- **Constraint**: Message MUST identify sender as SAB or Strategic Asset Brokers (can be in sign-off)
- **Test**: Check for "SAB", "Strategic Asset Brokers", or sender signing as "[Name] from SAB" / "[Name] - SAB"
- **Severity**: HIGH

#### RULE SPAM-02 | Opt-Out Mechanism
- **Subject**: Any lead with `total_sends` >= 3
- **Constraint**: MUST include opt-out mechanism
- **Test**: Check for soft contextual opt-out OR mechanical opt-out
- **Soft examples**: "no worries if nows not the right time", "happy to step back", "not keen? all good"
- **Note**: Soft opt-outs are PREFERRED. Mechanical opt-outs ("Reply STOP") should be flagged as STYLE ISSUE.
- **Severity**: CRITICAL (for sends >= 3)

#### RULE SPAM-03 | Frequency Advisory
- **Subject**: Any lead with `total_sends` >= 6
- **Constraint**: HIGH frequency - flag for review. Recommend extended gap.
- **Severity**: ADVISORY (warn but don't fail)

### Australian Consumer Law (ACL)

#### RULE ACL-01 | Misleading Conduct Prohibition
- **Constraint**: MUST NOT mislead about SAB's services or the finance process
- **Severity**: HIGH

#### RULE ACL-02 | Vulnerable Consumer Protection
- **Constraint**: MUST NOT use pressure tactics on potentially vulnerable leads
- **Severity**: HIGH

#### RULE ACL-03 | Pressure Tactic Prohibition
- **Constraint**: MUST NOT use guilt, fear, or FOMO-based pressure
- **Severity**: HIGH

### National Credit Code

#### RULE NCC-01 | Pre-Contract Disclosure Prohibition
- **Constraint**: MUST NOT make credit contract promises in marketing messages
- **Constraint**: MUST NOT guarantee specific loan amounts or terms
- **Severity**: HIGH

#### RULE NCC-02 | Responsible Lending Acknowledgment
- **Constraint**: Messages should acknowledge we assess suitability (implicit in saying "we'll check your situation")
- **Constraint**: MUST NOT pressure or coerce leads into credit applications
- **Severity**: MEDIUM

## Compliance Decision Logic

### Message Failure Criteria
A message FAILS compliance if ANY of these are true:
1. Contains specific interest rates or comparison rates
2. Implies guaranteed or certain approval
3. Uses unsubstantiated superlatives about rates/process
4. Creates artificial urgency on finance offers
5. Fails to identify sender (for any message)
6. Lacks opt-out for leads with total_sends >= 3
7. Uses guilt, fear, or FOMO pressure tactics
8. Misleads about SAB's services

### Preferred Opt-Out Approach
For leads with multiple sends, soft opt-outs are preferred over mechanical ones:
- "no worries if now's not the right time"
- "happy to step back if you're not keen"
- "not interested? no drama"
- These feel conversational and Australian
