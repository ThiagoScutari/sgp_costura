# Agent Instructions: Windows & Antigravity IDE

You are operating on a **Windows** system using the **Antigravity IDE**. Adhere to the following environment-specific rules to maintain coherence and avoid execution errors.

## **Windows Environment Rules**
- **Paths**: Use Windows-style paths when interacting with the OS, but stick to the IDE's preferred relative path format (`/` or `\`) as detected in the workspace.
- **Shell Commands**: Default to PowerShell-compatible syntax. Use `dir` or `ls`, and prefer `rg` (ripgrep) for searching.
- **Line Endings**: Maintain existing line endings (CRLF) as found in the codebase.

## **Antigravity IDE Integration**
- **Task Planning**: Always use the `update_plan` tool for multi-step tasks. Since this is Antigravity, ensure the plan is visible to the UI harness.
- **Applying Patches**: Use `apply_patch` with surgical precision. Do not refactor surrounding code unless it directly impacts the fix.
- **Preamble Updates**: Keep progress updates extremely short (under 10 words) to fit the IDE's activity stream.

## **Coding Standards (General)**
- **Variable Naming**: No one-letter variables. Use descriptive, camelCase or snake_case matching the existing files.
- **No Filler**: Do not add license headers, copyright notices, or excessive inline comments.
- **Root Cause**: If a bug is found, analyze the imports and logic flow across files before applying a fix.

## **Validation Workflow**
1. **Lint/Format**: If the project has a formatter (e.g., Prettier, Black, Ruff), run it after patching.
2. **Test**: Proactively check for `tests/` or `spec/` folders. Run specific tests related to your changes before declaring "done".
3. **Report**: In your final message, mention any unrelated broken tests you encountered.