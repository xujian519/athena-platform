import ast
import os


def analyze_file(filepath):
    try:
        with open(filepath, encoding='utf-8') as f:
            content = f.read()
        tree = ast.parse(content)
        classes = [node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
        functions = [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
        imports = [node for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom))]
        try_blocks = [node for node in ast.walk(tree) if isinstance(node, ast.Try)]

        return {
            "classes": len(classes),
            "functions": len(functions),
            "imports": len(imports),
            "try_blocks": len(try_blocks),
            "loc": len(content.splitlines()),
        }
    except Exception as e:
        return {"error": str(e)}

agents_dir = ['core/agents', 'core/agent', 'core/xiaonuo_agent', 'core/agent_collaboration']
report = {}

for d in agents_dir:
    for root, _dirs, files in os.walk(d):
        for file in files:
            if file.endswith('.py') and not file.startswith('__'):
                filepath = os.path.join(root, file)
                report[filepath] = analyze_file(filepath)

total_agents = len([f for f in report if "error" not in report[f])
total_try_blocks = sum([report[f].get('try_blocks', 0) for f in report if "error" not in report[f])

print(f"Scanned {total_agents} agent files.")
print(f"Total try-except blocks: {total_try_blocks}")
print("Files with low error handling:")
for f, data in report.items():
    if "error" not in data and data.get("try_blocks", 0) == 0 and data.get("loc", 0) > 50:
        print(f"  {f} (LOC: {data['loc']})")
