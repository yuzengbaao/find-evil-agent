#!/usr/bin/env python3
"""
Complete demo video producer for FIND EVIL! hackathon.
Generates: terminal recordings (asciinema) + voice-over (edge-tts) + final video (ffmpeg)

Usage:
  python3 produce-demo-video.py --phase all     # Generate everything
  python3 produce-demo-video.py --phase tts      # Generate voice-over only
  python3 produce-demo-video.py --phase record   # Record terminal only
  python3 produce-demo-video.py --phase compose   # Compose final video only
"""

import argparse
import os
import subprocess
import json
from pathlib import Path
from datetime import datetime

OUTPUT_DIR = Path("/tmp/demo-video")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ============================================================
# Narration scripts (6 acts)
# ============================================================

NARRATIONS = {
    "act1-problem": (
        "DFIR analysts face a massive challenge: thousands of artifacts across "
        "disk images, memory dumps, and log files. Current AI tools suffer from "
        "three critical flaws: hallucination with fake findings, no audit trail "
        "to verify conclusions, and prompt-based constraints that can be ignored."
    ),
    "act2-architecture": (
        "We built a structurally self-correcting DFIR agent on OpenClaw that "
        "orchestrates four forensic tools: SleuthKit for filesystem analysis, "
        "YARA for signature matching, Plaso for timeline reconstruction, and "
        "Volatility3 for memory forensics. The critical difference: our constraints "
        "are architectural, not prompts. Read-only mounts enforced by the OS. "
        "Write sandboxes enforced by the filesystem. Evidence integrity enforced "
        "by SHA256 hashing."
    ),
    "act3-demo-intro": (
        "One command. The agent automatically mounts the evidence read-only, "
        "runs all applicable tools, and generates findings with complete audit trails."
    ),
    "act3-demo-result": (
        "Three independent forensic tools confirmed the same backdoor. Not 'the AI "
        "thinks there's a backdoor'. Three real tools independently agree, with "
        "SHA256 hashes proving the evidence wasn't tampered with. Every action is "
        "logged: mount decisions, tool executions with timing, findings with evidence "
        "hashes. Complete traceability from conclusion back to raw evidence."
    ),
    "act4-generalize": (
        "To prove this isn't a one-trick demo, we tested on a completely different "
        "attack scenario: ransomware. Different artifacts, different attack chain, "
        "same agent."
    ),
    "act5-results": (
        "100 percent detection, zero false positives, across two different attack "
        "scenarios. Every finding traces back to verifiable tool output with "
        "cryptographic hashes. We don't ask the AI to be careful. We build a "
        "pipeline where being careless is architecturally impossible."
    ),
    "act6-closing": (
        "DFIR doesn't need more features. It needs more trust. Our agent delivers "
        "that trust through architecture, not prompts. Thank you."
    ),
}

