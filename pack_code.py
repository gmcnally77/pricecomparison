import os

# --- CONFIGURATION ---
# 1. Output file name
OUTPUT_FILE = 'full_codebase.txt'

# 2. Folders to strictly ignore (add any build folders here)
IGNORE_DIRS = {
    '.git', 'node_modules', '__pycache__', 'venv', 'env', 
    'dist', 'build', 'coverage', '.idea', '.vscode', 'tmp', 'log'
}

# 3. File extensions to include (customize based on your stack)
#    Add '.rb', '.erb' for Rails; '.js', '.ts', '.tsx' for JS/React; etc.
INCLUDE_EXTENSIONS = {
    '.rb', '.erb', '.rake',         # Ruby/Rails
    '.js', '.jsx', '.ts', '.tsx',   # JavaScript/TypeScript
    '.py',                          # Python
    '.html', '.css', '.scss',       # Web standard
    '.json', '.yml', '.yaml', '.md' # Configs & Docs
}

def pack_codebase():
    current_dir = os.getcwd()
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as outfile:
        print(f"📦 Scanning directory: {current_dir}")
        print(f"🚫 Ignoring folders: {', '.join(IGNORE_DIRS)}")
        
        file_count = 0
        
        for root, dirs, files in os.walk(current_dir):
            # Modify 'dirs' in-place to skip ignored directories
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
            
            for file in files:
                # Check extension
                _, ext = os.path.splitext(file)
                if ext.lower() in INCLUDE_EXTENSIONS and file != 'pack_code.py':
                    file_path = os.path.join(root, file)
                    rel_path = os.path.relpath(file_path, current_dir)
                    
                    try:
                        # Write the file header
                        outfile.write(f"\n{'='*60}\n")
                        outfile.write(f"FILE_PATH: {rel_path}\n")
                        outfile.write(f"{'='*60}\n\n")
                        
                        # Write the file content
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as infile:
                            outfile.write(infile.read())
                            outfile.write("\n") # Ensure separation
                        
                        file_count += 1
                        print(f"  + Added: {rel_path}")
                        
                    except Exception as e:
                        print(f"  ! Error reading {rel_path}: {e}")

    print(f"\n✅ Done! {file_count} files packed into '{OUTPUT_FILE}'.")
    print(f"🚀 Upload this file to your new Gem chat to reset context.")

if __name__ == "__main__":
    pack_codebase()