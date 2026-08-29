# Contributing Guide

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork**:
   ```bash
   git clone https://github.com/YOUR_USERNAME/qr-code-scanner-unified.git
   cd qr-code-scanner-unified
   ```
3. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

## Development Workflow

### 1. Setup Development Environment

```bash
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
pip install pytest pytest-cov black flake8
```

### 2. Make Changes

- Write code following PEP 8 style guide
- Keep functions small and focused
- Add docstrings to all functions
- Use type hints where possible

### 3. Write Tests

Add tests for any new functionality in `tests/` directory:

```python
def test_your_new_feature():
    # Arrange
    input_data = ...
    
    # Act
    result = your_function(input_data)
    
    # Assert
    assert result == expected_output
```

Run tests:
```bash
pytest tests/ -v
```

### 4. Code Quality

**Format code:**
```bash
black shared/ desktop/ android/ tests/
```

**Lint code:**
```bash
flake8 shared/ --max-line-length=100
```

**Check coverage:**
```bash
pytest tests/ --cov=shared --cov-report=html
```

### 5. Commit Changes

```bash
git add .
git commit -m "Clear, descriptive commit message"
```

**Commit message format:**
```
[type]: Brief description

Optional detailed explanation

Types: feat, fix, docs, test, refactor, style, perf
```

Example:
```
feat: Add image file scanning capability

Implements scan_image_file() method to allow scanning
QR codes from local image files. Useful for batch
processing and testing.
```

### 6. Push and Create Pull Request

```bash
git push origin feature/your-feature-name
```

Then create a Pull Request on GitHub with:
- Clear title and description
- Reference to related issues ("Fixes #123")
- Screenshots if UI changes
- Test coverage confirmation

## Code Style Guide

### Python

```python
# Use type hints
def scan_frame(frame: np.ndarray) -> List[ScanResult]:
    """Scan a single frame for QR codes.
    
    Args:
        frame: OpenCV frame (numpy array)
    
    Returns:
        List[ScanResult]: List of detected QR codes
    """
    pass

# Use docstrings (Google style)
class MyClass:
    """Brief description.
    
    Longer description if needed.
    
    Attributes:
        attribute: Description
    """
    pass

# Constants in UPPER_CASE
MAX_FRAME_SIZE = 2048

# Private methods/attributes start with _
def _internal_helper():
    pass
```

## Project Structure

When adding new features:

```
shared/          # Core business logic
├── qr_scanner.py      # Scanning functionality
├── data_manager.py     # Persistence layer
├── config.py           # Configuration
└── __init__.py

desktop/         # Desktop UI (PyQt5)
├── qr_scanner_desktop.py
├── ui/
│   ├── main_window.py
│   ├── dialogs.py
│   └── widgets.py
└── handlers.py

android/         # Android UI (Pydroid 3)
├── qr_scanner_android.py
├── ui/
│   └── touch_interface.py
├── camera.py
└── storage.py

tests/           # Test suite
├── conftest.py   # Pytest configuration
├── test_qr_scanner.py
├── test_data_manager.py
└── test_*.py

docs/            # Documentation
├── ARCHITECTURE.md
├── SETUP.md
├── API.md
└── CONTRIBUTING.md
```

## Testing Requirements

- **New features** must include tests
- **Bug fixes** should include regression tests
- **Target coverage**: >80% for shared module
- **No external dependencies** in unit tests

Example test structure:

```python
class TestMyFeature:
    """Test suite for my feature."""
    
    def test_normal_case(self, fixture):
        """Test normal operation."""
        pass
    
    def test_edge_case(self, fixture):
        """Test edge cases."""
        pass
    
    def test_error_handling(self, fixture):
        """Test error conditions."""
        pass
```

## Documentation

Update documentation for:
- New public APIs → `docs/API.md`
- Architecture changes → `docs/ARCHITECTURE.md`
- Setup/installation changes → `docs/SETUP.md`
- Code comments for complex logic

## Issue Reporting

When reporting issues, include:
- **Steps to reproduce**
- **Expected behavior**
- **Actual behavior**
- **Environment**: OS, Python version, etc.
- **Screenshots/logs** if applicable

## Pull Request Process

1. **Pass all tests**: `pytest tests/ -v`
2. **No linting errors**: `flake8 shared/`
3. **Code formatted**: `black .`
4. **Documentation updated** for API changes
5. **Descriptive commit messages**
6. **Link to related issues**

## Release Process

1. **Update version** in `shared/__init__.py`
2. **Update CHANGELOG.md** with changes
3. **Update documentation** if needed
4. **Create release tag**: `git tag v1.0.0`
5. **Push tag**: `git push origin v1.0.0`
6. **Create GitHub release** with release notes

## Questions?

Open an issue or discussion on GitHub for help.

## Code of Conduct

Be respectful, inclusive, and constructive in all interactions.
