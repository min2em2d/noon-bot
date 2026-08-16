import json
import sys

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

log_path = r"C:\Users\3moha\.gemini\antigravity\brain\2d72dd3e-a000-482f-a448-035820c71536\.system_generated/logs/transcript.jsonl"

with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
    for line in f:
        try:
            obj = json.loads(line)
        except Exception:
            continue
            
        step = obj.get("step_index", 0)
        if step in [558, 594, 636, 680, 707]:
            for tc in obj.get("tool_calls", []):
                if tc.get("name") in ["write_to_file", "replace_file_content"]:
                    args = tc.get("args", {})
                    print(f"=== Step {step} | Tool: {tc.get('name')} ===")
                    if tc.get("name") == "write_to_file":
                        print("CodeContent:")
                        print(args.get("CodeContent", ""))
                    else:
                        print("Target:")
                        print(repr(args.get("TargetContent", "")))
                        print("Replacement:")
                        print(repr(args.get("ReplacementContent", "")))
                    print("=" * 60)
