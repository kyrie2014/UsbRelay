# Contributing to USB Relay Controller

First off, thank you for considering contributing to USB Relay Controller! It's people like you that make this tool better for everyone.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [How Can I Contribute?](#how-can-i-contribute)
  - [Reporting Bugs](#reporting-bugs)
  - [Suggesting Enhancements](#suggesting-enhancements)
  - [Pull Requests](#pull-requests)
- [Development Setup](#development-setup)
- [Style Guidelines](#style-guidelines)
- [Commit Messages](#commit-messages)

## Code of Conduct

This project and everyone participating in it is governed by respect and professionalism. By participating, you are expected to uphold this code.

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check the existing issues to see if the problem has already been reported. When you are creating a bug report, please include as many details as possible:

**Bug Report Template:**

```markdown
**Describe the bug**
A clear and concise description of what the bug is.

**To Reproduce**
Steps to reproduce the behavior:
1. Run command '...'
2. Connect device '...'
3. See error

**Expected behavior**
A clear and concise description of what you expected to happen.

**Environment:**
 - OS: [e.g., Windows 10]
 - Python Version: [e.g., 3.8.10]
 - Relay Model: [e.g., 4-channel USB relay]
 - Device: [e.g., Samsung Galaxy S10]

**Logs**
Please attach relevant log files from the RelayLog/ directory.

**Additional context**
Add any other context about the problem here.
```

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion, please include:

- **Use a clear and descriptive title**
- **Provide a detailed description** of the suggested enhancement
- **Explain why this enhancement would be useful** to most users
- **List some examples** of how it would work

### Pull Requests

1. Fork the repository
2. Create a new branch from `main` for your feature or bugfix
3. Make your changes
4. Write or update tests if applicable
5. Update documentation if needed
6. Submit a pull request

**Pull Request Template:**

```markdown
## Description
Brief description of what this PR does.

## Type of Change
- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update

## Testing
Describe the tests you ran to verify your changes:
- [ ] Test A
- [ ] Test B

## Checklist
- [ ] My code follows the style guidelines of this project
- [ ] I have commented my code, particularly in hard-to-understand areas
- [ ] I have updated the documentation accordingly
- [ ] My changes generate no new warnings
- [ ] I have tested my code with Python 2.7 and Python 3.x (if applicable)
```

## Development Setup

### Prerequisites

- Python 2.7 or 3.6+
- MySQL Server
- USB Relay hardware
- Windows OS (for USB DLL support)

### Setup Steps

1. **Clone your fork**
   ```bash
   git clone https://github.com/your-username/UsbRelay.git
   cd UsbRelay
   ```

2. **Create a virtual environment**
   ```bash
   # Python 3
   python -m venv venv
   venv\Scripts\activate

   # Python 2.7
   virtualenv venv
   venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure local settings**
   ```bash
   cp config.example.py config_local.py
   # Edit config_local.py with your settings
   ```

5. **Set up test database**
   ```sql
   CREATE DATABASE relay_test;
   CREATE USER 'relay_user'@'localhost' IDENTIFIED BY 'password';
   GRANT ALL PRIVILEGES ON relay_test.* TO 'relay_user'@'localhost';
   ```

6. **Run tests** (if available)
   ```bash
   python -m pytest tests/
   ```

## Style Guidelines

### Python Code Style

This project follows [PEP 8](https://www.python.org/dev/peps/pep-0008/) style guide for Python code.

**Key Points:**

- Use 4 spaces for indentation (no tabs)
- Maximum line length: 100 characters (relaxed from PEP 8's 79)
- Use meaningful variable and function names
- Add docstrings to classes and functions
- Add comments for complex logic

**Example:**

```python
def get_relay_port_states(self):
    """
    Get the current state of all relay ports.
    
    Returns:
        list: List of hex strings representing each port's state
        
    Raises:
        SerialException: If communication with relay fails
    """
    self.log.info('[BOX_STAT] - Read all relay port states')
    return self.switcher(self.frame_relay_port_states()).split(' ')[4:9]
```

### Documentation Style

- Use clear, concise language
- Provide examples where appropriate
- Keep README.md up to date
- Document all configuration options
- Include both English and Chinese documentation when possible

## Commit Messages

### Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

- **feat**: A new feature
- **fix**: A bug fix
- **docs**: Documentation only changes
- **style**: Code style changes (formatting, missing semicolons, etc.)
- **refactor**: Code refactoring without changing functionality
- **test**: Adding or updating tests
- **chore**: Maintenance tasks, dependency updates, etc.

### Examples

```
feat(relay): add support for 8-channel relay boards

- Extend protocol to support more channels
- Update configuration options
- Add detection for relay channel count

Closes #123
```

```
fix(serial): handle timeout exception properly

Previously, serial timeout would crash the server.
Now it's caught and logged appropriately.

Fixes #456
```

```
docs: update README with Python 3.9 compatibility

Add note about Python 3.9 support and update installation instructions.
```

## Testing

### Manual Testing Checklist

Before submitting a PR, please test:

- [ ] Server starts without errors
- [ ] Device binding works correctly
- [ ] ADB recovery functions as expected
- [ ] Database logging is accurate
- [ ] All log files are created properly
- [ ] Error handling works for common failure cases

### Hardware Testing

If you're making changes to hardware communication:

- Test with actual relay hardware if possible
- Document any hardware-specific requirements
- Note any compatibility issues

## Questions?

Feel free to open an issue with the `question` label if you need help or clarification on anything.

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to USB Relay Controller! 🎉

