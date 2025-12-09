import torch
from fastapi import FastAPI
from pydantic import BaseModel
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
from peft import PeftModel

# ==== Local paths ====
BASE_MODEL_DIR = "/workspace/models/llama3-base"
LORA_DIR       = "/workspace/models/summarization-lora"
TOKENIZER_DIR  = "/workspace/tokenizers/summarization-tokenizer"

# ==== FastAPI app ====
app = FastAPI(title="Project Summarization API")

# Global objects
tokenizer = None
model = None

class SummarizeRequest(BaseModel):
    project_json: str

class SummarizeResponse(BaseModel):
    output_text: str


def load_tokenizer():
    global tokenizer
    tokenizer = AutoTokenizer.from_pretrained(
        TOKENIZER_DIR,
        trust_remote_code=True,
    )
    # tokenizer.chat_template already saved in tokenizer_config.json
    if tokenizer.chat_template is None:
        # Fallback (only if something went wrong in saving)
        tokenizer.chat_template = """
        {% for m in messages %}
        <|{{ m.role }}|>
        {{ m.content.strip() }}
        {% endfor %}
        <|assistant|>
        """
    # Safety
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "right"
    print("✅ Tokenizer loaded with chat_template.")


def load_model():
    global model

    print("⏳ Loading base model in 4-bit...")
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_quant_type="nf4",
    )

    base_model = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL_DIR,
        quantization_config=bnb_config,
        device_map="auto",
        trust_remote_code=True,
    )

    print("⏳ Attaching LoRA adapter...")
    model_with_lora = PeftModel.from_pretrained(
        base_model,
        LORA_DIR,
        device_map="auto",
    )

    model_with_lora.eval()
    print("✅ Model with LoRA ready.")
    model = model_with_lora


@app.on_event("startup")
def startup_event():
    print("🚀 Starting up, loading tokenizer and model...")
    load_tokenizer()
    load_model()
    print("🚀 Startup complete.")


@app.post("/summarize", response_model=SummarizeResponse)
def summarize(req: SummarizeRequest):
    """
    Expects: project_json (string with the project fields)
    Returns: model's structured JSON summarization as text
    """
    messages = [
        {"role": "system", "content":(
                                """ You are an expert project summarization model used in the Horizon Extra Works tool
                                Your task is: Project Summarization
                                You strictly follow these rules:
                                1. Rewrite scope fields (notes, problem, scope, justification, non-approval-effect) into short summarized and clean human language.
                                2. When you got no data for output field then simply mention N/A
                                3. Never copy text word-for-word unless required (e.g., financial values).
                                4. Summaries must be factual, fluent, and business-professional.
                                5. Follow the exact output structure:
                                    - reasoning
                                    - overview
                                    - project_scope
                                    - status_history
                                    - project_financials
                                    - epic_form
                                    - pors
                                    - close_out
                                    - blockers[]
                                    - next_steps[]
                                6. The “reasoning” field must explain HOW you transformed the input into structured summaries so smaller models can learn the summarization policy.
                                7. Blockers are the missing things in project completion and next steps are their implementation steps
                                """
                            )},
        {"role": "user", "content": req.project_json},
    ]

    # Convert messages -> prompt via saved chat_template
    prompt = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True,
    )

    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)

    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=1600,
            temperature=0.2,
        )

    output_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
    return SummarizeResponse(output_text=output_text)


@app.get("/health")
def health():
    return {"status": "ok"}
