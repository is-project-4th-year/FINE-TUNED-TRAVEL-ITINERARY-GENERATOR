# loader.py
import os
import logging
from typing import Tuple

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

def safe_imports():
    try:
        import torch
        from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, AutoModelForCausalLM, BitsAndBytesConfig
        from peft import PeftModel
        return {
            "torch": torch,
            "AutoTokenizer": AutoTokenizer,
            "AutoModelForSeq2SeqLM": AutoModelForSeq2SeqLM,
            "AutoModelForCausalLM": AutoModelForCausalLM,
            "BitsAndBytesConfig": BitsAndBytesConfig,
            "PeftModel": PeftModel,
        }
    except Exception as e:
        logger.warning("Some ML libs are missing or failed to import: %s", e)
        raise

def _try_load(base_model, adapter_path, tokenizer_class, model_loader, device, quant_cfg=None, low_cpu_mem_usage=True):
    """
    Helper to load a model with optional quantization config.
    """
    torch = __imports__["torch"]
    tokenizer = tokenizer_class.from_pretrained(base_model)
    load_kwargs = {
        "device_map": "auto" if device.type == "cuda" else None,
        "torch_dtype": torch.float16 if device.type == "cuda" else torch.float32,
        "low_cpu_mem_usage": low_cpu_mem_usage
    }
    if quant_cfg is not None:
        load_kwargs["quantization_config"] = quant_cfg
    logger.info("Loading base model %s with kwargs: %s", base_model, {k: (type(v).__name__ if k=="quantization_config" else str(v)) for k,v in load_kwargs.items() if v is not None})
    base = model_loader.from_pretrained(base_model, **load_kwargs)
    logger.info("Wrapping with PEFT adapter from %s", adapter_path)
    from peft import PeftModel
    model = PeftModel.from_pretrained(base, adapter_path)
    model.eval()
    return model, tokenizer

def load_models(
    extractor_base: str,
    generator_base: str,
    extractor_adapter_local: str,
    generator_adapter_local: str,
    prefer_4bit: bool = True
) -> Tuple[object, object, object, object, object]:
    """
    Returns: extractor, tokenizer_ex, generator, tokenizer_gen, device
    """
    global __imports__
    __imports__ = safe_imports()
    torch = __imports__["torch"]
    BitsAndBytesConfig = __imports__["BitsAndBytesConfig"]
    AutoTokenizer = __imports__["AutoTokenizer"]
    AutoModelForSeq2SeqLM = __imports__["AutoModelForSeq2SeqLM"]
    AutoModelForCausalLM = __imports__["AutoModelForCausalLM"]

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    logger.info("Device detected: %s", device)

    # EXTRACTOR (seq2seq) — we load normally (LoRA adapter will be applied)
    logger.info("Loading extractor (seq2seq) base: %s adapter: %s", extractor_base, extractor_adapter_local)
    try:
        extractor_base_model = AutoModelForSeq2SeqLM.from_pretrained(
            extractor_base,
            device_map="auto" if device.type == "cuda" else None,
            torch_dtype=torch.float16 if device.type == "cuda" else torch.float32,
            low_cpu_mem_usage=True
        )
        tokenizer_ex = AutoTokenizer.from_pretrained(extractor_base)
        extractor = __imports__["PeftModel"].from_pretrained(extractor_base_model, extractor_adapter_local)
        extractor.eval()
        logger.info("Extractor loaded (base+adapter).")
    except Exception as e:
        logger.exception("Failed to load extractor base+adapter: %s", e)
        raise

    # GENERATOR (causal) — try quantization strategies
    logger.info("Loading generator (causal) base: %s adapter: %s", generator_base, generator_adapter_local)

    # Prepare possible quant configs
    quant_cfg_4bit = None
    quant_cfg_8bit = None
    try:
        # 4-bit config
        quant_cfg_4bit = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_use_double_quant=True,
            bnb_4bit_quant_type="nf4"
        )
    except Exception:
        quant_cfg_4bit = None

    try:
        # 8-bit config
        quant_cfg_8bit = BitsAndBytesConfig(
            load_in_8bit=True,
            llm_int8_threshold=6.0
        )
    except Exception:
        quant_cfg_8bit = None

    generator = None
    tokenizer_gen = None
    # Try 4-bit if preferred
    tried = []
    if prefer_4bit and quant_cfg_4bit is not None:
        try:
            logger.info("Attempting 4-bit generator load...")
            tokenizer_gen = AutoTokenizer.from_pretrained(generator_base, use_fast=True)
            base_gen = AutoModelForCausalLM.from_pretrained(
                generator_base,
                quantization_config=quant_cfg_4bit,
                device_map="auto",
                torch_dtype=torch.float16,
                low_cpu_mem_usage=True
            )
            generator = __imports__["PeftModel"].from_pretrained(base_gen, generator_adapter_local)
            generator.eval()
            logger.info("Generator loaded in 4-bit.")
        except Exception as e:
            logger.warning("4-bit generator load failed: %s", e)
            tried.append(("4-bit", str(e)))

    # Try 8-bit
    if generator is None and quant_cfg_8bit is not None:
        try:
            logger.info("Attempting 8-bit generator load...")
            tokenizer_gen = AutoTokenizer.from_pretrained(generator_base, use_fast=True)
            base_gen = AutoModelForCausalLM.from_pretrained(
                generator_base,
                quantization_config=quant_cfg_8bit,
                device_map="auto",
                torch_dtype=torch.float16,
                low_cpu_mem_usage=True
            )
            generator = __imports__["PeftModel"].from_pretrained(base_gen, generator_adapter_local)
            generator.eval()
            logger.info("Generator loaded in 8-bit.")
        except Exception as e:
            logger.warning("8-bit generator load failed: %s", e)
            tried.append(("8-bit", str(e)))

    # Fallback to fp16 (no quant)
    if generator is None:
        try:
            logger.info("Attempting non-quantized (fp16) generator load (may require lots of RAM)...")
            tokenizer_gen = AutoTokenizer.from_pretrained(generator_base, use_fast=True)
            base_gen = AutoModelForCausalLM.from_pretrained(
                generator_base,
                device_map="auto" if device.type == "cuda" else None,
                torch_dtype=torch.float16 if device.type == "cuda" else torch.float32,
                low_cpu_mem_usage=True
            )
            generator = __imports__["PeftModel"].from_pretrained(base_gen, generator_adapter_local)
            generator.eval()
            logger.info("Generator loaded without quantization.")
        except Exception as e:
            logger.exception("Final fallback generator load failed: %s", e)
            tried.append(("fp16", str(e)))
            raise RuntimeError(f"All generator load attempts failed: {tried}")

    return extractor, tokenizer_ex, generator, tokenizer_gen, device

if __name__ == "__main__":
    # quick local test - paths here should be relative to repo root
    EXTRACTOR_BASE = "google/flan-t5-base"   # change if different
    GENERATOR_BASE = "NousResearch/Hermes-2-Pro-Mistral-7B"  # or local path if you have local base
    EXTRACTOR_ADAPTER = "models/extractor"
    GENERATOR_ADAPTER = "models/generator"
    print("Starting local load test...")
    e, te, g, tg, dev = load_models(EXTRACTOR_BASE, GENERATOR_BASE, EXTRACTOR_ADAPTER, GENERATOR_ADAPTER)
    print("Loaded on", dev)
