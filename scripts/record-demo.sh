#!/bin/bash
# Record terminal demo for FIND EVIL! hackathon
# Uses asciinema for terminal recording

CASE_DIR="/cases/test-case-001"
AGENT_DIR="/root/find-evil-agent"
OUTPUT_DIR="/tmp/demo-recordings"

mkdir -p "$OUTPUT_DIR"

echo "========================================="
echo "FIND EVIL! Demo Terminal Recording Script"
echo "========================================="
echo ""
echo "This script will guide you through 6 acts."
echo "Each act is recorded separately."
echo ""
echo "Press Ctrl+D or type 'exit' to end each recording."
echo ""

# Act 1: The Problem (static text, no recording needed)
echo "=== Act 1: Skip (text overlay added in post) ==="
echo ""

# Act 2: Architecture (static diagram, no recording needed)
echo "=== Act 2: Skip (diagram added in post) ==="
echo ""

# Act 3: Live Demo - TC-001
echo "=== Act 3: TC-001 Live Demo ==="
echo "Starting asciinema recording..."
echo "Run these commands in the terminal:"
echo ""
echo "  cd $AGENT_DIR"
echo "  python3 scripts/agent.py --case $CASE_DIR"
echo "  python3 scripts/deduplicate.py $CASE_DIR/logs/forensic_audit_*.jsonl"
echo "  cat $CASE_DIR/reports/agent_report.md | head -30"
echo ""
asciinema rec "$OUTPUT_DIR/act3-tc001-demo.cast"
echo ""

# Act 4: TC-002 Quick
echo "=== Act 4: TC-002 Ransomware ==="
echo "Run these commands:"
echo ""
echo "  python3 scripts/agent.py --case /cases/test-case-002"
echo "  python3 scripts/deduplicate.py /cases/test-case-002/logs/forensic_audit_*.jsonl"
echo ""
asciinema rec "$OUTPUT_DIR/act4-tc002-demo.cast"
echo ""

# Act 5: Results table (static, no recording needed)
echo "=== Act 5: Skip (table added in post) ==="

# Act 6: Closing (static, no recording needed)
echo "=== Act 6: Skip (closing added in post) ==="

echo ""
echo "========================================="
echo "Recordings saved to: $OUTPUT_DIR/"
echo "========================================="
ls -la "$OUTPUT_DIR/"
