---
description: Execute a development plan with full Archon task management integration and Git branch creation
argument-hint: [plan-file-path]
---

# Execute Development Plan with Archon Task Management

You are about to execute a comprehensive development plan with integrated Archon task management and Git branch workflow. This ensures systematic task tracking, implementation, and version control throughout the entire development process.

## Critical Requirements

**MANDATORY**: Throughout the ENTIRE execution of this plan, you MUST maintain continuous usage of Archon for task management. DO NOT drop or skip Archon integration at any point. Every task from the plan must be tracked in Archon from creation to completion.

## Step 1: Read and Parse the Plan

Read the plan file specified in: $ARGUMENTS

The plan file will contain:
- A list of tasks to implement
- References to existing codebase components and integration points
- Context about where to look in the codebase for implementation
- A feature/plan name or description

Extract the plan name/description for branch creation. This is typically found in:
- The plan filename
- A title or description section at the top of the plan
- The first heading or summary

## Step 2: Create Feature Branch

**IMPORTANT**: Run the branch creation script once and only once.

1. Run the script `.specify/scripts/bash/create-new-feature.sh --json "<plan-name-or-description>"` from repo root
   - Use the plan name/description extracted from Step 1
   - Parse the JSON output for BRANCH_NAME, SPEC_FILE, FEATURE_NUM, and HAS_GIT
   - Store these values for reference throughout execution

2. The script will:
   - Create a new numbered branch (e.g., 001-feature-name)
   - Check out the branch (if git is available)
   - Create the specs directory structure
   - Initialize the spec file

3. Confirm branch creation:
   - Report the branch name that was created
   - Note if git was available or if running in no-git mode
   - Store BRANCH_NAME for later reference

**Note**: All file paths from the script output are absolute paths. Use them as provided.

## Step 3: Project Setup in Archon

1. Check if a project ID is specified in CLAUDE.md for this feature
   - Look for any Archon project references in CLAUDE.md
   - If found, use that project ID

2. If no project exists:
   - Create a new project in Archon using `mcp__archon__manage_project`
   - Use the BRANCH_NAME or plan description as the project title
   - Store the project ID for use throughout execution

3. Consider adding the BRANCH_NAME to the project metadata for tracking

## Step 4: Create All Tasks in Archon

For EACH task identified in the plan:
1. Create a corresponding task in Archon using `mcp__archon__manage_task("create", ...)`
2. Set initial status as "todo"
3. Include detailed descriptions from the plan
4. Maintain the task order/priority from the plan

**IMPORTANT**: Create ALL tasks in Archon upfront before starting implementation. This ensures complete visibility of the work scope.

## Step 5: Codebase Analysis

Before implementation begins:
1. Analyze ALL integration points mentioned in the plan
2. Use Grep and Glob tools to:
   - Understand existing code patterns
   - Identify where changes need to be made
   - Find similar implementations for reference
3. Read all referenced files and components
4. Build a comprehensive understanding of the codebase context

## Step 6: Implementation Cycle

For EACH task in sequence:

### 6.1 Start Task
- Move the current task to "doing" status in Archon: `mcp__archon__manage_task("update", task_id=..., status="doing")`
- Use TodoWrite to track local subtasks if needed

### 6.2 Implement
- Execute the implementation based on:
  - The task requirements from the plan
  - Your codebase analysis findings
  - Best practices and existing patterns
- Make all necessary code changes
- Ensure code quality and consistency

### 6.3 Complete Task
- Once implementation is complete, move task to "review" status: `mcp__archon__manage_task("update", task_id=..., status="review")`
- DO NOT mark as "done" yet - this comes after validation

### 6.4 Proceed to Next
- Move to the next task in the list
- Repeat steps 6.1-6.3

**CRITICAL**: Only ONE task should be in "doing" status at any time. Complete each task before starting the next.

## Step 7: Validation Phase

After ALL tasks are in "review" status:

**IMPORTANT: Use the `validator` agent for comprehensive testing**
1. Launch the validator agent using the Task tool
   - Provide the validator with a detailed description of what was built
   - Include the list of features implemented and files modified
   - The validator will create simple, effective unit tests
   - It will run tests and report results

The validator agent will:
- Create focused unit tests for the main functionality
- Test critical edge cases and error handling
- Run the tests using the project's test framework
- Report what was tested and any issues found

Additional validation you should perform:
- Check for integration issues between components
- Ensure all acceptance criteria from the plan are met

## Step 8: Finalize Tasks in Archon

After successful validation:

1. For each task that has corresponding unit test coverage:
   - Move from "review" to "done" status: `mcp__archon__manage_task("update", task_id=..., status="done")`

2. For any tasks without test coverage:
   - Leave in "review" status for future attention
   - Document why they remain in review (e.g., "Awaiting integration tests")

## Step 9: Final Report

Provide a summary including:
- **Branch created**: Report the BRANCH_NAME that was created
- **Git status**: Whether git was available (HAS_GIT)
- **Total tasks**: Created and completed counts
- **Review tasks**: Any tasks remaining in review and why
- **Test coverage**: Coverage achieved by the validator
- **Key features**: Main features implemented
- **Issues**: Any issues encountered and how they were resolved
- **Next steps**: Recommendations for PR creation, code review, or additional testing

## Workflow Rules

1. **NEVER** skip Archon task management at any point
2. **RUN** the branch creation script exactly once at the beginning
3. **ALWAYS** create all tasks in Archon before starting implementation
4. **MAINTAIN** one task in "doing" status at a time
5. **VALIDATE** all work before marking tasks as "done"
6. **TRACK** progress continuously through Archon status updates
7. **ANALYZE** the codebase thoroughly before implementation
8. **TEST** everything before final completion
9. **COMMIT** regularly on the feature branch (if git is available)

## Error Handling

### Archon Failures
If at any point Archon operations fail:
1. Retry the operation
2. If persistent failures, document the issue but continue tracking locally
3. Never abandon the Archon integration - find workarounds if needed

### Branch Creation Failures
If branch creation fails:
1. Check if `.specify/scripts/bash/create-new-feature.sh` exists
2. If script is not found, create branch manually using git commands
3. Continue with execution even without branch (but note this in final report)
4. If git is not available (HAS_GIT=false), continue execution and note in final report

Remember: The success of this execution depends on maintaining systematic task management through Archon and proper version control through Git branches throughout the entire process. This ensures accountability, progress tracking, quality delivery, and clean merge workflows.