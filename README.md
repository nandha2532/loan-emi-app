# Loan EMI Manager

Streamlit app for managing loans and EMI schedules using PostgreSQL (Neon or any Postgres).

## Project structure

loan-emi-app/
- app.py
- db.py
- emi.py
- models.sql
- requirements.txt
- README.md
- .gitignore
- .streamlit/secrets.toml (LOCAL ONLY - DO NOT COMMIT)

## Setup (local)

1. Create a free Postgres instance (recommended: Neon.tech)
   - Sign up at https://neon.tech and create a project.
   - Copy the connection string (format `postgresql://user:pass@host:port/dbname`).

2. Run the SQL in `models.sql` in Neon SQL editor (creates tables).

3. Create a local secrets file:
   - Create folder `.streamlit/`
   - Create file `.streamlit/secrets.toml` with:
     ```toml
     DATABASE_URL = "postgresql://username:password@host:port/dbname"
     ```
   - IMPORTANT: Do NOT commit this file. Add it to `.gitignore`.

4. Install dependencies:
   ```bash
   python -m pip install -r requirements.txt
   ```

5. Run the app:
   ```bash
   streamlit run app.py
   ```

## Deploying to Streamlit Cloud
- Use the same repository.
- In Streamlit app dashboard, add a secret named `DATABASE_URL` with the Neon connection string (do not upload `secrets.toml` to Git).
- Deploy.

## Git steps (create new repo & push)
```bash
git init
git add .
git commit -m "Initial commit: Loan EMI Manager (Postgres)"
# create repo on GitHub, then:
git remote add origin git@github.com:yourusername/loan-emi-app.git
git branch -M main
git push -u origin main
```

## Notes & tips
- Keep `secrets.toml` out of Git — it contains DB credentials.
- Neon provides a free Postgres tier; other providers (Supabase) also work.
- If you need an automatic migration from an existing SQLite DB, I can provide a migration script.
