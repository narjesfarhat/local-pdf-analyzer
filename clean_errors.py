# clean_errors.py
INPUT = "analysis_output.txt"

with open(INPUT, "r", encoding="utf-8") as f:
    content = f.read()

# Split into page blocks
blocks = content.split("=" * 60)

clean_blocks = []
for block in blocks:
    # Keep block only if it has real content (not just an LLM error)
    if "LLM error" not in block and block.strip():
        clean_blocks.append(block)

result = ("=" * 60).join(clean_blocks)

with open(INPUT, "w", encoding="utf-8") as f:
    f.write(result)

print("Done — error pages removed from output file")
