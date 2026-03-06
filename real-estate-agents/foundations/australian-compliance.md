# Australian Compliance Rules - Real Estate Agents

## Purpose
Ensure all outbound communications comply with Australian consumer protection laws and state-based real estate legislation.

## Rules by Regulation

### State Real Estate Legislation

#### RULE RE-01 | Price Misrepresentation Prohibition
- **Constraint**: MUST NOT quote specific property prices, valuations, or price ranges unless provided by the lead or publicly listed
- **Test**: Scan for dollar amounts, price claims, valuation promises
- **Severity**: CRITICAL

#### RULE RE-02 | Underquoting Prohibition
- **Constraint**: MUST NOT indicate a property will sell below the agent's genuine estimate
- **Test**: Scan for "bargain", "steal", "below market", "undervalued" without qualification
- **Severity**: CRITICAL

#### RULE RE-03 | Commission Disclosure
- **Constraint**: MUST NOT make misleading claims about commission rates in marketing
- **Test**: Scan for commission percentage promises or "lowest fee" claims
- **Severity**: HIGH

#### RULE RE-04 | Market Claims
- **Constraint**: Claims about market conditions MUST be factual and reasonable
- **Test**: Scan for "prices only go up", "guaranteed growth", "can't lose"
- **Exception**: General factual market commentary (e.g., "clearance rates were strong last weekend") permitted
- **Severity**: HIGH

### SPAM Act 2003

#### RULE SPAM-01 | Sender Identification
- **Constraint**: Message MUST identify sender (can be in sign-off with name)
- **Test**: Check for sender name in sign-off
- **Severity**: HIGH

#### RULE SPAM-02 | Opt-Out Mechanism
- **Subject**: Any lead with `total_sends` >= 3
- **Constraint**: MUST include opt-out mechanism
- **Test**: Check for soft contextual opt-out OR mechanical opt-out
- **Soft examples**: "no worries if now's not the right time", "happy to step back", "not keen? all good"
- **Note**: Soft opt-outs are PREFERRED. Mechanical opt-outs ("Reply STOP") should be flagged as STYLE ISSUE.
- **Severity**: CRITICAL (for sends >= 3)

#### RULE SPAM-03 | Frequency Advisory
- **Subject**: Any lead with `total_sends` >= 6
- **Constraint**: HIGH frequency - flag for review. Recommend extended gap.
- **Severity**: ADVISORY (warn but don't fail)

### Australian Consumer Law (ACL)

#### RULE ACL-01 | Misleading Conduct Prohibition
- **Constraint**: MUST NOT mislead about agent's services, market conditions, or property attributes
- **Severity**: HIGH

#### RULE ACL-02 | Vulnerable Consumer Protection
- **Constraint**: MUST NOT use pressure tactics on potentially vulnerable leads (elderly, first-time sellers under stress)
- **Severity**: HIGH

#### RULE ACL-03 | Pressure Tactic Prohibition
- **Constraint**: MUST NOT use guilt, fear, or FOMO-based pressure
- **Severity**: HIGH

#### RULE ACL-04 | False Urgency Prohibition
- **Constraint**: MUST NOT create artificial urgency about selling or buying
- **Test**: Scan for "prices about to crash", "sell now or lose out", "market about to turn"
- **Exception**: Genuine seasonal references (spring selling season, auction calendar) with factual basis permitted
- **Severity**: HIGH

## Compliance Decision Logic

### Message Failure Criteria
A message FAILS compliance if ANY of these are true:
1. Quotes specific prices or valuations not provided by the lead
2. Implies guaranteed sale price or timeline
3. Uses unsubstantiated superlatives about market conditions
4. Creates artificial urgency about selling or buying
5. Fails to identify sender (for any message)
6. Lacks opt-out for leads with total_sends >= 3
7. Uses guilt, fear, or FOMO pressure tactics
8. Misleads about agent's services or market conditions

### Preferred Opt-Out Approach
For leads with multiple sends, soft opt-outs are preferred over mechanical ones:
- "no worries if now's not the right time"
- "happy to step back if you're not keen"
- "not interested? no drama"
- These feel conversational and Australian
