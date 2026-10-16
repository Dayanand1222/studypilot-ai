# StudyPilot AI — Professional Student Study Planner

[![StudyPilot AI CI](https://github.com/USERNAME/REPOSITORY/actions/workflows/ci.yml/badge.svg)](https://github.com/USERNAME/REPOSITORY/actions/workflows/ci.yml)

> Replace `USERNAME/REPOSITORY` with your actual GitHub username and repository name after uploading.


## Features
- Polished dark dashboard
- Subject and exam-date management
- Explainable priority scoring (50% urgency, 20% difficulty, 30% pending syllabus)
- AI Plan Bot: date-wise study blocks, revision blocks, CSV export
- Save plan to schedule and mark sessions complete
- Progress analytics with charts
- Topic-specific YouTube search helper
- SQLite local persistence

## Run on Windows
Python 3.13 recommended. Open PowerShell in this folder and run:
```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```
Open the local URL printed by Streamlit, normally http://localhost:8501.

## AI Plan Bot input
One subject per line:
`Subject Name | YYYY-MM-DD | difficulty 1-5 | total topics | completed topics`

Example:
`DBMS | 2026-10-20 | 5 | 10 | 2`

This is an explainable rule-based scheduling algorithm, not a trained ML model or cloud LLM. The Video Tutor creates YouTube search links; it does not verify individual videos.


## CI/CD (GitHub Actions + Streamlit Community Cloud)

### Continuous Integration (CI)
This repository includes `.github/workflows/ci.yml`. On each push or pull request to
`main` or `master`, GitHub Actions installs the dependencies, checks Python syntax,
and runs lightweight project checks with pytest.

### Continuous Deployment (CD)
The project is ready to deploy on Streamlit Community Cloud. Deployment needs a one-time
manual connection because it must be linked to your GitHub account:

1. Create a GitHub repository and upload the contents of this project folder.
2. Open https://share.streamlit.io/ and sign in with GitHub.
3. Choose **Create app**, select your repository, branch (`main`), and `app.py`.
4. Click **Deploy**. Streamlit Community Cloud will build the app.
5. After the initial deployment, new commits to the selected branch trigger redeployment.

The CI workflow validates the project; the Streamlit Community Cloud connection handles CD.
No API key or secret is required by the current project. Do not commit passwords or API keys.
