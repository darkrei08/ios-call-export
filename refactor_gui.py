import re

with open("gui.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

new_lines = []
skip = False
for line in lines:
    if "def setup_theme(self):" in line:
        new_lines.append(line)
        new_lines.append("        import sv_ttk\n")
        new_lines.append(
            "        sv_ttk.set_theme('dark' if self.is_dark_mode else 'light')\n"
        )
        skip = True
        continue
    if skip and "def create_widgets(self):" in line:
        skip = False

    if skip:
        continue

    # Replace tk.Frame with ttk.Frame
    line = line.replace("tk.Frame", "ttk.Frame")
    line = line.replace("tk.Label(", "ttk.Label(")
    line = line.replace("tk.LabelFrame", "ttk.LabelFrame")
    line = line.replace("tk.Checkbutton", "ttk.Checkbutton")

    # Strip attributes
    line = re.sub(r",\s*bg=self\.[a-zA-Z_]+", "", line)
    line = re.sub(r",\s*fg=self\.[a-zA-Z_]+", "", line)
    line = re.sub(r',\s*bg=[\'"][^\'"]*[\'"]', "", line)
    line = re.sub(r',\s*fg=[\'"][^\'"]*[\'"]', "", line)
    line = re.sub(r",\s*bd=\d+", "", line)
    line = re.sub(r',\s*relief=[\'"][^\'"]*[\'"]', "", line)
    line = re.sub(r",\s*activebackground=self\.[a-zA-Z_]+", "", line)
    line = re.sub(r",\s*activeforeground=self\.[a-zA-Z_]+", "", line)
    line = re.sub(r",\s*selectcolor=self\.[a-zA-Z_]+", "", line)
    line = re.sub(r",\s*highlightbackground=self\.[a-zA-Z_]+", "", line)
    line = re.sub(r",\s*highlightcolor=self\.[a-zA-Z_]+", "", line)
    line = re.sub(r",\s*highlightthickness=\d+", "", line)
    line = re.sub(r",\s*insertbackground=self\.[a-zA-Z_]+", "", line)
    line = re.sub(r",\s*background=self\.[a-zA-Z_]+", "", line)
    line = re.sub(r",\s*foreground=self\.[a-zA-Z_]+", "", line)
    line = re.sub(r",\s*font=\(.*?\)", "", line)

    # Replace the theme toggle
    if "command=self.toggle_theme" in line:
        line = line.replace("command=self.toggle_theme", "command=self.switch_theme")

    new_lines.append(line)

content = "".join(new_lines)
# Add switch theme function
toggle_func = """
    def switch_theme(self):
        import sv_ttk
        self.is_dark_mode = not self.is_dark_mode
        sv_ttk.set_theme('dark' if self.is_dark_mode else 'light')
"""
content = content.replace(
    "def toggle_theme(self):", toggle_func + "\n    def old_toggle_theme(self):"
)
with open("gui.py", "w", encoding="utf-8") as f:
    f.write(content)
