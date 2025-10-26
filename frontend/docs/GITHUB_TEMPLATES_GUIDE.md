# GitHub Templates Usage Guide

This guide demonstrates how to use the GitHub issue and pull request templates that have been configured for this repository.

## Overview

The repository now has a complete GitHub template infrastructure consisting of:
- **Issue Chooser Configuration** - Guides users to the right template
- **5 Issue Templates** - Structured forms for different issue types
- **Pull Request Template** - Comprehensive PR submission checklist

## Using Issue Templates

### How to Create an Issue

1. Navigate to the [Issues tab](https://github.com/meraalfai-oss/ymera-frontend-/issues)
2. Click the **"New Issue"** button
3. You'll see the **Issue Chooser** interface with the following options:

#### Available Templates:

**🐛 Bug report**
- Basic bug reporting template
- Use for: Quick bug reports with reproduction steps
- Fields: Bug description, reproduction steps, expected behavior, screenshots

**🐛 Bug Fix Request** (Copilot-optimized)
- Comprehensive bug fix template
- Use for: Detailed bug reports that need systematic fixing
- Fields: Bug description, reproduction steps, actual/expected behavior, affected files, environment, root cause analysis, proposed fix, test requirements, priority, severity

**💡 Feature request**
- Feature suggestion template
- Use for: Proposing new features or improvements
- Fields: Problem description, proposed solution, alternatives considered

**🔍 System Analysis & Optimization** (Copilot-optimized)
- Comprehensive system analysis template
- Use for: Performance optimization, security audits, code quality improvements, technical debt reduction
- Fields: System description, files involved, analysis requirements, testing strategy, known issues, fixing approach, optimization targets, upgrade opportunities, integration requirements, duplicate/conflict removal, coding standards, acceptance criteria

**✏️ Custom issue template**
- Generic template for other types of issues
- Use for: Issues that don't fit the above categories

### Issue Chooser Features

At the bottom of the issue chooser, you'll find helpful links:
- **📚 Documentation** - Browse the docs folder for guides and references
- **💬 Discussions** - Ask questions in GitHub Discussions
- **🔒 Security Issues** - Report security vulnerabilities privately

**Note:** Blank issues are disabled - you must choose a template to ensure structured, high-quality issue reports.

## Using the Pull Request Template

### How to Create a Pull Request

1. Push your changes to a branch
2. Navigate to the [Pull Requests tab](https://github.com/meraalfai-oss/ymera-frontend-/pulls)
3. Click **"New Pull Request"**
4. Select your branch and click **"Create Pull Request"**
5. The PR template will automatically populate the description field

### PR Template Sections

The template includes the following sections to fill out:

#### 1. Description
Provide a clear and concise description of your changes. Explain what you changed and why.

#### 2. Related Issues
Link related issues using GitHub's keywords:
- `Fixes #123` - Closes issue #123 when PR is merged
- `Closes #456` - Same as Fixes
- `Related to #789` - References without closing

#### 3. Type of Change
Mark which type of change this PR contains:
- 🐛 Bug fix (non-breaking change which fixes an issue)
- ✨ New feature (non-breaking change which adds functionality)
- 💥 Breaking change (fix or feature that would cause existing functionality to not work as expected)
- 📚 Documentation update
- 🎨 Style/UI update
- ♻️ Code refactoring
- ⚡ Performance improvement
- ✅ Test update
- 🔧 Configuration change
- 🚀 CI/CD update

#### 4. Testing
Document your testing approach:
- **Test Coverage**: Which types of tests were added/updated
- **Test Results**: Paste test output or screenshots

#### 5. Screenshots/Videos
For UI changes, include before/after screenshots or screen recordings.

#### 6. Checklist
Complete all applicable items before requesting review:

**Code Quality** (7 items):
- Follows project style guidelines
- Self-review completed
- Code is commented where needed
- Documentation updated
- No new warnings/errors
- Debug statements removed

**Testing** (4 items):
- Tests added/updated
- All tests passing
- Cross-browser/device testing (if applicable)
- Edge cases tested

**Security** (3 items):
- No security vulnerabilities introduced
- No sensitive data exposed
- User inputs validated (if applicable)

**Performance** (3 items):
- No negative performance impact
- Load times and bundle size considered
- Assets optimized (if applicable)

**Dependencies** (3 items):
- Dependency vulnerabilities checked
- New dependencies documented
- Lock files updated

#### 7. Additional Notes
Add any context, concerns, or notes for reviewers.

#### 8. Reviewer Checklist
A checklist for reviewers to complete during the review process.

## Examples

### Example: Creating a Bug Report

1. Click "New Issue"
2. Select "🐛 Bug report"
3. Fill in the template:
   ```
   **Describe the bug**
   The login button doesn't respond when clicked on mobile devices.

   **To Reproduce**
   1. Open the app on iPhone 12
   2. Navigate to login page
   3. Tap the login button
   4. Nothing happens

   **Expected behavior**
   The login form should appear when the button is tapped.

   **Screenshots**
   [Attach screenshot of the login page]

   **Smartphone:**
   - Device: iPhone 12
   - OS: iOS 16.5
   - Browser: Safari
   - Version: Latest
   ```

### Example: Creating a Feature Request

1. Click "New Issue"
2. Select "💡 Feature request"
3. Fill in the template:
   ```
   **Is your feature request related to a problem?**
   Users have requested the ability to export their data in CSV format.

   **Describe the solution you'd like**
   Add an "Export to CSV" button on the dashboard that downloads 
   all user data in a formatted CSV file.

   **Describe alternatives you've considered**
   - JSON export
   - PDF export
   - Email the data

   **Additional context**
   This feature has been requested by 15 users in the last month.
   ```

### Example: Creating a Pull Request

When you create a PR, fill out the template like this:

```markdown
## 📝 Description
Added a CSV export feature to the dashboard that allows users to 
download their data in CSV format.

## 🔗 Related Issues
Fixes #123

## 🎯 Type of Change
- [x] ✨ New feature (non-breaking change which adds functionality)

## 🧪 Testing
### Test Coverage
- [x] Unit tests added/updated
- [x] Integration tests added/updated
- [x] Manual testing completed

### Test Results
All tests passing:
- Unit tests: 145 passed
- Integration tests: 23 passed
- CSV export feature tested with 1000+ rows

## 📸 Screenshots/Videos
**Before:**
[Screenshot of dashboard without export button]

**After:**
[Screenshot of dashboard with new "Export to CSV" button]
[Screenshot of downloaded CSV file]

## ✅ Checklist
### Code Quality
- [x] My code follows the project's style guidelines
- [x] I have performed a self-review of my code
- [x] I have commented my code, particularly in hard-to-understand areas
- [x] I have made corresponding changes to the documentation
- [x] My changes generate no new warnings or errors
- [x] I have removed any console.log() or debug statements

### Testing
- [x] I have added tests that prove my fix is effective or that my feature works
- [x] New and existing unit tests pass locally with my changes
- [x] I have tested edge cases and error scenarios

### Security
- [x] My changes don't introduce security vulnerabilities
- [x] I haven't exposed any sensitive data
- [x] I have validated all user inputs

### Performance
- [x] My changes don't negatively impact performance
- [x] I have considered the impact on load times and bundle size

### Dependencies
- [x] I have checked for dependency vulnerabilities
- [x] I have updated package-lock.json
```

## Benefits of Using Templates

### For Contributors:
- **Clear Structure**: Know exactly what information to provide
- **Reduced Back-and-Forth**: All necessary information requested upfront
- **Quality Assurance**: Built-in checklists ensure nothing is forgotten
- **Faster Acceptance**: Well-structured submissions are reviewed faster

### For Maintainers:
- **Consistent Format**: All issues and PRs follow the same structure
- **Better Information**: Templates ensure all necessary details are provided
- **Easier Triage**: Categorized issues are easier to prioritize
- **Quality Control**: Checklists ensure standards are met

### For the Project:
- **Higher Quality**: Templates encourage thorough, well-documented contributions
- **Better Documentation**: Issues and PRs serve as project documentation
- **Professional Appearance**: Structured templates show project maturity
- **Copilot-Optimized**: Special templates help GitHub Copilot provide better assistance

## Template Files Location

All template files are located in the `.github` directory:

```
.github/
├── ISSUE_TEMPLATE/
│   ├── config.yml                 # Issue chooser configuration
│   ├── README.md                  # Template documentation
│   ├── bug_report.md              # Basic bug report
│   ├── bug-fix-request.yml        # Comprehensive bug fix (Copilot-optimized)
│   ├── feature_request.md         # Feature request
│   ├── system-analysis.yml        # System analysis (Copilot-optimized)
│   └── custom.md                  # Custom issue
└── PULL_REQUEST_TEMPLATE.md       # PR template
```

## Customizing Templates

If you need to modify the templates for your workflow:

1. Edit the appropriate file in `.github/ISSUE_TEMPLATE/`
2. For YAML templates (`.yml`), validate syntax before committing
3. Test the template by creating a new issue/PR
4. Update this guide if you add new templates

## Support

If you have questions about using the templates:
- Check the [Documentation](https://github.com/meraalfai-oss/ymera-frontend-/tree/main/docs)
- Ask in [GitHub Discussions](https://github.com/meraalfai-oss/ymera-frontend-/discussions)
- Review [CONTRIBUTING.md](../CONTRIBUTING.md) for contribution guidelines

---

**Last Updated**: October 24, 2025  
**Template Version**: 1.0
