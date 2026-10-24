# Lab 3 — Maintainable Python Service

A CSC10014 project focused on refactoring a monolithic Python script into a modular, testable, and maintainable **Smart Virtual Assistant** named `assistant_core`.

## Team Members

| No. | Full Name               | GitHub                                                             | Student ID |
| :-: | ----------------------- | ------------------------------------------------------------------ | :--------: |
|  1  | Châu Hòa Phát           | [@chp0703](https://github.com/chp0703)                             |  25127224  |
|  2  | Huỳnh Nguyễn Thế Hiển   | [@AIVIETNAM-AIO-TheHien](https://github.com/AIVIETNAM-AIO-TheHien) |  25127327  |
|  3  | Phạm Hùng Khôi          | [@phkhoiit-1508](https://github.com/phkhoiit-1508)                 |  25127390  |
|  4  | Nguyễn Trần Minh Khang  | [@kentlatoi](https://github.com/kentlatoi)                         |  25127369  |
|  5  | Nguyễn Ngọc Thanh Hương | [@thanhhuong107](https://github.com/thanhhuong107)                 |  25127197  |
|  6  | Đặng Minh Hùng          | [@dmh612](https://github.com/dmh612)                               |  25127340  |

## Key Features

- Modular architecture with clear responsibilities.
- Environment-based configuration and secret protection.
- Typed data models and meaningful exceptions.
- Office and handbook data retrieval.
- Deterministic tuition calculations.
- Template-based responses and fallback handling.
- Automated testing and code quality checks.

## Technology Stack

Python 3.10+, Pydantic, python-dotenv, pytest, Ruff, and setuptools.

## Project Structure

```text
lab3-team3/
├── .github/
│   └── workflows/                 # GitHub Actions workflows
│
├── lab03/
│   ├── monolith/
│   │   ├── assistant_monolith.py  # Original application
│   │   └── data/
│   │       ├── offices.csv
│   │       └── handbook.json
│   └── worksheets/
│       ├── before_after_maintainability.md
│       └── ai_extension_review.md
│
├── assistant_core_lab/             #Official Submission
│   ├── pyproject.toml
│   ├── requirements.txt
│   ├── .env.example
│   ├── .gitignore
│   ├── data/
│   │   ├── offices.csv
│   │   └── handbook.json
│   ├── docs/
│   │   ├── architecture.md
│   │   ├── ai-use-log.md
│   │   └── lab3/
│   │       ├── models_erroes.md
│   │       └── members/
│   │           └── chp0703/
│   │               ├── before_after.md
│   │               └── ai_extension_review.md
│   ├── src/
│   │   └── assistant_core/
│   │       ├── __init__.py
│   │       ├── __main__.py
│   │       ├── config.py
│   │       ├── errors.py
│   │       ├── models.py
│   │       ├── router.py
│   │       ├── knowledge.py
│   │       ├── tools.py
│   │       ├── responder.py
│   │       ├── service.py
│   │       └── logging_setup.py
│   └── tests/
│       ├── conftest.py
│       └──...
│
│
│
├── .gitignore
├── pyrightconfig.json
└── README.md
```

## Setup and Testing

```bash
git clone https://github.com/chp0703/lab3-team3.git
cd lab3-team3/assistant_core_lab
python -m venv .venv
python -m pip install -r requirements.txt
python -m pip install -e .
python -m pytest -v
ruff check .
```

## Development Workflow

Team members use GitHub Issues, dedicated branches, Pull Requests, peer reviews, and automated tests to manage contributions.

Individual deliverables include the maintainability worksheet and AI extension review. Team deliverables include the integrated `assistant_core` package and architecture documentation.

**Course:** CSC10014 — Practical Track, Lab 3  
**Institution:** University of Science, VNU-HCM
