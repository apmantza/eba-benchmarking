---
description: Deploy the EBA Benchmarking App to Streamlit Community Cloud
---

# Deploying to Streamlit Community Cloud

This guide outlines the steps to deploy your application to Streamlit Community Cloud.

## Prerequisites

1.  **GitHub Account**: You need a GitHub account to host the repository.
2.  **Streamlit Cloud Account**: Sign up at [share.streamlit.io](https://share.streamlit.io/).
3.  **Git LFS**: Since your database (`eba_data.db`) is >500MB, you MUST use Git Large File Storage (LFS).

## Step 1: Prepare the Repository

1.  **Initialize Git LFS** (if not done):
    ```bash
    git lfs install
    git lfs track "*.db"
    git add .gitattributes
    ```

2.  **Commit and Push**:
    Ensure all your code and the database are committed.
    ```bash
    git add .
    git commit -m "Prepare for deployment"
    git push origin main
    ```
    *Note: The first push with the large DB might take some time.*

## Step 2: Deploy on Streamlit Cloud

1.  Go to [share.streamlit.io](https://share.streamlit.io/).
2.  Click **"New app"**.
3.  **Repository**: Select your `eba-benchmarking` repository.
4.  **Branch**: `main` (or your working branch).
5.  **Main file path**: `src/app.py`
6.  Click **"Deploy!"**.

## Step 3: Troubleshooting

*   **Database Not Found**: Ensure `data/eba_data.db` was successfully pushed. Check your repo on GitHub; if the file is just a pointer text file (LFS pointer), Streamlit Cloud usually handles checking out the actual file, but it counts against your bandwidth.
*   **Memory Issues**: The database is large (0.5GB). Loading it into memory (pandas) might hit the resource limits of the free tier (1GB RAM).
    *   *Optimization*: The app uses SQLite queries (`pd.read_sql`) which is efficient and doesn't load the whole DB. This should work fine.
