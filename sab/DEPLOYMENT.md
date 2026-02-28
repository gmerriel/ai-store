# Deployment Guide: How to Use These Skills in n8n

This document explains how to connect the SAB AI Skills repository to your n8n workflows.

## Overview

Instead of storing system messages directly in n8n AI Agent nodes, we point them to files in this GitHub repository. This allows:

1. **Version Control**: All changes tracked in Git
2. **Reusability**: Foundations can be shared across multiple roles
3. **Rapid Updates**: Change one file, affects all agents that use it
4. **Compliance Audits**: Clear history of what changed and when
5. **Easy Rollback**: Revert to previous version if something breaks

## Setup Instructions

### Step 1: Push This Repository to GitHub

1. Create a new GitHub repository called `sab-ai-skills` in your organization
2. Push this folder to that repository:
   ```bash
   cd /sessions/busy-gifted-dijkstra/mnt/outputs/sab-ai-skills
   git init
   git add .
   git commit -m "initial: decompose n8n system messages into modular skills"
   git remote add origin https://github.com/[owner]/sab-ai-skills.git
   git push -u origin main
   ```

### Step 2: Configure n8n AI Agent Nodes

For each AI Agent node in n8n, update it to use the GitHub raw content URL:

**Example: WF1 Copywriter Node**

Current configuration (in n8n):
```
Node Type: AI Agent
Provider: OpenAI
System Message: [large text block directly in n8n]
```

New configuration:
```
Node Type: AI Agent
Provider: OpenAI
System Message Source: https://raw.githubusercontent.com/[owner]/sab-ai-skills/main/assembled/wf1-copywriter.md
```

**All 15 AI Agent nodes:**

| Workflow | Node Name | GitHub URL |
|----------|-----------|-----------|
| WF1 | Lead Analyst | `https://raw.githubusercontent.com/[owner]/sab-ai-skills/main/assembled/wf1-lead-analyst.md` |
| WF1 | Copywriter | `https://raw.githubusercontent.com/[owner]/sab-ai-skills/main/assembled/wf1-copywriter.md` |
| WF1 | Compliance | `https://raw.githubusercontent.com/[owner]/sab-ai-skills/main/assembled/wf1-compliance.md` |
| WF1 | Rewriter | `https://raw.githubusercontent.com/[owner]/sab-ai-skills/main/assembled/wf1-rewriter.md` |
| WF2 | Reply Classifier | `https://raw.githubusercontent.com/[owner]/sab-ai-skills/main/assembled/wf2-reply-classifier.md` |
| WF2 | Response Drafter | `https://raw.githubusercontent.com/[owner]/sab-ai-skills/main/assembled/wf2-response-drafter.md` |
| WF3 | Lead Analyst | `https://raw.githubusercontent.com/[owner]/sab-ai-skills/main/assembled/wf3-lead-analyst.md` |
| WF3 | Copywriter | `https://raw.githubusercontent.com/[owner]/sab-ai-skills/main/assembled/wf3-copywriter.md` |
| WF3 | Compliance | `https://raw.githubusercontent.com/[owner]/sab-ai-skills/main/assembled/wf3-compliance.md` |
| WF3 | Rewriter | `https://raw.githubusercontent.com/[owner]/sab-ai-skills/main/assembled/wf3-rewriter.md` |
| WF4 | Lead Analyst | `https://raw.githubusercontent.com/[owner]/sab-ai-skills/main/assembled/wf4-lead-analyst.md` |
| WF4 | Copywriter | `https://raw.githubusercontent.com/[owner]/sab-ai-skills/main/assembled/wf4-copywriter.md` |
| WF4 | Compliance | `https://raw.githubusercontent.com/[owner]/sab-ai-skills/main/assembled/wf4-compliance.md` |
| WF4 | Rewriter | `https://raw.githubusercontent.com/[owner]/sab-ai-skills/main/assembled/wf4-rewriter.md` |
| WF5 | Weekly Analyst | `https://raw.githubusercontent.com/[owner]/sab-ai-skills/main/assembled/wf5-weekly-analyst.md` |

### Step 3: Test in Sandbox

Before deploying to production:

1. In n8n, create a test workflow that copies WF1
2. Point the Copywriter node to: `https://raw.githubusercontent.com/[owner]/sab-ai-skills/main/assembled/wf1-copywriter.md`
3. Run the test with a sample lead
4. Verify the output looks correct
5. If good, update production WF1 to use the GitHub URL

## How Updates Work

### Scenario: You discover a compliance issue

1. **Fix the foundation**: Edit `foundations/australian-compliance.md`
2. **Commit to Git**: `git commit -m "compliance: fix ASIC-01 rule wording"`
3. **Push to GitHub**: `git push`
4. **n8n automatically fetches the latest**: Next time the workflow runs, it reads the updated version from GitHub
5. **No need to manually update n8n**: The change deploys instantly

