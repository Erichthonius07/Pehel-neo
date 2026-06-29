with open('app/models/__init__.py', 'r', encoding='utf-8') as f:
    content = f.read()

old_line = '    confidence_updated_at = Column(DateTime(timezone=True))'
new_lines = '''    confidence_updated_at = Column(DateTime(timezone=True))
    confidence_label = Column(String(20))'''

content = content.replace(old_line, new_lines, 1)

with open('app/models/__init__.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Added confidence_label')