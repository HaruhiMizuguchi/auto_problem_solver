"""
ocr_solver.py
OpenAI / Gemini を環境変数で切替可能にした版
"""
from __future__ import annotations
import os, re, json, pytesseract
from typing import List, Tuple
from PIL import Image
from dotenv import load_dotenv

# === 環境変数読込 ===
load_dotenv()
OCR_LANG: str = os.getenv('OCR_LANG', 'eng')
LLM_PROVIDER: str = (os.getenv('LLM_PROVIDER', 'openai') or 'openai').lower()  # 'openai' | 'gemini'

# --- OpenAI (任意) ---
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
_openai_client = None

# --- Gemini (任意) ---
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
GEMINI_MODEL = os.getenv('GEMINI_MODEL', 'gemini-1.5-flash')
_gemini_model = None

# Windows で Tesseract のパスが必要なら:
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# ===== OCR =====
def ocr_image(img: Image.Image) -> str:
    scale = 1.5
    w, h = img.size
    img = img.resize((int(w * scale), int(h * scale)))
    text = pytesseract.image_to_string(img, lang=OCR_LANG)
    return text

# ===== 問題・選択肢抽出 =====
def parse_question_choices(text: str) -> Tuple[str, List[Tuple[str, str]]]:
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    choice_pat = re.compile(r'^((?:[ア-エ]|[A-D]|[1-9]|①|②|③|④|a|b|c|d)[\)|．\.\s])')
    question_lines, choice_lines = [], []
    hit_choice = False
    for ln in lines:
        if choice_pat.match(ln):
            hit_choice = True
            choice_lines.append(ln)
        else:
            (choice_lines if hit_choice else question_lines).append(ln)

    choices: List[Tuple[str, str]] = []
    for ln in choice_lines:
        m = choice_pat.match(ln)
        if m:
            label = m.group(1).strip()
            label = label.strip(').．. ').upper()
            body = ln[m.end():].strip()
            choices.append((label, body))
        else:
            if choices:
                choices[-1] = (choices[-1][0], (choices[-1][1] + ' ' + ln).strip())

    question = '\n'.join(question_lines).strip()
    return question, choices

# ===== LLM 呼び出し 共通プロンプト =====
def _build_user_prompt(question: str, choices: List[Tuple[str, str]]) -> str:
    choice_text = '\n'.join([f"{k}. {v}" for k, v in choices]) if choices else '(選択肢なし)'
    return f"""問題:
{question}

選択肢:
{choice_text}

出力フォーマット（JSONで厳守）:
{{
  "answer_label": "<ラベル(例: A/ア/1など)>",
  "reason": "<100〜300字で根拠>"
}}"""

# ===== OpenAI 実装 =====
def _ensure_openai():
    global _openai_client
    if _openai_client is None:
        from openai import OpenAI
        if not OPENAI_API_KEY:
            raise RuntimeError("OPENAI_API_KEY が未設定です。")
        _openai_client = OpenAI(api_key=OPENAI_API_KEY)
    return _openai_client


def _ask_openai(question: str, choices: List[Tuple[str, str]]) -> str:
    client = _ensure_openai()
    system = 'あなたは厳密で説明力の高い試験対策アシスタントです。根拠を筋道立てて示し、最終的に一つの回答ラベルをJSONで返してください。'
    user = _build_user_prompt(question, choices)
    resp = client.chat.completions.create(
        model='gpt-4.1-mini',
        messages=[{'role': 'system', 'content': system},
                  {'role': 'user', 'content': user}],
        response_format={'type': 'json_object'},
        temperature=0.2,
    )
    return resp.choices[0].message.content

# ===== Gemini 実装 =====
def _ensure_gemini():
    global _gemini_model
    if _gemini_model is None:
        if not GEMINI_API_KEY:
            raise RuntimeError("GEMINI_API_KEY が未設定です。")
        import google.generativeai as genai
        genai.configure(api_key=GEMINI_API_KEY)
        _gemini_model = genai.GenerativeModel(
            GEMINI_MODEL,
            generation_config={"temperature": 0.2, "response_mime_type": "application/json"},
        )
    return _gemini_model


def _ask_gemini(question: str, choices: List[Tuple[str, str]]) -> str:
    model = _ensure_gemini()
    user = _build_user_prompt(question, choices)
    resp = model.generate_content(user)
    return resp.text

# ===== 公開 API =====
def ask_llm(question: str, choices: List[Tuple[str, str]]) -> str:
    provider = LLM_PROVIDER
    if provider == 'gemini':
        return _ask_gemini(question, choices)
    return _ask_openai(question, choices)


def solve_from_image(img: Image.Image) -> str:
    text = ocr_image(img)
    q, ch = parse_question_choices(text)
    out = ask_llm(q, ch)
    try:
        json.loads(out)
        return out
    except Exception:
        cleaned = out.strip()
        if cleaned.startswith('```'):
            cleaned = cleaned.strip('` \n')
            idx = cleaned.find('\n')
            if idx != -1:
                cleaned = cleaned[idx+1:].strip()
        m_label = re.search(r'"?answer_label"?\s*:\s*"([^"]+)"', cleaned)
        m_reason = re.search(r'"?reason"?\s*:\s*"([^"]+)"', cleaned, flags=re.S)
        fallback = {"answer_label": (m_label.group(1) if m_label else ''),"reason": (m_reason.group(1).strip() if m_reason else cleaned[:500])}
        return json.dumps(fallback, ensure_ascii=False)