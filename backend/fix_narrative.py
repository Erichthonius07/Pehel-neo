with open('app/agents/narrative_agent.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Remove duplicate import sys
content = content.replace('        import sys\n        import sys', '        import sys')

# Remove duplicate db.rollback()
content = content.replace('            db.rollback()\n            db.rollback()', '            db.rollback()')

with open('app/agents/narrative_agent.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Fixed narrative_agent.py')