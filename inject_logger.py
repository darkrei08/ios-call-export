import re

files = ["export_calls.py", "export_messages.py"]

for file in files:
    with open(file, "r", encoding="utf-8") as f:
        content = f.read()

    # Add import at the top
    if "from logger import app_logger" not in content:
        content = "from logger import app_logger\n" + content

    # Replace print(..., file=sys.stderr) with app_logger.error(...)
    content = re.sub(r"print\((.*?),?\s*file=sys\.stderr\)", r"app_logger.error(\1)", content)

    # Replace remaining print(...) with app_logger.info(...)
    content = re.sub(r"print\((.*?)\)", r"app_logger.info(\1)", content)

    with open(file, "w", encoding="utf-8") as f:
        f.write(content)

print("Injected logger")
