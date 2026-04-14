# Python Best Practices for this Project

This document outlines the recommended best practices for Python development within this project. Adhering to these guidelines ensures code quality, maintainability, and consistency.

## 1. Typing (Type Hints)

All new Python code should utilize type hints (PEP 484) for function arguments, return values, and variables. This improves code readability, enables static analysis, and helps catch errors early. Prefer native types (like rather dict instead of Dict)

**Example:**

```python
def calculate_sum(a: int, b: int) -> int:
    """Calculates the sum of two integers."""
    return a + b

class User:
    def __init__(self, name: str, age: int):
        self.name = name
        self.age = age
```

Run `mypy` regularly to check type consistency:
```bash
python -m mypy src/
```

## 2. Pytest for Testing

`pytest` is the preferred testing framework. Write comprehensive unit and integration tests for all new features and bug fixes.

*   Place test files in the `tests/` directory.
*   Name test files `test_*.py` or `*_test.py`.
*   Name test functions `test_*`.
*   Use `assert` statements for assertions.

**Example (`tests/test_example.py`):**

```python
import pytest
from src.wichteln.main import some_function # Example import

def test_some_function_returns_expected_value():
    assert some_function(2, 3) == 5

def test_some_function_handles_negative_numbers():
    assert some_function(-1, 1) == 0
```

Run tests using:
```bash
pytest
```

## 3. `uv` as Package Manager

`uv` is used for dependency management. Use `uv` for installing, updating, and managing project dependencies.

*   Add a new dependency:
    ```bash
    uv add <package-name>
    ```
*   Sync dependencies with `uv.lock`:
    ```bash
    uv sync
    ```

## 4. Design Principles

Writing clean, maintainable, and scalable code requires adherence to established design principles. These principles help manage complexity, reduce coupling, and improve the overall structure of the software. This project emphasizes two core sets of principles: SOLID and DRY.

### SOLID Principles

SOLID is a mnemonic acronym for five design principles intended to make software designs more understandable, flexible, and maintainable.

*   **S - Single-Responsibility Principle:** A class should have only one reason to change, meaning it should have only one job.
*   **O - Open-Closed Principle:** Software entities (classes, modules, functions) should be open for extension but closed for modification.
*   **L - Liskov Substitution Principle:** Subtypes must be substitutable for their base types without altering the correctness of the program.
*   **I - Interface Segregation Principle:** No client should be forced to depend on methods it does not use. Prefer smaller, more specific interfaces over large, general-purpose ones.
*   **D - Dependency Inversion Principle:** High-level modules should not depend on low-level modules. Both should depend on abstractions. Abstractions should not depend on details; details should depend on abstractions. (e.g., use Dependency Injection).

### DRY (Don't Repeat Yourself) Principle

Avoid duplicating code. If you find yourself writing the same logic more than once, abstract it into a reusable function, class, or module.

*   **Functions/Methods:** Encapsulate common operations.
*   **Classes:** Use inheritance or composition for shared behavior.
*   **Utility Modules:** Create modules for common helper functions.

## 5. Docstrings

All modules, classes, methods, and functions should have clear and concise docstrings (PEP 257). Use reStructuredText or Google style for formatting.

**Example (Google Style):**

```python
def greet(name: str) -> str:
    """Greets a person by their name.

    Args:
        name: The name of the person to greet.

    Returns:
        A greeting string.
    """
    return f"Hello, {name}!"


class Calculator:
    """A simple calculator class.

    Attributes:
        history: A list of operations performed.
    """
    def __init__(self):
        self.history = []

    def add(self, a: float, b: float) -> float:
        """Adds two numbers.

        Args:
            a: The first number.
            b: The second number.

        Returns:
            The sum of a and b.
        """
        result = a + b
        self.history.append(f"{a} + {b} = {result}")
        return result
```

## 6. Adhere to the Zen of Python

- Beautiful is better than ugly.
- Explicit is better than implicit.
- Simple is better than complex.
- Complex is better than complicated.
- Flat is better than nested.
- Sparse is better than dense.
- Readability counts.
- Special cases aren't special enough to break the rules.
- Although practicality beats purity.
- Errors should never pass silently.
- Unless explicitly silenced.
- In the face of ambiguity, refuse the temptation to guess.
- There should be one-- and preferably only one --obvious way to do it.
- Although that way may not be obvious at first unless you're Dutch.
- Now is better than never.
- Although never is often better than *right* now.
- If the implementation is hard to explain, it's a bad idea.
- If the implementation is easy to explain, it may be a good idea.
- Namespaces are one honking great idea -- let's do more of those!

## 7. Linting and Formatting

This project uses `ruff` for code linting and formatting to ensure a consistent style (PEP 8) and catch common errors.

*   **Linting:** Check for code quality issues:
    ```bash
    uv run ruff check .
    ```
*   **Formatting:** Automatically format your code:
    ```bash
    uv run ruff format .
    ```

## 8. Pre-commit Hooks

This project uses pre-commit hooks to automatically run quality checks before each commit. This ensures that no-unlinted or unformatted code is committed.

*   **Installation:** Enable the hooks in your local repository:
    ```bash
    pre-commit install
    ```
After installation, the defined hooks will run automatically on `git commit`.

## 9. Security Scanning

Use `bandit` to find common security vulnerabilities in the codebase.

*   **Run a scan:**
    ```bash
    bandit -r .
    ```
*   **Generate a report:** For a detailed report, you can output the results to a file.
    ```bash
    bandit -r . -o bandit-report.json -f json
    ```

# Node.js Best Practices for this Project

This section outlines the recommended best practices for Node.js development within this project.

## 1. Package Manager

Use `npm` for managing dependencies. The `package-lock.json` file ensures that the dependency tree is consistent across all environments.

*   **Install dependencies:**
    ```bash
    npm install
    ```
*   **Add a new dependency:**
    ```bash
    npm install <package-name>
    ```
*   **Add a new development dependency:**
    ```bash
    npm install <package-name> --save-dev
    ```

## 2. Testing

This project uses `vitest` for testing.

*   **Run tests:**
    ```bash
    npm test
    ```
*   Write tests for all new features and bug fixes.
*   Test files should be located alongside the source files with a `.test.js` extension.

## 3. Linting and Formatting

Consistent code style is crucial for readability and maintainability. This project should use `ESLint` for linting and `Prettier` for formatting.

*   **Installation:**
    ```bash
    npm install eslint prettier eslint-config-prettier eslint-plugin-prettier --save-dev
    ```
*   **Configuration:** Create `.eslintrc.cjs` and `.prettierrc.json` files.
*   **Run linting:**
    ```bash
    npx eslint .
    ```
*   **Run formatting:**
    ```bash
    npx prettier --write .
    ```

## 4. Security

Regularly check for vulnerabilities in your dependencies.

*   **Run a security audit:**
    ```bash
    npm audit
    ```
*   **Fix vulnerabilities:**
    ```bash
    npm audit fix
    ```

## 5. Development and Build

This project uses `Vite` for the development server and build process.

*   **Start the development server:**
    ```bash
    npm run dev
    ```
*   **Build for production:**
    ```bash
    npm run build
    ```

## 6. ES Modules

This project uses ES Modules (`"type": "module"` in `package.json`). Use `import` and `export` statements.
