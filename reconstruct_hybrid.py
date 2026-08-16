import json
import sys

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

log_path = r"C:\Users\3moha\.gemini\antigravity\brain\2d72dd3e-a000-482f-a448-035820c71536\.system_generated/logs/transcript.jsonl"

print("Reconstructing exact history of noon_signup_hybrid.py before step 716...")

edits = []
with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
    for i, line in enumerate(f):
        try:
            obj = json.loads(line)
        except Exception:
            continue
            
        step = obj.get("step_index", i)
        tool_calls = obj.get("tool_calls", [])
        
        if step <= 716:
            for tc in tool_calls:
                name = tc.get("name", "")
                if name in ["write_to_file", "replace_file_content"]:
                    args = tc.get("args", {})
                    target = args.get("TargetFile", "")
                    if "noon_signup_hybrid.py" in target:
                        edits.append((step, name, args))

print(f"Total edits to noon_signup_hybrid.py before step 716: {len(edits)}")
for step, name, args in edits:
    print(f"\n================ Step {step} | Tool: {name} ================")
    if name == "write_to_file":
        code = args.get("CodeContent", "")
        print("Full Write Code length:", len(code))
        print("First 300 chars:")
        print(code[:300])
    elif name == "replace_file_content":
        tc = args.get("TargetContent", "")
        rc = args.get("ReplacementContent", "")
        print("Target Content:\n", tc[:200])
        print("---> Replacement:\n", rc[:300])
