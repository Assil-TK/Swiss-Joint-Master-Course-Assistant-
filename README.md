# Fuzzy Course Selection Assistant

A Streamlit app that helps students of the Swiss Joint Master in Computer Science (BeNeFri: Bern, Neuchâtel, Fribourg) choose their courses.

- **Hard constraints** (semester, cities or days the student can't attend, courses already completed) remove courses.
- **Fuzzy preferences**, given in words such as *High* or *Prefer*, will rank the remaining courses.
- A **degree checklist** tracks progress towards 12 teaching units, at least 3 tracks, specialisation and the thesis.

Course group project for *Fuzzy Sets and Systems I* (University of Fribourg, Autumn 2026).

## Run locally

```bash
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

## Files

- `app.py`: the Streamlit interface
- `courses.csv`: BeNeFri course list (code, name, type, semester, site, tracks, lecturers)
- `.streamlit/config.toml`: colour theme
