#!/usr/bin/env bash
# =============================================================================
# spawn-agents.sh — Software Factory Agent Orchestrator
#
# Usage:
#   bash scripts/spawn-agents.sh <agent> "<prompt>"
#   bash scripts/spawn-agents.sh --task <task-id>
#   bash scripts/spawn-agents.sh --process-queue
#   bash scripts/spawn-agents.sh --status
#
# Agents: director | backend | frontend | qa
# =============================================================================

set -euo pipefail

# ─── Configuration ────────────────────────────────────────────────────────────
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
AGENTS_DIR="$REPO_ROOT/agents"
SKILLS_DIR="$REPO_ROOT/skills"
MEMORY_DIR="$REPO_ROOT/memory"
TASKS_FILE="$REPO_ROOT/tasks/queue.json"
WORKTREES_DIR="$REPO_ROOT/worktrees"
LOG_DIR="$REPO_ROOT/logs"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

# Colors
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
BLUE='\033[0;34m'; CYAN='\033[0;36m'; NC='\033[0m'

# ─── Helpers ──────────────────────────────────────────────────────────────────
log()    { echo -e "${CYAN}[factory]${NC} $*"; }
success(){ echo -e "${GREEN}[✓]${NC} $*"; }
warn()   { echo -e "${YELLOW}[!]${NC} $*"; }
error()  { echo -e "${RED}[✗]${NC} $*" >&2; }
die()    { error "$*"; exit 1; }

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || die "Required command not found: $1"
}

require_cmd claude
require_cmd jq

mkdir -p "$LOG_DIR" "$WORKTREES_DIR"

