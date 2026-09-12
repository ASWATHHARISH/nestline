# Stage 9 local Streamlit runbook

Stage 9 is a local product experience. It does not deploy a website or publish health content.

## Clean start

Use Python 3.12 from the repository root:

```powershell
py -3.12 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m streamlit run streamlit_app.py --server.headless true --server.port 8501 --browser.gatherUsageStats false
```

Open `http://localhost:8501/?mode=demo&page=Weekly+Home` for the deterministic fictional experience. Demo Mode needs no API key, provider, LangSmith, or live database. It is visibly fixture-only and must not receive real medical or personal information.

Personal Mode starts empty. To exercise the accepted Stage 3/4 sign-in/onboarding path, copy `.env.example` to the ignored `.env` file and set:

```text
NESTLINE_SUPABASE_URL=https://YOUR_PROJECT_REF.supabase.co
NESTLINE_SUPABASE_PUBLISHABLE_KEY=YOUR_PUBLISHABLE_KEY
```

Do not put a service-role key in the Streamlit environment.

## Reset

Use **Reset fictional Demo Mode** in the sidebar. It removes only `stage9_demo_*` temporary UI keys. It does not remove Personal Mode authentication or workspace state. Restart Streamlit for a completely new local process.

## Verification

```powershell
.venv\Scripts\python.exe -m unittest tests.test_product_experience -v
.venv\Scripts\python.exe -m scripts.check_stage9_ui
.venv\Scripts\python.exe -m scripts.export_product_experience_schema
.venv\Scripts\python.exe -m scripts.run_stage9_evals
.venv\Scripts\python.exe -m scripts.check_stage9 --write-report
```

## Troubleshooting

- **Personal Mode configuration is incomplete:** add the two public Supabase values above and restart. Demo Mode remains available.
- **A Compass response is blocked:** read the clarification, abstention, or safety route. The UI does not reveal an unvalidated partial draft.
- **A citation cannot open:** return to Compass, submit a supported fictional task, and choose **Open supporting evidence**. Private fixture citations are bound to the active fictional workspace.
- **Save/review submission is disabled:** durable plan/fact/review writes belong to Stage 10 and are deliberately unavailable.
- **No public weekly development card appears:** the repository has zero publicly released weekly profiles. Stage 9 refuses to present draft content as released guidance.
- **Provider, LangSmith, or internet unavailable:** Stage 9 engineering uses deterministic local fixtures. The Evaluator view labels live runs as unavailable/unrun.

The safety specification remains draft. Controlled fixture evaluations are software-contract evidence, not clinical validation or public-release authorization.
