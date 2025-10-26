# Issue Templates

This directory contains GitHub issue templates to help structure contributions and requests.

**📖 For complete usage instructions with examples, see the [GitHub Templates Usage Guide](../../docs/GITHUB_TEMPLATES_GUIDE.md)**

## Available Templates

### 🐛 Bug Report (`bug_report.md`)
Use this template to report bugs and issues you've encountered.
- Includes reproduction steps
- Environment details
- Screenshots support

### 🐛 Bug Fix Request (`bug-fix-request.yml`)
**NEW!** Comprehensive bug fix template optimized for GitHub Copilot to identify and fix bugs efficiently.
- Detailed bug description with real outputs
- Step-by-step reproduction
- Root cause analysis
- Proposed fix with test requirements
- Priority and severity levels
- Copilot-optimized workflow

### 💡 Feature Request (`feature_request.md`)
Use this template to suggest new features or improvements.
- Problem description
- Proposed solution
- Alternative considerations

### ✨ Feature Request (Enhanced) (`feature-request-enhanced.yml`)
**NEW!** Comprehensive feature request template optimized for GitHub Copilot implementation.
- Detailed user stories and acceptance criteria
- Technical requirements and API specifications
- UI/UX specifications with mockups
- Security and performance requirements
- Implementation phases and test scenarios
- Copilot-optimized workflow with 18+ sections

**When to use (Enhanced Feature Request):**
- Complex features requiring detailed specifications
- Features that need Copilot implementation assistance
- Real-time systems (WebSocket, notifications, etc.)
- Features with strict security/performance requirements
- Multi-phase implementations
- Features requiring comprehensive testing

**Key Features:**
- ✅ 18 comprehensive sections
- ✅ User story format for clarity
- ✅ API and data structure specifications
- ✅ Security and performance targets
- ✅ Phased implementation planning
- ✅ Copilot-ready format

### 🔍 System Analysis & Optimization (`system-analysis.yml`)
Comprehensive template for systematic code analysis and optimization, optimized for GitHub Copilot.

**When to use (Bug Fix Request):**
- Bugs need systematic analysis and fixing
- OAuth/authentication issues
- API integration problems
- Error handling improvements
- Production incidents
- Critical bug fixes with test coverage

**When to use (System Analysis):**
- Performance optimization needed
- Security audit required
- Code quality improvements
- Technical debt reduction
- System refactoring
- Dependency upgrades
- Integration preparation

**Key Features:**
- ✅ 17 comprehensive sections
- ✅ Structured checklists
- ✅ Measurable targets
- ✅ Real data requirements
- ✅ Copilot-optimized workflow

**Documentation:** [System Analysis Template Guide](../../docs/SYSTEM_ANALYSIS_TEMPLATE_GUIDE.md)

### ♻️ Code Refactoring (`code-refactoring.yml`)
**NEW!** Comprehensive refactoring template for systematic code quality improvements.

**When to use:**
- Code smells identified (God objects, duplicate code, tight coupling)
- Large files need decomposition (>300 lines)
- Magic numbers need extraction to constants
- Callback hell needs async/await conversion
- Technical debt reduction initiatives
- Architectural improvements

**Key Features:**
- ✅ Code smell identification
- ✅ Before/after examples
- ✅ Step-by-step refactoring plan
- ✅ Testing strategy
- ✅ Code quality metrics tracking
- ✅ Breaking changes analysis
- ✅ Rollback plan
- ✅ Copilot-optimized workflow

**Documentation:** 
- [Refactoring Guide](../../docs/REFACTORING_GUIDE.md)
- [Refactoring Examples](../../docs/REFACTORING_EXAMPLES.md)

### ✏️ Custom (`custom.md`)
For issues that don't fit other templates.

## Configuration

### Issue Chooser (`config.yml`)
The `config.yml` file configures the GitHub issue chooser interface:
- Disables blank issues to encourage use of templates
- Provides helpful links to documentation, discussions, and security reporting

## How to Use

1. Go to the [Issues](../../issues) page
2. Click "New Issue"
3. Select the appropriate template from the chooser
4. Fill out all required fields
5. Submit the issue

## Template Development

To modify or add templates:
1. Edit existing templates in this directory
2. Use `.md` format for simple templates
3. Use `.yml` format for form-based templates (recommended)
4. Test YAML syntax before committing
5. Update this README when adding new templates

## YAML Template Structure

Form-based templates (`.yml`) provide better structure:

```yaml
name: Template Name
description: Brief description
title: "[PREFIX]: "
labels: ["label1", "label2"]
assignees: []

body:
  - type: markdown
    attributes:
      value: Introduction text
      
  - type: textarea
    id: field-id
    attributes:
      label: Field Label
      description: Field description
    validations:
      required: true
```

## Best Practices

1. **Be Specific**: Provide detailed information
2. **Use Labels**: Tag issues appropriately
3. **Include Context**: Share relevant files and code
4. **Set Expectations**: Define success criteria
5. **Follow Up**: Respond to questions promptly

## Resources

- [GitHub Issue Templates Documentation](https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests)
- [YAML Syntax Guide](https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests/syntax-for-issue-forms)
- [Contributing Guidelines](../../CONTRIBUTING.md)

---

**Last Updated**: 2025-10-24