# ─── Context Builders ─────────────────────────────────────────────────────────
build_context() {
  local agent="$1"
  local prompt="$2"

  local agent_def task_queue architecture decisions

  agent_def=$(cat "$AGENTS_DIR/${agent}.md" 2>/dev/null || echo "Agent definition not found: ${agent}")
  task_queue=$(cat "$TASKS_FILE" 2>/dev/null | jq '.' || echo "{}")
  architecture=$(cat "$MEMORY_DIR/architecture.md" 2>/dev/null || echo "No architecture defined yet.")
  decisions=$(cat "$MEMORY_DIR/decisions.md" 2>/dev/null || echo "No decisions recorded yet.")

  cat <<EOF
# Agent: ${agent}

## Your Role Definition
${agent_def}

## Current Task / Instruction
${prompt}

## Task Queue (tasks/queue.json)
\`\`\`json
${task_queue}
\`\`\`

## Architecture Context (memory/architecture.md)
${architecture}

## Decision Log (memory/decisions.md)
${decisions}

## Available Skills
$(find "$SKILLS_DIR" -name "*.md" | sort | sed "s|$REPO_ROOT/||")

## Instructions
- Follow your agent role definition precisely
- Use the available skills by reading the relevant skill file for guidance
- Update tasks/queue.json when task status changes
- Record any new architectural decisions in memory/decisions.md
- Output your completion report in the format specified by your agent definition
EOF
}

# ─── Spawn a single agent ─────────────────────────────────────────────────────
spawn_agent() {
  local agent="$1"
  local prompt="$2"
  local log_file="$LOG_DIR/${agent}_${TIMESTAMP}.log"

  # Validate agent
  [[ -f "$AGENTS_DIR/${agent}.md" ]] || die "Unknown agent: '${agent}'. Available: director, backend, frontend, qa"

  log "Spawning ${agent} agent..."
  log "Log: $log_file"
  echo ""

  # Build context
  local context
  context=$(build_context "$agent" "$prompt")

  # Create a worktree for isolation if git repo
  local worktree_path=""
  if git -C "$REPO_ROOT" rev-parse --git-dir >/dev/null 2>&1; then
    worktree_path="$WORKTREES_DIR/${agent}_${TIMESTAMP}"
    local branch_name="${agent}/${TIMESTAMP}"
    git -C "$REPO_ROOT" worktree add -b "$branch_name" "$worktree_path" HEAD 2>/dev/null \
      && log "Worktree created: $worktree_path (branch: $branch_name)" \
      || warn "Could not create worktree — running in main repo"
  else
    warn "Not a git repository — running without worktree isolation"
  fi

  # Spawn Claude Code
  if [[ -n "$worktree_path" ]]; then
    (cd "$worktree_path" && claude --print "$context" 2>&1 | tee "$log_file")
  else
    (cd "$REPO_ROOT" && claude --print "$context" 2>&1 | tee "$log_file")
  fi

  local exit_code=$?
  if [[ $exit_code -eq 0 ]]; then
    success "${agent} agent completed. Output in: $log_file"
  else
    error "${agent} agent exited with code $exit_code. Check: $log_file"
  fi

  return $exit_code
}

# ─── Spawn agent for a specific task ID ───────────────────────────────────────
spawn_for_task() {
  local task_id="$1"

  # Extract task from queue
  local task
  task=$(jq -r --arg id "$task_id" '.tasks[] | select(.id == $id)' "$TASKS_FILE") \
    || die "Task '$task_id' not found in queue.json"

  [[ -z "$task" ]] && die "Task '$task_id' not found in queue.json"

  local assigned_to status title description
  assigned_to=$(echo "$task" | jq -r '.assigned_to')
  status=$(echo "$task" | jq -r '.status')
  title=$(echo "$task" | jq -r '.title')
  description=$(echo "$task" | jq -r '.context.description')

  log "Task: [$task_id] $title"
  log "Assigned to: $assigned_to | Status: $status"

  if [[ "$status" == "DONE" ]]; then
    warn "Task '$task_id' is already DONE. Skipping."
    return 0
  fi

  if [[ "$status" == "CANCELLED" ]]; then
    warn "Task '$task_id' is CANCELLED. Skipping."
    return 0
  fi

  # Update status to IN_PROGRESS
  local tmp
  tmp=$(mktemp)
  jq --arg id "$task_id" \
     --arg ts "$(date -u +"%Y-%m-%dT%H:%M:%SZ")" \
     '(.tasks[] | select(.id == $id) | .status) = "IN_PROGRESS" |
      (.tasks[] | select(.id == $id) | .updated_at) = $ts' \
     "$TASKS_FILE" > "$tmp" && mv "$tmp" "$TASKS_FILE"

  local prompt
  prompt="Execute the following task from the factory queue.

Task ID: $task_id
Task JSON:
$(echo "$task" | jq '.')

Instructions:
1. Read your agent definition carefully
2. Complete the task described above
3. Use relevant skills from the skills/ directory
4. Update tasks/queue.json: set status to DONE and populate the result field
5. Report your output in the standard agent output format"

  spawn_agent "$assigned_to" "$prompt"
}

# ─── Process all PENDING tasks in queue ───────────────────────────────────────
process_queue() {
  log "Processing PENDING tasks in queue..."

  local pending_ids
  pending_ids=$(jq -r '.tasks[] | select(.status == "PENDING") | .id' "$TASKS_FILE")

  if [[ -z "$pending_ids" ]]; then
    log "No PENDING tasks found."
    return 0
  fi

  local count=0
  while IFS= read -r task_id; do
    [[ -z "$task_id" ]] && continue
    echo ""
    log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    log "Processing task: $task_id"
    log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    spawn_for_task "$task_id" || warn "Task $task_id failed — continuing to next"
    ((count++))
  done <<< "$pending_ids"

  echo ""
  success "Processed $count task(s)."
}

# ─── Status report ────────────────────────────────────────────────────────────
print_status() {
  echo ""
  log "═══════════════════════════════════════"
  log "  Software Factory — Queue Status"
  log "═══════════════════════════════════════"
  echo ""

  if [[ ! -f "$TASKS_FILE" ]]; then
    warn "tasks/queue.json not found"
    return 1
  fi

  local statuses=("PENDING" "IN_PROGRESS" "BLOCKED" "DONE" "CANCELLED")
  for status in "${statuses[@]}"; do
    local count
    count=$(jq -r --arg s "$status" '[.tasks[] | select(.status == $s)] | length' "$TASKS_FILE")
    local tasks
    tasks=$(jq -r --arg s "$status" '.tasks[] | select(.status == $s) | "  • [\(.id)] \(.title)"' "$TASKS_FILE")
    echo -e "  ${YELLOW}${status}${NC} ($count)"
    [[ -n "$tasks" ]] && echo "$tasks"
    echo ""
  done
}

# ─── Entry Point ──────────────────────────────────────────────────────────────
usage() {
  cat <<EOF
Usage:
  bash scripts/spawn-agents.sh <agent> "<prompt>"
      Spawn a specific agent with a direct prompt.
      Agents: director | backend | frontend | qa

  bash scripts/spawn-agents.sh --task <task-id>
      Spawn the assigned agent for a specific task from queue.json.

  bash scripts/spawn-agents.sh --process-queue
      Process all PENDING tasks in queue.json sequentially.

  bash scripts/spawn-agents.sh --status
      Print the current queue status.

Examples:
  bash scripts/spawn-agents.sh director "We need a user authentication system with email/password login."
  bash scripts/spawn-agents.sh backend "Implement the password reset endpoint per task backend-003."
  bash scripts/spawn-agents.sh --task backend-005
  bash scripts/spawn-agents.sh --process-queue
  bash scripts/spawn-agents.sh --status
EOF
}

main() {
  if [[ $# -eq 0 ]]; then
    usage
    exit 1
  fi

  case "$1" in
    --status)
      print_status
      ;;
    --process-queue)
      process_queue
      ;;
    --task)
      [[ $# -lt 2 ]] && die "--task requires a task ID argument"
      spawn_for_task "$2"
      ;;
    director|backend|frontend|qa)
      [[ $# -lt 2 ]] && die "Agent requires a prompt argument"
      spawn_agent "$1" "$2"
      ;;
    --help|-h)
      usage
      ;;
    *)
      error "Unknown argument: $1"
      usage
      exit 1
      ;;
  esac
}

main "$@"
