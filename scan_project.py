import os
import pathspec
import chardet
import re

# Array of folder names to ignore
IGNORED_FOLDERS = ["ai_conversation", "jobs"]

def read_gitignore(root_path):
    gitignore_path = os.path.join(root_path, '.gitignore')
    if os.path.exists(gitignore_path):
        with open(gitignore_path, 'r') as gitignore_file:
            spec = pathspec.PathSpec.from_lines('gitwildmatch', gitignore_file)
        return spec
    return None

def should_ignore(path, gitignore_spec):
    if path.startswith(('.git', 'venv')) or path == 'scan_project.py' or '__pycache__' in path:
        return True
    if path == 'main.spec' or path == 'project_contents.txt' or path.endswith('__init__.py'):
        return True
    if any(folder in path for folder in IGNORED_FOLDERS):
        return True
    if gitignore_spec:
        return gitignore_spec.match_file(path)
    return False

def read_file_content(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except UnicodeDecodeError:
        with open(file_path, 'rb') as file:
            raw_data = file.read()
        detected = chardet.detect(raw_data)
        encoding = detected['encoding']
        try:
            return raw_data.decode(encoding)
        except:
            return f"Error: Unable to decode file with detected encoding: {encoding}"

def simplify_content(content, file_path):
    if file_path.endswith('.py'):
        # Remove Django's docstring comments with djangoproject.com URLs
        content = re.sub(r'"""[\s\S]*?https://docs\.djangoproject\.com/[\s\S]*?"""', '', content)
        
        # Remove empty lines that might be left after removing the docstring
        content = '\n'.join(line for line in content.split('\n') if line.strip())
        
        # For settings.py, remove comments starting with #
        if os.path.basename(file_path) == 'settings.py':
            content = '\n'.join(line for line in content.split('\n') if not line.strip().startswith('#'))
        
    elif file_path.endswith('.html'):
        return '\n'.join(line for line in content.split('\n') if line.strip() and not line.strip().startswith(('<!--', '//')))
    
    return content

def scan_project(root_path, output_file):
    gitignore_spec = read_gitignore(root_path)

    with open(output_file, 'w', encoding='utf-8') as out_file:
        for root, dirs, files in os.walk(root_path):
            dirs[:] = [d for d in dirs if d not in {'.git', 'venv'} and d not in IGNORED_FOLDERS]

            rel_path = os.path.relpath(root, root_path)

            for file in files:
                file_path = os.path.join(root, file)
                rel_file_path = os.path.relpath(file_path, root_path)

                if should_ignore(rel_file_path, gitignore_spec):
                    continue

                out_file.write(f"\nFile: {rel_file_path}\n")
                out_file.write('------\n')

                content = read_file_content(file_path)
                simplified_content = simplify_content(content, file_path)
                out_file.write(simplified_content)
                out_file.write('\n\n')

if __name__ == "__main__":
    project_root = os.getcwd()
    output_file = "project_contents.txt"
    
    scan_project(project_root, output_file)
    print(f"Simplified project contents have been written to {output_file}")