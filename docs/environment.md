# SIFT DFIR Environment — Tool Inventory

**Server**: CloudCone VPS, 142.171.227.166, Ubuntu 22.04
**Date**: 2026-05-02

## Installed Tools

| Tool | Version | Path | Status |
|------|---------|------|--------|
| SleuthKit | 4.11.1 | `/usr/bin/fls`, `icat`, `mmls`, `mactime`, `blkls`, `istat`, `fsstat` | ✅ |
| YARA | 4.1.3 | `/usr/bin/yara`, `/usr/bin/yarac` | ✅ |
| EWF Tools | - | `/usr/bin/ewfmount`, `ewfinfo`, `ewfverify` | ✅ |
| Volatility 3 | 2.28.0 | `/usr/local/bin/vol` | ✅ |
| Plaso | - | - | ⬜ 跳过(编译依赖) |
| Python | 3.10.12 | `/usr/bin/python3` | ✅ |

## Volatility 3 Plugins (available)

```bash
# List all Windows plugins
vol --plugins -f /dev/null 2>/dev/null | grep windows | head -20

# Key plugins for DFIR:
# windows.pstree      - Process tree
# windows.psscan      - Process scan (incl. hidden)
# windows.cmdline     - Command lines
# windows.netstat     - Network connections
# windows.dlllist     - DLL list
# windows.filescan    - File scan
# windows.registry    - Registry access
# windows.malfind     - Find injected code
```

## SleuthKit Quick Reference

```bash
# List files in image
fls -r -m body /mnt/evidence/ewf1 > body.txt

# Generate timeline
mactime -b body.txt > timeline.csv

# Extract file by inode
icat /mnt/evidence/ewf1 <inode> > extracted_file

# Partition table
mmls /mnt/evidence/ewf1
```

## YARA Quick Reference

```bash
# Scan directory
yara -r rules.yar /cases/

# Compile rules
yarac rules.yar compiled_rules
```

## EWF Tools Quick Reference

```bash
# Mount E01 (read-only)
ewfmount evidence.E01 /mnt/ewf
mount -o ro,loop,noatime /mnt/ewf/ewf1 /mnt/evidence

# Verify integrity
ewfverify evidence.E01

# Image info
ewfinfo evidence.E01
```
