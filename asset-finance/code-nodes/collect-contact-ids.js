/**
 * collect-contact-ids.js
 * 
 * Purpose: Collects contact IDs from lead records for batch processing in message sending
 * 
 * Used in: WF1 (New Lead), WF3 (Ghosted), WF4 (Nurture)
 * 
 * This code executes in n8n Code nodes and prepares data for downstream AI agents
 */

const allItems = $input.all();
const stageMap = {};
for (const item of allItems) {
  const opps = item.json.opportunities || [];
  for (const opp of opps) {
    stageMap[opp.contactId] = {
      stageId: opp.pipelineStageId,
      opportunityId: opp.id,
      assignedUserName: opp.assignedTo?.name?.split(' ')[0] || opp.assignedToName?.split(' ')[0] || null
    };
  }
}
const contactIds = Object.keys(stageMap);
if (contactIds.length === 0) {
  return [{ json: { contactIds: [], stageMap: {}, contactIdsSql: "'__none__'", hasContacts: false } }];
}
return [{ json: { contactIds, stageMap, contactIdsSql: contactIds.map(id => `'${id}'`).join(','), hasContacts: true } }];