### Scenario: You want to test a change without affecting production

1. **Create a feature branch**: `git checkout -b feature/test-new-angle`
2. **Make your changes** to foundations/roles
3. **Re-assemble the files** (if needed)
4. **In n8n, point test node to your branch URL**: `https://raw.githubusercontent.com/[owner]/sab-ai-skills/main/feature/test-new-angle/assembled/wf1-copywriter.md`
5. **Test the change** in a limited way
6. **If good, merge to main**: `git merge feature/test-new-angle`
7. **If bad, delete the branch**: `git branch -D feature/test-new-angle`

## Caching Considerations

GitHub raw content URLs are typically cached. If you need n8n to immediately fetch the latest version:

1. **Clear n8n cache** (if applicable to your n8n version)
2. **Add a query parameter** to force fresh fetch: `?v=` + timestamp
   ```
   https://raw.githubusercontent.com/[owner]/sab-ai-skills/main/assembled/wf1-copywriter.md?v=1709024800
   ```
3. **Or** use GitHub's CDN bust by adding random parameter:
   ```
   https://raw.githubusercontent.com/[owner]/sab-ai-skills/main/assembled/wf1-copywriter.md?cache_bust=20260228
   ```

## Authentication

If your repository is private:

1. **Create a GitHub Personal Access Token** (Settings > Developer Settings > Personal Access Tokens)
2. **Give it `repo` scope** (read-only access to repository)
3. **Use it in the URL**:
   ```
   https://[TOKEN]@raw.githubusercontent.com/[owner]/sab-ai-skills/main/assembled/wf1-copywriter.md
   ```
4. **Or** store the token in n8n's secure credentials and reference it

## Troubleshooting

### Issue: n8n is still using the old message

**Solution**: 
- Verify the URL is correct in the AI Agent node
- Check that you pushed the changes to GitHub
- Wait 5 minutes for GitHub CDN to refresh
- If still not working, add `?cache_bust=` with current timestamp

### Issue: n8n can't fetch the URL

**Solution**:
- Verify the URL is accessible from n8n's environment
- Check that the repository is public (or credentials are set up)
- Check GitHub status page (github.com/status)
- Test the URL directly in a browser

### Issue: The assembled file is incomplete

**Solution**:
- Check that all foundations and roles are present in the repo
- Verify the assembled file was re-generated after updates
- Check file permissions (should be readable)
- Manually verify the file in GitHub web UI

## Monitoring & Auditing

### Track Changes

```bash
# See recent changes to assembled files
git log --oneline assembled/

# See all changes to a specific foundation
git log --oneline foundations/natural-typing.md

# See who changed what and when
git log -p assembled/wf1-copywriter.md | head -100

# See differences between versions
git diff [commit1] [commit2] assembled/wf1-copywriter.md
```

### Set Up Alerts

Configure GitHub to notify you when:
- Changes are pushed to `main` branch
- Changes affect `foundations/` or `assembled/`
- Pull requests are created

## Disaster Recovery

### If Something Breaks in Production

1. **Identify the problematic commit**: Review recent changes to the affected assembled file
2. **Revert the change**:
   ```bash
   git log --oneline assembled/wf1-copywriter.md  # Find bad commit hash
   git revert [bad-commit-hash]
   git push
   ```
3. **n8n will fetch the reverted version** on next run
4. **Monitor the workflow** to confirm it's fixed

### Complete Rollback

If you need to go back to the original system messages:

1. This entire repository represents the CURRENT production state
2. If you need to revert everything to before this decomposition, you'd need to store the original monolithic messages somewhere
3. Recommendation: Keep a backup branch `original-monolithic` with the old n8n exports for reference

## Performance Notes

- **Fetching from GitHub**: <100ms typically (cached by CDN)
- **No local caching overhead**: n8n fetches on every workflow execution
- **If concerned about latency**: Test with a sample workflow to measure actual impact

## Best Practices

1. **Always test in sandbox first** before deploying to production
2. **Keep commits focused**: One concern per commit
3. **Use descriptive commit messages**: Future you will thank you
4. **Review changes in context**: How will this affect lead engagement?
5. **Get approval for compliance changes**: Before pushing to main
6. **Monitor response rates**: Track if changes improve or degrade engagement

## Next Steps

1. Push this repository to GitHub
2. Update all 15 AI Agent nodes in n8n to use GitHub URLs (start with WF1 in sandbox)
3. Test with a few sample leads
4. Once confident, roll out to remaining workflows (WF2, WF3, WF4, WF5)
5. Start using Git workflow for future changes

---

**Last Updated**: 2026-02-28
**Repository**: https://github.com/[owner]/sab-ai-skills