def generate_tts():
    """Generate all voice-over audio files."""
    print("[TTS] Generating voice-over audio...")
    voice = "en-US-GuyNeural"
    
    for name, text in NARRATIONS.items():
        out_file = OUTPUT_DIR / f"{name}.mp3"
        print(f"  Generating: {name}...")
        result = subprocess.run(
            ["edge-tts", "--text", text, "--voice", voice,
             "--write-media", str(out_file)],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            size = os.path.getsize(out_file)
            print(f"  ✅ {out_file.name} ({size/1024:.0f}KB)")
        else:
            print(f"  ❌ Failed: {result.stderr[:100]}")
    
    # Generate combined narration
    print("\n[TTS] Combining all narrations...")
    list_file = OUTPUT_DIR / "narration-list.txt"
    with open(list_file, 'w') as f:
        for name in NARRATIONS:
            path = OUTPUT_DIR / f"{name}.mp3"
            f.write(f"file '{path}'\n")
    
    combined = OUTPUT_DIR / "full-narration.mp3"
    subprocess.run(
        ["ffmpeg", "-y", "-f", "concat", "-safe", "0",
         "-i", str(list_file), "-c", "copy", str(combined)],
        capture_output=True
    )
    if combined.exists():
        print(f"  ✅ {combined.name} ({os.path.getsize(combined)/1024:.0f}KB)")
    
    return True

def generate_slides():
    """Generate static slides as PNG images."""
    print("[SLIDES] Generating static slides...")
    
    slides = {
        "slide1-problem.png": [
            "The Problem with Current AI Forensics",
            "",
            "❌ LLM Hallucination → Fake findings",
            "❌ No Audit Trail → Can't verify conclusions",
            "❌ Prompt Constraints → Can be bypassed",
        ],
        "slide2-architecture.png": [
            "Our Architecture: 4-Tool Self-Correcting Pipeline",
            "",
            "┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐",
            "│ SleuthKit│  │   YARA   │  │  Plaso   │  │ Volatil3 │",
            "│ filesystem│  │ signatures│  │ timeline │  │  memory  │",
            "└─────┬────┘  └─────┬────┘  └─────┬────┘  └─────┬────┘",
            "      └──────────────┼──────────────┼──────────────┘",
            "                     ▼              ▼",
            "          ┌─────────────────────────────┐",
            "          │  Artifact Deduplication      │",
            "          │  Cross-tool Corroboration    │",
            "          │  SHA256 Evidence Hashing     │",
            "          │  Read-only Mount Protection  │",
            "          └─────────────────────────────┘",
        ],
        "slide5-results.png": [
            "Results: Dual-Case Validation",
            "",
            "┌──────────────────┬──────────┬──────────┐",
            "│ Metric           │ TC-001   │ TC-002   │",
            "├──────────────────┼──────────┼──────────┤",
            "│ Detection Rate   │  100%    │  100%    │",
            "│ False Positives  │    0     │    0     │",
            "│ 3-Tool Corrob.   │    2     │    1     │",
            "│ Avg Confidence   │  0.85    │  0.85    │",
            "│ Audit Trail      │ Complete │ Complete │",
            "│ Evidence Hash    │  SHA256  │  SHA256  │",
            "└──────────────────┴──────────┴──────────┘",
        ],
        "slide6-closing.png": [
            "DFIR doesn't need more features. It needs more trust.",
            "",
            "github.com/yuzengbaao/find-evil-agent",
            "",
            "Built on OpenClaw + Protocol SIFT",
            "Tools: SleuthKit + YARA + Plaso + Volatility3",
        ],
    }
    
    for filename, lines in slides.items():
        out_path = OUTPUT_DIR / filename
        # Use ImageMagick convert or Python PIL
        generate_text_image(lines, out_path)
        if out_path.exists():
            print(f"  ✅ {filename}")
        else:
            print(f"  ❌ Failed: {filename}")
    
    return True

def generate_text_image(lines, output_path, width=1920, height=1080):
    """Generate a text image using Python PIL."""
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        # Fallback: use ffmpeg with drawtext
        text = "\n".join(lines)
        subprocess.run([
            "ffmpeg", "-y", "-f", "lavfi", "-i", f"color=c=black:s={width}x{height}:d=1",
            "-vf", f"drawtext=text='{text}':fontcolor=white:fontsize=36:"
                  f"x=(w-text_w)/2:y=(h-text_h)/2:fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
            "-frames:v", "1", str(output_path)
        ], capture_output=True)
        return
    
    img = Image.new('RGB', (width, height), color=(20, 20, 30))
    draw = ImageDraw.Draw(img)
    
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 28)
        title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf", 40)
    except:
        font = ImageFont.load_default()
        title_font = font
    
    y = 200
    for i, line in enumerate(lines):
        f = title_font if i == 0 else font
        color = (100, 200, 255) if i == 0 else (220, 220, 220)
        draw.text((100, y), line, fill=color, font=f)
        y += 50
    
    img.save(str(output_path))

