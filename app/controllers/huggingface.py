import logging
import os


log = logging.getLogger("app.controllers.capital_palnning")


HF_TOKEN = os.environ.get("HUGGINGFACE_HUB_TOKEN")

BASE_MODEL_ID = "meta-llama/Meta-Llama-3-8B-Instruct"
LORA_REPO_ID = "afzalakram20/summarization-lora"
TOKENIZER_REPO_ID = "afzalakram20/summarization-tokenizer"

BASE_MODEL_DIR = "/hf/models/llama3-base"
LORA_DIR = "/hf/models/summarization-lora"
TOKENIZER_DIR = "/hf/tokenizers/summarization-tokenizer"


class HuggingFaceController:
    async def loadModels(self, req: ScopeRequest):
        try:
            os.makedirs("/hf/models", exist_ok=True)
            os.makedirs("/hf/tokenizers", exist_ok=True)
            HF_TOKEN = os.environ.get("HUGGINGFACE_HUB_TOKEN")

            snapshot_download(
                repo_id=BASE_MODEL_ID,
                local_dir=BASE_MODEL_DIR,
                token=HF_TOKEN,
                local_dir_use_symlinks=False,
            )

            snapshot_download(
                repo_id=LORA_REPO_ID,
                local_dir=LORA_DIR,
                token=HF_TOKEN,
                local_dir_use_symlinks=False,
            )

            snapshot_download(
                repo_id=TOKENIZER_REPO_ID,
                local_dir=TOKENIZER_DIR,
                token=HF_TOKEN,
                local_dir_use_symlinks=False,
            )

            return {
                "ok": True,
                "data": selected_estimates,
                "error": None,
            }

        except HTTPException as e:
            raise e
        except Exception as e:
            return {
                "ok": False,
                "data": None,
                "error": {
                    "code": "SERVER_ERROR",
                    "message": str(e),
                },
            }
