import site
import re
from pathlib import Path
from add_config_to_path import customize_script_path, script_header, script_footer

# see https://python-forum.io/thread-32255.html for explanation

if __name__ == '__main__':
    # check if customize_script_path exists, if no exit, if so, read contents to string
    if not Path(customize_script_path).exists():
        exit()
    with open(customize_script_path, 'r') as f:
        usercustomize_file_contents = f.read()

    script_matcher = re.compile(f"\n?{script_header}.*{script_footer}\n?", re.DOTALL)

    # replace customize_script_path contents with the usercustomize_file_contents, deleting all matches of script_matcher from the contents of the python file
    with open(customize_script_path, 'w') as f:
        f.write(script_matcher.sub('', usercustomize_file_contents))
