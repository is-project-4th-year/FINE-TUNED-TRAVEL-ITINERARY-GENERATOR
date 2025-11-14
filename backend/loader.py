import os, torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, AutoModelForCausalLM, BitsAndBytesConfig
from peft import PeftModel

BASE_DIR = os.path.dirname(__file__)
MODELS_DIR = os.path.join(BASE_DIR, "models")

adapter_extraction_path = os.path.join(MODELS_DIR, "flan_t5_base_lora_adapter")
adapter_generation_path = os.path.join(MODELS_DIR, "hermes2pro_lora_adapter")

BASE_SEQ2SEQ_MODEL = "google/flan-t5-base"
BASE_CAUSAL_MODEL = "teknium/OpenHermes-2.5-Mistral-7B"

device = "cuda" if torch.cuda.is_available() else "cpu"


def load_extractor():
    tokenizer_ex = AutoTokenizer.from_pretrained(BASE_SEQ2SEQ_MODEL)
    base_seq2seq = AutoModelForSeq2SeqLM.from_pretrained(
        BASE_SEQ2SEQ_MODEL,
        torch_dtype=torch.float16 if device=="cuda" else torch.float32,
        device_map="auto" if device=="cuda" else None,
    )
    extractor = PeftModel.from_pretrained(base_seq2seq, adapter_extraction_path)
    extractor.eval()
    return extractor, tokenizer_ex


def load_generator():
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_use_double_quant=True,
    )

    tokenizer_gen = AutoTokenizer.from_pretrained(BASE_CAUSAL_MODEL, use_fast=True)
    base_causal = AutoModelForCausalLM.from_pretrained(
        BASE_CAUSAL_MODEL,
        quantization_config=bnb_config,
        device_map="auto",
        torch_dtype=torch.float16,
    )
    generator = PeftModel.from_pretrained(base_causal, adapter_generation_path)
    generator.eval()
    return generator, tokenizer_gen
