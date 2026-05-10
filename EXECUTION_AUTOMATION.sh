#!/bin/bash
# Automated Execution Script for one-shot-prompting v0.6.1-v1.0.0
# Executes complete testing and release workflow
# Usage: ./EXECUTION_AUTOMATION.sh [phase]

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPTS_DIR="$PROJECT_ROOT/skills/one-shot-generator/scripts"
LOG_DIR="$PROJECT_ROOT/execution_logs"
RESULTS_DIR="$PROJECT_ROOT/test_results"

# Create directories
mkdir -p "$LOG_DIR"
mkdir -p "$RESULTS_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_DIR/execution.log"
}

log_error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1" | tee -a "$LOG_DIR/execution.log"
}

log_warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1" | tee -a "$LOG_DIR/execution.log"
}

# Phase 0: Integration Testing
phase_0_testing() {
    log_info "================================"
    log_info "PHASE 0: Integration Testing"
    log_info "================================"

    log_info "Running Phase 0 tests..."
    if python "$SCRIPTS_DIR/test_phase_0_integration.py" > "$RESULTS_DIR/phase_0.log" 2>&1; then
        log_info "✅ Phase 0 tests PASSED"
        return 0
    else
        log_error "❌ Phase 0 tests FAILED"
        cat "$RESULTS_DIR/phase_0.log"
        return 1
    fi
}

# Gap 1: Multi-File Generation Testing
gap_1_testing() {
    log_info "================================"
    log_info "GAP 1: Multi-File Testing"
    log_info "================================"

    log_info "Running Gap 1 tests..."
    if python "$SCRIPTS_DIR/test_gap_1_multifile.py" > "$RESULTS_DIR/gap_1.log" 2>&1; then
        log_info "✅ Gap 1 tests PASSED"
        return 0
    else
        log_error "❌ Gap 1 tests FAILED"
        cat "$RESULTS_DIR/gap_1.log"
        return 1
    fi
}

# Gaps 2-8: Comprehensive Testing
gaps_2_8_testing() {
    log_info "================================"
    log_info "GAPS 2-8: Comprehensive Testing"
    log_info "================================"

    log_info "Running Gaps 2-8 tests..."
    if python "$SCRIPTS_DIR/test_all_gaps.py" > "$RESULTS_DIR/gaps_2_8.log" 2>&1; then
        log_info "✅ Gaps 2-8 tests PASSED"
        return 0
    else
        log_error "❌ Gaps 2-8 tests FAILED"
        cat "$RESULTS_DIR/gaps_2_8.log"
        return 1
    fi
}

# Performance Testing
performance_testing() {
    log_info "================================"
    log_info "PERFORMANCE TESTING"
    log_info "================================"

    log_info "Running performance tests..."
    if python "$SCRIPTS_DIR/performance_test_harness.py" > "$RESULTS_DIR/performance.log" 2>&1; then
        log_info "✅ Performance tests PASSED"
        return 0
    else
        log_error "❌ Performance tests FAILED"
        cat "$RESULTS_DIR/performance.log"
        return 1
    fi
}

# Real Project Validation
validate_real_projects() {
    log_info "================================"
    log_info "REAL PROJECT VALIDATION"
    log_info "================================"

    # This would require actual project paths
    log_warning "Real project validation requires project paths"
    log_info "Usage: python scripts/validate_real_project.py /path/to/project"

    return 0
}

# Master Test Suite
run_all_tests() {
    log_info "================================"
    log_info "RUNNING MASTER TEST SUITE"
    log_info "================================"

    if python "$PROJECT_ROOT/RUN_INTEGRATION_TESTS.py" > "$RESULTS_DIR/master_tests.log" 2>&1; then
        log_info "✅ Master test suite PASSED"
        return 0
    else
        log_error "❌ Master test suite FAILED"
        cat "$RESULTS_DIR/master_tests.log"
        return 1
    fi
}

