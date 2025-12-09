from huggingface_hub import snapshot_download
import os

HF_TOKEN = os.environ.get("HUGGINGFACE_HUB_TOKEN")

BASE_MODEL_ID      = "meta-llama/Meta-Llama-3-8B-Instruct"
LORA_REPO_ID       = "afzalakram20/summarization-lora"
TOKENIZER_REPO_ID  = "afzalakram20/summarization-tokenizer"

BASE_MODEL_DIR     = "/workspace/models/llama3-base"
LORA_DIR           = "/workspace/models/summarization-lora"
TOKENIZER_DIR      = "/workspace/tokenizers/summarization-tokenizer"

os.makedirs("/workspace/models", exist_ok=True)
os.makedirs("/workspace/tokenizers", exist_ok=True)

print("⏬ Downloading base model...")
snapshot_download(
    repo_id=BASE_MODEL_ID,
    local_dir=BASE_MODEL_DIR,
    token=HF_TOKEN,
    local_dir_use_symlinks=False,
)

print("⏬ Downloading LoRA adapter...")
snapshot_download(
    repo_id=LORA_REPO_ID,
    local_dir=LORA_DIR,
    token=HF_TOKEN,
    local_dir_use_symlinks=False,
)

print("⏬ Downloading tokenizer...")
snapshot_download(
    repo_id=TOKENIZER_REPO_ID,
    local_dir=TOKENIZER_DIR,
    token=HF_TOKEN,
    local_dir_use_symlinks=False,
)

print("✅ All artifacts downloaded.")
