Running streamlit in CodeSpaces is tricky but the following should work.
```bash
streamlit run app.py --server.enableCORS false --server.enableXsrfProtection false
```