# Version Bump
bump_version() {
    local old_version=$1
    local new_version=$2

    log_info "Bumping version from $old_version to $new_version"

    # Update plugin.json
    if [ -f "$PROJECT_ROOT/.claude-plugin/plugin.json" ]; then
        sed -i "s/\"version\": \"$old_version\"/\"version\": \"$new_version\"/g" \
            "$PROJECT_ROOT/.claude-plugin/plugin.json"
        log_info "✅ Updated plugin.json"
    fi

    # Update CHANGELOG.md
    if [ -f "$PROJECT_ROOT/CHANGELOG.md" ]; then
        log_info "✅ CHANGELOG.md ready for manual update"
    fi
}

# Git Release
create_release() {
    local version=$1
    local branch="release/v$version"

    log_info "Creating release branch: $branch"

    cd "$PROJECT_ROOT"

    # Create release branch
    git checkout -b "$branch" || git checkout "$branch"

    # Commit changes
    git add -A
    git commit -m "release: v$version - Complete implementation ready for marketplace"

    # Create tag
    git tag -a "v$version" -m "Release v$version"

    log_info "✅ Release created: v$version"
    log_info "Run 'git push origin $branch' and 'git push origin v$version' to push to remote"
}

# Generate Report
generate_report() {
    log_info "Generating execution report..."

    cat > "$RESULTS_DIR/execution_report.md" << 'EOF'
# Execution Report

## Test Results Summary

EOF

    # Add Phase 0 results
    if [ -f "$RESULTS_DIR/phase_0_test_results.json" ]; then
        echo "### Phase 0" >> "$RESULTS_DIR/execution_report.md"
        cat "$RESULTS_DIR/phase_0_test_results.json" >> "$RESULTS_DIR/execution_report.md"
        echo "" >> "$RESULTS_DIR/execution_report.md"
    fi

    # Add performance results
    if [ -f "$RESULTS_DIR/performance_test_results.json" ]; then
        echo "### Performance" >> "$RESULTS_DIR/execution_report.md"
        cat "$RESULTS_DIR/performance_test_results.json" >> "$RESULTS_DIR/execution_report.md"
        echo "" >> "$RESULTS_DIR/execution_report.md"
    fi

    log_info "✅ Report generated: $RESULTS_DIR/execution_report.md"
}

# Main execution
main() {
    local phase=${1:-all}

    log_info "========================================"
    log_info "ONE-SHOT-PROMPTING EXECUTION AUTOMATION"
    log_info "========================================"

    case $phase in
        phase0)
            phase_0_testing
            ;;
        gap1)
            gap_1_testing
            ;;
        gaps2_8)
            gaps_2_8_testing
            ;;
        performance)
            performance_testing
            ;;
        projects)
            validate_real_projects
            ;;
        all)
            log_info "Running complete test suite..."
            run_all_tests
            local test_result=$?

            if [ $test_result -eq 0 ]; then
                log_info "✅ All tests PASSED"
                generate_report

                log_info ""
                log_info "✅ EXECUTION COMPLETE - READY FOR RELEASE"
                log_info ""
                log_info "Next steps:"
                log_info "1. Review results in: $RESULTS_DIR/"
                log_info "2. Create release: ./EXECUTION_AUTOMATION.sh release v0.6.1-harness"
                log_info "3. Push to marketplace"
            else
                log_error "❌ Tests FAILED - See logs for details"
                exit 1
            fi
            ;;
        release)
            local version=${2:-0.6.1-harness}
            bump_version "0.6.0" "$version"
            create_release "$version"
            ;;
        *)
            echo "Usage: $0 {phase0|gap1|gaps2_8|performance|projects|all|release [version]}"
            echo ""
            echo "Examples:"
            echo "  $0 all                    # Run all tests"
            echo "  $0 phase0                 # Run Phase 0 tests"
            echo "  $0 release v0.6.1         # Create release"
            exit 1
            ;;
    esac
}

# Run main
main "$@"
