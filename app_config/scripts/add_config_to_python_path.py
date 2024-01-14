import os
import site
from pathlib import Path

# see https://python-forum.io/thread-32255.html for explanation

def escape_path_str(path):
    escaped_path = str(path).replace('\\', '\\\\')
    escaped_path = escaped_path.replace('c:', 'C:')
    return escaped_path

config_parent_path = Path(__file__).parent.parent.parent
escaped_config_parent_dir = escape_path_str(config_parent_path)
user_site_packages_dir = site.getusersitepackages()
os.makedirs(user_site_packages_dir, exist_ok=True)

customize_script_path = user_site_packages_dir + '/usercustomize.py'

script_header = "# SOSO: add config to path"
script_footer = '# SOSO: end add config to path'

script = f"""
{script_header}
import sys
path = '{escaped_config_parent_dir}'
if path not in sys.path:
    sys.path.append(path)
{script_footer}
"""

def get_usercustomize_file_contents():
    if Path(customize_script_path).exists():
        with open(customize_script_path, 'r') as f:
            return f.read()
    return ''

if __name__ == '__main__':
    usercustomize_file_contents = get_usercustomize_file_contents()

    if script not in usercustomize_file_contents:
        with open(customize_script_path, 'a+') as f:
            f.write(script)