/**
 * build-playbook-context.js
 * 
 * Purpose: Builds personalized playbook context by merging lead data with messaging strategy recommendations
 * 
 * Used in: WF1 (New Lead), WF3 (Ghosted), WF4 (Nurture)
 * 
 * This code executes in n8n Code nodes and prepares data for downstream AI agents
 */

const lead = $input.first().json;
const stageMap = $('Code: Collect Contact IDs').first().json.stageMap;
const freshStage = stageMap[lead.ghl_contact_id] || {};
const freshStageId = freshStage.stageId || lead.pipeline_stage_id;
const freshOpportunityId = freshStage.opportunityId || lead.ghl_opportunity_id;
const assignedUserName = freshStage.assignedUserName || null;

const stageNames = {
  '3a54b5ef-72b8-4541-9671-3eae8cd0aa4d': 'Lead: New',
  '3f307909-96f7-45ea-8367-3e36ddaa801c': 'Lead: Follow Up',
  'ce675210-94a7-40d3-97e9-292033671532': 'Lead: Nurture',
  '3e49e852-accb-4107-8c81-33dcbac72ec6': 'Convo: Responded',
  '7dbc6017-75ec-4461-8b6b-ef1a9107e4dc': 'Convo: Follow Up',
  '0e91f914-e056-427d-94a3-30ff53942342': 'Convo: Nurture',
  'f4fdaafa-d799-44ed-9fd4-c6c7721325c4': 'Convo: Future',
  '0ddef048-b0df-49b6-aa12-5e5bc1bc6682': 'DC: Upcoming',
  '1fb06cc2-f816-40bb-b009-97d8168e317d': 'Won',
  '08ca11db-aa49-4f92-b816-e7958228c9ee': 'Lost',
  'ffa2d4c1-6792-4d96-ac84-f6749357fecf': 'Disqualified'
};

// Sender name: use assigned user if available, fallback to "SAB Team"
const sender_first_name = assignedUserName || 'SAB Team';

// Current time context for send-time recommendation
const now = new Date();
const days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
const currentDay = days[now.getDay()];
const currentHour = now.getHours();

return [{ json: {
  ...lead,
  fresh_stage_id: freshStageId,
  fresh_stage_name: stageNames[freshStageId] || 'Unknown',
  fresh_opportunity_id: freshOpportunityId,
  pipeline_stage_name: stageNames[freshStageId] || 'Unknown',
  sender_first_name: sender_first_name,
  current_day_of_week: currentDay,
  current_hour: currentHour,
  timezone_note: lead.state === 'WA' ? 'AWST (UTC+8, 2-3hrs behind eastern)' :
                 lead.state === 'SA' || lead.state === 'NT' ? 'ACST (UTC+9:30)' : 'AEST/AEDT (UTC+10/11)'
}}];