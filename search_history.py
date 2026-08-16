import json
import sys

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

log_path = r"C:\Users\3moha\.gemini\antigravity\brain\2d72dd3e-a000-482f-a448-035820c71536\.system_generated/logs/transcript.jsonl"

print("Searching transcript for steps 670-720...")
with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
    for i, line in enumerate(f):
        try:
            obj = json.loads(line)
        except Exception:
            continue
            
        step = obj.get("step_index", i)
        if 670 <= step <= 720:
            type_ = obj.get("type", "")
            content = obj.get("content", "") or ""
            tool_calls = obj.get("tool_calls", [])
            
            print(f"=== Step {step} | Type: {type_} ===")
            if content:
                print("Content:", content[:300])
            for tc in tool_calls:
                name = tc.get("name", "")
                args = tc.get("args", {})
                print(f"  Tool Call: {name} -> {args.get('TargetFile', args.get('CommandLine', ''))}")
                if name in ["replace_file_content", "write_to_file"]:
                    print("  TargetContent / Replacement:")
                    print(args.get("TargetContent", "")[:200])
                    print("  --->")
                    print(args.get("ReplacementContent", args.get("CodeContent", ""))[:300])
            print("-" * 50)
