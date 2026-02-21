# Contributing to Campus Recovery Hub

Thank you for your interest in contributing to Campus Recovery Hub! This document provides guidelines and instructions for contributing.

## Code of Conduct

Be respectful, inclusive, and professional. We welcome contributions from everyone.

## How to Contribute

### 1. Report Bugs
- Check if the bug has already been reported
- Include detailed description
- Provide steps to reproduce
- Include expected vs actual behavior
- Add screenshots if applicable

### 2. Suggest Features
- Check if feature has been suggested
- Provide clear description
- Explain use case
- Suggest possible implementation

### 3. Submit Pull Requests
- Fork the repository
- Create a feature branch (`git checkout -b feature/AmazingFeature`)
- Make your changes
- Commit with clear messages (`git commit -m 'Add AmazingFeature'`)
- Push to branch (`git push origin feature/AmazingFeature`)
- Open a Pull Request

## Development Setup

```bash
# Clone repository
git clone https://github.com/yourusername/Campus-Recovery-Hub.git
cd Campus-Recovery-Hub

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env

# Run development server
python app.py
```

## Code Standards

### Python
- Follow PEP 8 style guide
- Use meaningful variable names
- Add docstrings to functions
- Keep functions small and focused
- Add type hints when appropriate

### HTML/CSS
- Use semantic HTML5
- Follow BEM naming convention
- Keep CSS organized and documented
- Ensure responsive design

### JavaScript
- Use ES6+ features
- Add comments for complex logic
- Use consistent naming conventions
- Test in multiple browsers

## Testing

Before submitting a PR:
1. Test all features locally
2. Test on different browsers
3. Check responsive design
4. Verify error handling
5. Check security

## Commit Messages

Use clear, descriptive commit messages:
```
feat: Add user authentication
fix: Fix image upload validation
docs: Update deployment guide
style: Format code
refactor: Reorganize database module
test: Add authentication tests
```

## Pull Request Process

1. Update documentation if needed
2. Ensure no conflicts with main branch
3. Fill in PR template completely
4. Include screenshots for UI changes
5. Wait for review and address feedback

## Areas for Contribution

### High Priority
- Bug fixes
- Security improvements
- Performance optimization
- Documentation

### Medium Priority
- UI/UX improvements
- Additional features
- Database optimizations
- Testing

### Low Priority
- Code refactoring
- Minor UI tweaks
- Documentation formatting

## Questions?

- Open an issue with your question
- Check existing documentation
- Review similar issues/PRs

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for helping make Campus Recovery Hub better! 🎉
