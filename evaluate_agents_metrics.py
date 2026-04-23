import os
import ast
import json

def analyze_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        tree = ast.parse(content)
        
        has_logging = 'logging' in content or 'logger' in content
        has_print = 'print(' in content
        has_typing = 'typing' in content or 'List[' in content or 'Dict[' in content
        
        functions = [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
        async_functions = [node for node in ast.walk(tree) if isinstance(node, ast.AsyncFunctionDef)]
        
        classes = [node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
        
        hardcoded_secrets = 'api_key' in content.lower() or 'secret' in content.lower()
        
        return {
            "has_logging": has_logging,
            "has_print": has_print,
            "has_typing": has_typing,
            "sync_funcs": len(functions),
            "async_funcs": len(async_functions),
            "classes": len(classes),
            "hardcoded_secrets": hardcoded_secrets,
            "loc": len(content.splitlines()),
        }
    except Exception as e:
        return {"error": str(e)}

agents_dir = ['core/agents', 'core/agent', 'core/xiaonuo_agent', 'core/agent_collaboration']
report = {}

for d in agents_dir:
    for root, dirs, files in os.walk(d):
        for file in files:
            if file.endswith('.py') and not file.startswith('__'):
                filepath = os.path.join(root, file)
                report[filepath] = analyze_file(filepath)

issues = {
    "no_logging_uses_print": [],
    "no_typing": [],
    "all_sync_network_potential": [],
    "potential_hardcoded_secrets": [],
}

for f, data in report.items():
    if "error" in data: continue
    
    if data["has_print"] and not data["has_logging"]:
        issues["no_logging_uses_print"].append(f)
    if not data["has_typing"] and data["loc"] > 20:
        issues["no_typing"].append(f)
    if data["sync_funcs"] > 0 and data["async_funcs"] == 0 and data["loc"] > 100:
        issues["all_sync_network_potential"].append(f)
    if data["hardcoded_secrets"]:
        issues["potential_hardcoded_secrets"].append(f)

print("Agent Analysis Results:")
for issue, files in issues.items():
    print(f"\n{issue} ({len(files)} files):")
    for f in files[:10]: # Print top 10
        print(f"  - {f}")
    if len(files) > 10:
        print(f"  ... and {len(files)-10} more")

