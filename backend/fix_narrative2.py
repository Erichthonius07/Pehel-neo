with open('app/agents/narrative_agent.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Remove the second import sys and the second print line
old_block = '''        import sys
        print(f"NARRATIVE AGENT ERROR: {e}", file=sys.stderr)
        import sys
        print(f"NARRATIVE AGENT ERROR: {e}", file=sys.stderr)'''

new_block = '''        import sys
        print(f"NARRATIVE AGENT ERROR: {e}", file=sys.stderr)'''

content = content.replace(old_block, new_block)

with open('app/agents/narrative_agent.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Fixed narrative_agent.py')