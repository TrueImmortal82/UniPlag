import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.db import init_db, SessionLocal, Document
from app.checker import run_check
import json

init_db()
session = SessionLocal()

sample_text = (
    "В исследовании Иванова [1] показано, что увеличение размера батча свыше 256 снижает обобщающую способность модели. "
    "В то же время Петров [2] установил, что адаптивный темп обучения AdamW стабилизирует дисперсию градиентов. "
    "Следовательно, объединяя данные подходы, при размере батча 512 и динамическом темпе обучения AdamW "
    "можно ожидать сохранения высокой точности классификации без деградации сходимости."
)

doc = Document(
    title="Тестовая ВКР по машинному обучению",
    author="Иван Иванов",
    kind="inline",
    text=sample_text,
    words=len(sample_text.split())
)
session.add(doc)
session.commit()
session.refresh(doc)

check = run_check(session, doc, do_plag=False, do_ai=False, do_quality=False)

print("=== CHECK COMPLETED SUCCESSFULLY ===")
print("Check ID:", check.id)
print("ICG Score:", check.icg_score)
icg = json.loads(check.icg_json)
print("Metrics Summary:", icg.get("metrics_summary"))
print("Nodes Count:", len(icg.get("nodes", [])))
print("Edges Count:", len(icg.get("edges", [])))
for n in icg.get("nodes", []):
    print(f"  [{n['id']}] {n['contribution_class']} -> {n['span']['raw_text'][:70]}...")
