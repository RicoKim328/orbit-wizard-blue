# Repository Guidelines

## Project Structure & Module Organization

This repository currently has no application code, tests, assets, or project manifest. As files are added, keep implementation code together in a clearly named directory such as `src/`, place automated tests in `tests/`, and keep static assets in `assets/` only when needed. Document any different layout in the root README so contributors can find the entry point quickly.

## Build, Test, and Development Commands

No build, test, or local run commands are configured yet. When introducing a toolchain, add its manifest or configuration file to the repository and record the exact setup, run, build, and test commands here and in the README. Prefer commands that work from the repository root and state required runtime versions.

## Coding Style & Naming Conventions

There is no established language style or formatter. Follow the conventions of the language and framework chosen for the first implementation, then commit formatter and linter configuration with that code. Use descriptive names, keep file naming consistent within each directory, and avoid formatting changes unrelated to the task. Document indentation and naming rules once a language is selected.

## Testing Guidelines

No test framework or coverage threshold is configured. Add focused tests for new behavior and bug fixes when testable code is introduced. Name tests after the behavior they verify, keep fixtures small, and document how to run the complete test suite. Do not claim coverage requirements until they are enforced by project tooling.

## Commit & Pull Request Guidelines

There is no Git history available here, so no existing commit convention can be inferred. Use short, imperative commit subjects that describe the change, such as `Add project setup`. Pull requests should explain the purpose, summarize key changes, include verification commands and results, and link relevant issues. Include screenshots when a change affects a visual interface.
