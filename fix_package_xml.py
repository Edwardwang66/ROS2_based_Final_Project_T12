#!/usr/bin/env python3
"""
Quick script to fix package.xml files - replace <n> with <name>
Run this if package.xml files have incorrect tags
"""

import os
import re

def fix_package_xml(filepath):
    """Fix <n> tags to <name> in package.xml"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Replace <n>package_name</n> with <name>package_name</name>
    content = re.sub(r'<n>([^<]+)</n>', r'<name>\1</name>', content)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Fixed: {filepath}")

# Find all package.xml files
for root, dirs, files in os.walk('src'):
    for file in files:
        if file == 'package.xml':
            filepath = os.path.join(root, file)
            fix_package_xml(filepath)

print("Done!")

