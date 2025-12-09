# AI Gateway (Dev mocks)

https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe
## 1) Install


```bash
py -3.11 -m venv .venv
c
# python -m venv .venv 
# .\.venv/bin/activate
./.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
cp .env.example .env


virtual
python -m venv .venv 
source .venv/bin/activate




uvicorn app.main:app --reload --port 8081
uvicorn app.main:app --reload --host 0.0.0.0 --port 8081

import logging
log = logging.getLogger("app.services.sqlchat")
 log.info(f"intent ---{parsed}")

 HF-->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