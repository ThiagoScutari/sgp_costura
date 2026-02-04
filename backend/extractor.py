import os
import json
from openai import OpenAI
from pypdf import PdfReader
from io import BytesIO
from httpx import Client as HttpxClient

# Initialize OpenAI Client
# Expects OPENAI_API_KEY in environment variables
client = None

def get_openai_client():
    global client
    if client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("WARNING: OPENAI_API_KEY not found in environment.")
            return None
        
        # FIX DEFINITIVO: Força o cliente a ignorar proxies do sistema
        # que podem estar sendo injetados indevidamente
        client = OpenAI(
            api_key=api_key,
            http_client=HttpxClient(proxies={})  # Força proxy vazio
        )
    return client

def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """
    Extracts text from a PDF file using pypdf.
    Ensures proper byte stream handling for complex PDFs.
    """
    # Ensure bytes from FastAPI are properly loaded into memory
    stream = BytesIO(pdf_bytes)
    reader = PdfReader(stream)
    text = ""
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:  # Only add if text was extracted
            text += page_text + "\n"
    return text

PROMPT_SYSTEM_CONTENT = """
### 📝 Prompt de Extração para o Agente de IA

**Instruções de Sistema:**

 **Papel:** Você é um Engenheiro de Processos Têxteis sênior e especialista em extração de dados estruturados.
 **Objetivo:** Extrair a Sequência Operacional de costura do arquivo PDF anexo, limpando os dados conforme as regras de negócio abaixo para alimentar um sistema de balanceamento de linha.
 **1. Identificação do Cabeçalho:**
 * Extraia a **Referência** (ex: FA026, J6686).
 * Extraia o **Nome do Produto** (ex: BLUSA LISTRADA HELLO KITTY, SHORTS CJ J6842 BLUSA J6654, MACAQUINHO MACAS).
 
 
 **2. Regras de Filtragem (Lógica de Negócio):**
 * **Ignorar Fases Iniciais:** Não extraia nenhuma operação pertencente a fases administrativas, PPCP, Risco, Corte, Enfesto ou Depósito de Matéria Prima (geralmente ordens de 1 a 13 ou Fases <= 7).
 * **Foco na Costura:** Comece a extração a partir do setor de "COSTURA" e "MANUAL COSTURA".
 * **Excluir Ruído de Acabamento:** Ignore operações manuais de revisão, tag, dobra, embalagem e lavação (ex: "CONFERIR TAMANHOS", "PISTOLAR TAG", "LAVAÇÃO PEÇAS", "DOBRAR E EMBALAR").
 
 
 **3. Mapeamento de Máquina (Maquina_Macro):**
 Classifique o campo `maquina_macro` seguindo esta prioridade:
 * **RETA:** Se a descrição da máquina ou operação contiver "RETA", "RETA AUTOMATICA" .
 * **OVERLOCK:** Se contiver "OVERLOCK", "OVER", "PONTO CONJUGADO", "OVERLOCK REMATE", "OVERLOCK ELASTICO".
 * **COBERTURA:** Se contiver "COBERTURA", "FRISO COBERTURA", "FRISO COBERTURA 1 AGULHA", "COBERTURA 2 AGULHAS".
 * **CATRACA:** Se contiver "CATRACA".
 * **MANUAL:** Se contiver "MANUAL COSTURA".
 
 
 **4. Processamento de Tempos:**
 * O valor na coluna **T.P.** está em minutos decimais (ex: 0,3484).
 * **IMPORTANTE: MANTENHA O VALOR EXATAMENTE COMO NO ARQUIVO.**
 * **CRÍTICO: O campo minutos_decimais deve ser sempre um número (float) e usar PONTO como separador decimal, nunca vírgula.**
 * **Exemplo correto: 0.3484 (não 0,3484)**

5. Formato de Saída (JSON Estrito):
{
  "referencia": "STRING",
  "produto": "STRING",
  "operacoes": [
    {
      "ordem": INT,
      "descricao": "STRING",
      "maquina_original": "STRING",
      "maquina_macro": "STRING",
      "minutos_decimais": FLOAT,  # SEMPRE com ponto decimal (ex: 0.3484)
      "aparelho_acessorio": "STRING"
    }
  ]
}
"""

def process_pdf_with_gpt4(pdf_bytes: bytes):
    client = get_openai_client()
    if not client:
        raise Exception("OpenAI API Key not configured/available.")

    text_content = extract_text_from_pdf(pdf_bytes)
    
    # Truncate if too long (though GPT-4o has 128k context, keeping it safe)
    if len(text_content) > 100000:
        text_content = text_content[:100000]

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": PROMPT_SYSTEM_CONTENT},
                {"role": "user", "content": f"Extraia os dados deste PDF (conteúdo de texto abaixo):\n\n{text_content}"}
            ],
            response_format={"type": "json_object"},
            temperature=0
        )
        
        content = response.choices[0].message.content
        data = json.loads(content)
        
        # Fallback: garante que se a IA falhar em algum campo, o sistema não quebre
        for op in data.get("operacoes", []):
            if "minutos_decimais" not in op or op["minutos_decimais"] is None:
                op["minutos_decimais"] = 0.0
        
        return data
        
    except Exception as e:
        print(f"Error calling OpenAI: {e}")
        raise e
