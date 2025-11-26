# loader.py
"""
Quantized LLaMA loader + generator wrapper.

Exposes:
 - warm_model(async_spawn=True)
 - hermes_generate(prompt, max_tokens=600, sampling=False, temperature=0.0)
 - flan_extract(text)
 - debug_model_status()  -> diagnostic dict

This loader prefers 4-bit/bitsandbytes quantization for speed and memory.
It will attempt to load the HF repo specified by HERMES_MODEL in .env.
If model/tokenizer can't be loaded, hermes_generate falls back to a deterministic quick generator.
"""
import os
import re
import threading
import logging
from typing import Optional

from dotenv import load_dotenv
load_dotenv("/workspace/travelplanner_runpod/.env")

logger = logging.getLogger("loader")
logger.setLevel(logging.INFO)

# environment helper
def get_env(key: str, default=None) -> Optional[str]:
    v = os.getenv(key, default)
    if v is None:
        logger.warning("Missing env var: %s", key)
    return v

# model globals
_transformers_available = False
_tokenizer = None
_model = None
_device = None
_is_warming = False
_warm_lock = threading.Lock()

# optional imports
try:
    import torch  # noqa: F401
    from transformers import AutoTokenizer, AutoModelForCausalLM
    # BitsAndBytesConfig safe import
    try:
        from transformers import BitsAndBytesConfig
    except Exception:
        BitsAndBytesConfig = None
    _transformers_available = True
except Exception as e:
    logger.warning("transformers/bitsandbytes unavailable: %s", e)
    _transformers_available = False


def debug_model_status():
    info = {
        "transformers_available": _transformers_available,
        "model_present": _model is not None,
        "tokenizer_present": _tokenizer is not None,
        "device": str(_device),
    }
    try:
        if _model is not None:
            param_bytes = sum(p.numel() * p.element_size() for p in _model.parameters())
            info["approx_params_bytes"] = param_bytes
    except Exception:
        pass
    try:
        import torch
        info["cuda_available"] = torch.cuda.is_available()
        info["cuda_count"] = torch.cuda.device_count()
        if torch.cuda.is_available():
            info["cuda_name"] = torch.cuda.get_device_name(0)
            info["cuda_mem_allocated"] = torch.cuda.memory_allocated(0)
            info["cuda_mem_reserved"] = torch.cuda.memory_reserved(0)
    except Exception:
        pass
    return info


def _load_llama_model(repo_id: str, debug: bool = False) -> bool:
    """
    Try to load the HF model into GPU using bitsandbytes quantization.
    Returns True on success.
    """
    global _model, _tokenizer, _device

    if not _transformers_available:
        logger.warning("transformers not available; skipping model load")
        return False

    if _model is not None and _tokenizer is not None:
        logger.info("Model already loaded in memory")
        return True

    try:
        logger.info("Loading tokenizer: %s", repo_id)
        _tokenizer = AutoTokenizer.from_pretrained(repo_id, use_fast=True)
        # ensure pad token exists
        if getattr(_tokenizer, "pad_token", None) is None:
            logger.info("No pad_token in tokenizer; setting pad_token = eos_token")
            _tokenizer.pad_token = _tokenizer.eos_token

        # Prepare BitsAndBytesConfig if available
        bnb_cfg = None
        if "BitsAndBytesConfig" in globals() and BitsAndBytesConfig is not None:
            try:
                # prefer 4-bit for RTX4090 (faster & smaller). If you want 8-bit, change here.
                bnb_cfg = BitsAndBytesConfig(
                    load_in_4bit=True,
                    bnb_4bit_compute_dtype=getattr(__import__("torch"), "float16"),
                    bnb_4bit_use_double_quant=True,
                )
            except Exception:
                bnb_cfg = None

        logger.info("Loading model (quantized) from: %s", repo_id)
        load_kwargs = {
            "pretrained_model_name_or_path": repo_id,
            "device_map": "auto",
            "trust_remote_code": True,
        }
        # attach quantization config where supported
        if bnb_cfg is not None:
            load_kwargs["quantization_config"] = bnb_cfg

        # Try with AutoModelForCausalLM.from_pretrained - let HF choose dtype/device
        _model = AutoModelForCausalLM.from_pretrained(**{k: v for k, v in load_kwargs.items() if v is not None})

        # deduce device
        try:
            _device = next(_model.parameters()).device
        except Exception:
            _device = None

        logger.info("Model loaded. device=%s tokenizer=%s", _device, type(_tokenizer))
        return True

    except Exception as e:
        logger.exception("Failed to load LLaMA: %s", e)
        _tokenizer = None
        _model = None
        _device = None
        return False


