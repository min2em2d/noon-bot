import json

log_path = r"C:\Users\3moha\.gemini\antigravity\brain\2d72dd3e-a000-482f-a448-035820c71536\.system_generated\logs\transcript_full.jsonl"

with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
    for i, line in enumerate(f):
        try:
            obj = json.loads(line)
        except Exception:
            continue
            
        step = obj.get("step_index", i)
        for tc in obj.get("tool_calls", []):
            name = tc.get("name", "")
            if name in ["write_to_file", "replace_file_content"]:
                target = tc.get("args", {}).get("TargetFile", "")
                if "noon_signup_hybrid" in target:
                    print(f"Step {step} | Tool: {name} | Target: {target}")
