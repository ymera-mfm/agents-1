# Bug Fix Request Template Guide

## Overview

The **Bug Fix Request** template is a comprehensive, Copilot-optimized issue template designed to help GitHub Copilot efficiently identify, analyze, and fix bugs in your codebase.

## When to Use This Template

Use the Bug Fix Request template when:

- 🔴 **Production bugs** that need immediate attention
- 🔄 **Authentication/OAuth issues** that block user access
- 🌐 **API integration problems** affecting functionality
- 💥 **Critical errors** causing crashes or data loss
- 🔧 **Systematic bug fixes** requiring test coverage
- 📊 **Error handling improvements** across the system

## Template Structure

### 1. Bug Description
Provide a clear, concise description of what's broken. Be specific about:
- What feature/functionality is affected
- What component/service is involved
- When the bug occurs

**Example:**
```
The user authentication fails when using OAuth2 with Google provider, 
resulting in a TypeError when accessing user.id property.
```

### 2. 🔄 Reproduction Steps
List detailed, step-by-step instructions to reproduce the bug. This helps Copilot understand the exact scenario.

**Tips:**
- Number each step
- Include exact URLs, button names, or commands
- Mention any specific conditions (logged in/out, specific data, etc.)

**Example:**
```
1. Navigate to '/login'
2. Click 'Sign in with Google'
3. Complete Google OAuth flow in popup window
4. Observe the error message in console
```

### 3. ❌ Actual Behavior (with Real Output)
Document what actually happens with **real data**. Include:
- Console error messages (full stack traces)
- Network responses (status codes, headers, body)
- Screenshots or screen recordings
- Log files or debugging output

**Example:**
```
Error in console:
```
TypeError: Cannot read property 'id' of undefined
    at UserService.validateToken (src/services/user-service.js:45)
    at OAuthHandler.callback (src/auth/oauth-handler.js:89)
```

Network Response:
Status: 500
Body: {"error": "Internal Server Error"}
```

### 4. ✅ Expected Behavior
Describe what **should** happen instead. Be specific about:
- Successful outcomes
- Redirects or navigation
- Data that should be created/updated
- Response codes and formats

**Example:**
```
User should be:
1. Successfully authenticated with Google OAuth
2. Redirected to dashboard at '/dashboard'
3. User session created with valid JWT token
4. Response: 200 OK with complete user object
```

### 5. 📁 Affected Files
List all files involved in the bug. Include:
- File paths (absolute or relative to project root)
- Specific line numbers if known
- Related configuration files

**Example:**
```
- `src/auth/oauth-handler.js` (lines 85-95)
- `src/services/user-service.js` (lines 40-50)
- `src/middleware/token-validator.js`
- `config/oauth-providers.json`
```

### 6. 🖥️ Environment
Specify where the bug occurs:
- Operating System
- Browser and version
- Node.js version
- Package/app version
- Environment (Development/Staging/Production)

This helps Copilot understand if the bug is environment-specific.

### 7. 🔍 Root Cause Analysis (Optional)
If you've already investigated, share your findings:
- What's causing the bug
- Why the current code fails
- What assumptions were incorrect

This accelerates Copilot's analysis and fix implementation.

**Example:**
```
The OAuth callback handler expects `user.id` field but Google OAuth 
returns `user.sub` instead. The code doesn't have a mapping layer to 
handle provider-specific differences.
```

### 8. 💡 Proposed Fix
List potential solutions as a checklist. This guides Copilot's approach:

**Example:**
```
- [ ] Add mapping layer for OAuth provider differences
- [ ] Update user service to handle both 'id' and 'sub' fields
- [ ] Add validation for OAuth response structure
- [ ] Include error handling for missing required fields
- [ ] Add tests for different OAuth providers
```

### 9. 🧪 Test Requirements
Define what tests are needed to verify the fix:

**Example:**
```
- [ ] Unit test for OAuth response mapping
- [ ] Integration test for Google OAuth flow
- [ ] Error case: Invalid OAuth response
- [ ] Error case: Missing user identifier
- [ ] Test with real OAuth provider (sandbox)
```

### 10. Priority & Severity
Select appropriate priority and severity levels:

**Priority:**
- 🔴 Critical - Blocking production
- 🟠 High - Major functionality broken
- 🟡 Medium - Workaround available
- 🟢 Low - Minor issue

**Severity:**
- 💥 Crash/Data Loss
- ⛔ Major Feature Broken
- ⚠️ Minor Feature Broken
- 📝 Cosmetic/UI Issue

### 11. 📚 Additional Context
Include any other relevant information:
- When the bug started occurring
- Related PRs or issues
- Previous attempts to fix
- Business impact
- Affected users count

## Best Practices

### For Maximum Copilot Effectiveness:

1. **Be Specific**: Provide exact file paths, line numbers, and error messages
2. **Include Real Data**: Use actual error logs, not hypothetical examples
3. **Show, Don't Tell**: Include screenshots, logs, and code snippets
4. **Context Matters**: Explain when the bug started and what changed
5. **Think Systematically**: Break down complex bugs into smaller pieces

### Common Mistakes to Avoid:

❌ **Don't:**
- Use vague descriptions like "login doesn't work"
- Skip reproduction steps
- Omit error messages or stack traces
- Leave file paths ambiguous
- Forget to specify the environment

✅ **Do:**
- Provide detailed, actionable information
- Include complete error messages with stack traces
- Specify exact file paths and line numbers
- Describe the environment thoroughly
- Add any relevant context or history

## Examples

### Good Bug Report:

```markdown
## Bug Description
User authentication fails with TypeError when using Google OAuth2 provider.

## Reproduction Steps
1. Navigate to https://app.example.com/login
2. Click "Sign in with Google" button
3. Complete OAuth flow in Google popup
4. Get redirected back to app
5. See error: "Cannot read property 'id' of undefined"

## Actual Behavior
Console error:
```
TypeError: Cannot read property 'id' of undefined
    at UserService.validateToken (src/services/user-service.js:45)
```

Network: POST /api/auth/callback - Status 500
```

### Bad Bug Report:

```markdown
## Bug Description
Login doesn't work

## Reproduction Steps
Try to login with Google

## Actual Behavior
It shows an error
```

## Integration with Development Workflow

1. **Create Issue**: Use the Bug Fix Request template
2. **Copilot Analysis**: Copilot analyzes the bug using provided information
3. **Fix Implementation**: Copilot implements fix based on proposed solution
4. **Test Coverage**: Copilot adds tests per test requirements
5. **Validation**: Run tests and verify fix resolves the issue
6. **Documentation**: Update docs if needed
7. **Close Issue**: Mark as resolved with details

## Related Resources

- [System Analysis Template](./SYSTEM_ANALYSIS_TEMPLATE_GUIDE.md)
- [Contributing Guidelines](../CONTRIBUTING.md)
- [GitHub Issue Templates Docs](https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests)

## Support

For questions or improvements to this template:
- Open an issue with label `template-improvement`
- Reference this guide in your issue
- Suggest specific improvements

---

**Last Updated**: 2025-10-24  
**Template Version**: 1.0.0