def record_terminal():
    """Print instructions for manual terminal recording."""
    print("""
[RECORD] Terminal Recording Instructions
==========================================

Since terminal recording requires interactive input, run these commands manually:

1. Start asciinema recording:
   asciinema rec /tmp/demo-video/act3-terminal.cast

2. In the recording, run:
   cd /root/find-evil-agent
   echo "=== FIND EVIL! Demo - TC-001 ==="
   python3 scripts/agent.py --case /cases/test-case-001
   echo ""
   echo "=== Deduplicated Results ==="
   python3 scripts/deduplicate.py /cases/test-case-001/logs/forensic_audit_*.jsonl | python3 -c "
import sys, json
data = json.load(sys.stdin)
for f in data['findings']:
    corr = '  ✅' + str(f['corroboration_count']) + 'tools' if f['corroborated'] else ''
    print(f'{f[\"finding_id\"]} {f[\"severity\"]:8s} {f[\"confidence\"]} {f[\"title\"]}{corr}')
"
   echo ""
   echo "=== Audit Trail ==="
   head -5 /cases/test-case-001/logs/forensic_audit_*.jsonl

3. Press Ctrl+D to stop recording.

Repeat for TC-002 if desired.

Convert to video:
   asciinema play /tmp/demo-video/act3-terminal.cast > /dev/null &
   # Use asciinema agg or svg-term to convert
""")

def compose_video():
    """Compose final video from slides + terminal + audio."""
    print("[COMPOSE] Composing final video...")
    print("  Note: Full composition requires terminal recording first.")
    print("  Available components:")
    for f in OUTPUT_DIR.iterdir():
        print(f"    {f.name} ({f.stat().st_size/1024:.0f}KB)")
    
    # If we have slides and audio, create a slides-only video
    slides = sorted(OUTPUT_DIR.glob("slide*.png"))
    narration = OUTPUT_DIR / "full-narration.mp3"
    
    if slides and narration.exists():
        print("\n  Creating slides + narration video...")
        # Create slideshow
        list_file = OUTPUT_DIR / "slides-list.txt"
        with open(list_file, 'w') as f:
            for s in slides:
                f.write(f"file '{s}'\n")
                f.write(f"duration 15\n")  # 15 seconds per slide
        
        slideshow = OUTPUT_DIR / "slideshow.mp4"
        result = subprocess.run([
            "ffmpeg", "-y", "-f", "concat", "-safe", "0",
            "-i", str(list_file),
            "-vf", "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2:black",
            "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-r", "1",  # 1 fps for slideshow
            str(slideshow)
        ], capture_output=True, text=True)
        
        if slideshow.exists():
            print(f"  ✅ Slideshow: {slideshow.name} ({slideshow.stat().st_size/1024:.0f}KB)")
            
            # Combine with audio
            final = OUTPUT_DIR / "find-evil-demo-video.mp4"
            result2 = subprocess.run([
                "ffmpeg", "-y",
                "-i", str(slideshow),
                "-i", str(narration),
                "-c:v", "copy",
                "-c:a", "aac",
                "-shortest",
                str(final)
            ], capture_output=True, text=True)
            
            if final.exists():
                size_mb = final.stat().st_size / 1024 / 1024
                print(f"  ✅ FINAL VIDEO: {final.name} ({size_mb:.1f}MB)")
                print(f"  📂 Location: {final}")
                return True
    
    return False

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", choices=["all", "tts", "slides", "record", "compose"],
                       default="all")
    args = parser.parse_args()
    
    print(f"\n{'='*50}")
    print(f"FIND EVIL! Demo Video Producer")
    print(f"Output: {OUTPUT_DIR}")
    print(f"{'='*50}\n")
    
    if args.phase in ("all", "tts"):
        generate_tts()
    
    if args.phase in ("all", "slides"):
        generate_slides()
    
    if args.phase in ("all", "record"):
        record_terminal()
    
    if args.phase in ("all", "compose"):
        compose_video()

if __name__ == "__main__":
    main()
