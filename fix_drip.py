path = r'c:\Users\pcgam\.gemini\antigravity\playground\dark-equinox\omniusb-farm-manager\app.py'
with open(path, 'r', encoding='utf-8', errors='ignore') as f: lines = f.readlines()

new_lines = []
skip = 0
for i, l in enumerate(lines):
    if skip > 0:
        skip -= 1
        continue
    
    if 'if hasattr(self, "youtube_drip_var") and self.youtube_drip_var.get():' in l:
        # Check if we are in the invalid lines (after line 4000)
        if i > 4000:
            # We must restore original s_sleep(1.5) with the correct indentation of the parent block.
            # The parent block indentation can be found by looking at the line before.
            prev_line = lines[i-1]
            spaces = len(prev_line) - len(prev_line.lstrip())
            new_lines.append((' ' * spaces) + 's_sleep(1.5)\n')
            skip = 5 # skip the next 5 lines of the drip block
            continue
    new_lines.append(l)

with open(path, 'w', encoding='utf-8') as f: f.writelines(new_lines)
print("Invalid drip blocks removed.")
