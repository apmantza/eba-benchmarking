
# 1. Soft reset to keep file but undo all commits
git reset --soft 77ffcd0~100 2>nul
if %errorlevel% neq 0 (
    # If less than 100 commits, just reset to root
    # Actually, easiest way to nuke history while keeping files:
    del .git /F /S /Q
    rmdir .git /S /Q
    git init
    # Re-initialize LFS
    git lfs install
    git lfs track "*.db"
    git add .gitattributes
)

# 2. Add files respecting the NEW .gitignore (which ignores data/raw)
git add .

# 3. Commit
git commit -m "Initial clean commit"

# 4. Add remote (since we deleted .git, we lost the remote)
# We need to know the remote URL. 
# From previous error: https://github.com/apmantza/eba-benchmarking.git
git remote add origin https://github.com/apmantza/eba-benchmarking.git

# 5. Force push to overwrite the bad history on server (if any got there)
# Note: The server repo is practically empty or has the failed state.
git push -u origin main --force