def warm_model(async_spawn: bool = True):
    """
    Ensure model loads in background (or synchronously if async_spawn=False).
    Safe to call multiple times.
    """
    global _is_warming
    with _warm_lock:
        if _is_warming or (_model is not None and _tokenizer is not None):
            logger.info("warm_model: already warmed or loading in progress")
            return
        _is_warming = True

    def _worker():
        try:
            repo = get_env("HERMES_MODEL", "meta-llama/Llama-3.1-8B")
            logger.info("warm_model: loading repo=%s", repo)
            ok = _load_llama_model(repo, debug=True)
            if ok:
                logger.info("warm_model: succeeded")
            else:
                logger.warning("warm_model: failed (will use fallback deterministic generator)")
        finally:
            global _is_warming
            with _warm_lock:
                _is_warming = False

    if async_spawn:
        t = threading.Thread(target=_worker, daemon=True)
        t.start()
    else:
        _worker()


def hermes_generate(prompt: str, max_tokens: int = 600, temperature: float = 0.0, sampling: bool = False, debug: bool = False) -> str:
    """
    Synchronous wrapper that generates text using the loaded model.
    If model isn't available or generation fails, returns a deterministic fallback quickly.
    """
    global _model, _tokenizer, _device

    # Ensure tokenizer/model loaded (best effort)
    if _model is None or _tokenizer is None:
        logger.info("hermes_generate: model not loaded; attempting sync warm")
        _load_llama_model(get_env("HERMES_MODEL", "meta-llama/Llama-3.1-8B"))

    if _model is not None and _tokenizer is not None:
        try:
            if debug:
                logger.info("hermes_generate: using HF model")

            # Tokenize with high max_length to avoid truncating prompt
            inputs = _tokenizer(prompt, return_tensors="pt", truncation=True, max_length=4096)
            # Move inputs to model device
            if _device is not None:
                for k, v in inputs.items():
                    try:
                        inputs[k] = v.to(_device)
                    except Exception:
                        pass

            # Build generation kwargs. For speed & determinism use do_sample=False.
            gen_kwargs = {
                "max_new_tokens": int(max_tokens),
                "do_sample": bool(sampling),
                "temperature": float(temperature) if sampling else 0.0,
                "top_k": 50 if sampling else None,
                "top_p": 0.95 if sampling else None,
                "num_beams": 1 if not sampling else None,
                "eos_token_id": getattr(_tokenizer, "eos_token_id", None),
                "pad_token_id": getattr(_tokenizer, "pad_token_id", None),
                "use_cache": True,
            }
            # filter None
            gen_kwargs = {k: v for k, v in gen_kwargs.items() if v is not None}

            import torch
            with torch.no_grad():
                outputs = _model.generate(**inputs, **gen_kwargs)

            text = _tokenizer.decode(outputs[0], skip_special_tokens=True)
            return text.strip()

        except Exception as e:
            logger.exception("hermes_generate: model generation failed: %s", e)
            # fall-through to fallback generator

    # ----------------- deterministic fallback -----------------
    if debug:
        logger.info("hermes_generate: fallback deterministic generator")
    days = 2
    m = re.search(r"(\d+)[-\s]*day", prompt, re.I)
    if m:
        try:
            days = int(m.group(1))
        except Exception:
            days = 2

    parts = []
    for d in range(1, days + 1):
        parts.append(f"Day {d}")
        parts.append(f"Morning (09:00–12:00): <POI #{d} from context>")
        parts.append(f"Afternoon (13:00–17:00): <POI #{d+days} from context>")
        parts.append(f"Evening (18:00–22:00): <event on day {d} or fallback POI>")
        parts.append("")
    return "\n".join(parts).strip()


def flan_extract(text: str, debug: bool = False):
    """
    Lightweight extractor used by main.py.
    Returns 'days' as an integer (important).
    """
    import uuid
    trip_id = str(uuid.uuid4())
    city = None

    m = re.search(r"to\s+([A-Z][a-zA-Z\s\-]{1,40})", text)
    if not m:
        m = re.search(r"in\s+([A-Z][a-zA-Z\s\-]{1,40})", text)
    if m:
        city = m.group(1).strip().strip(",.")
    if not city:
        caps = re.findall(r"\b([A-Z][a-z]{2,})\b", text)
        city = caps[-1] if caps else "Unknown"

    days = 1
    m = re.search(r"(\d+)[-\s]*day", text, re.I)
    if m:
        try:
            days = int(m.group(1))
        except Exception:
            days = 1

    return {
        "trip_id": trip_id,
        "title": f"Trip to {city}",
        "start_date": None,
        "end_date": None,
        "num_travelers": None,
        "destinations": [{"city": city, "country": None}],
        "days": days,
        "budget_usd": None,
        "raw_text": text
    }


# quick smoke test when run directly
if __name__ == "__main__":
    print("Loader smoke test")
    print("HERMES_MODEL:", get_env("HERMES_MODEL"))
    print("Status:", debug_model_status())
    # Do a short generation only if user explicitly wants it (avoid heavy ops)
