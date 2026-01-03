# -*- coding: utf-8 -*-
"""
Configurações centralizadas para o script de edição de EPUB.
"""

# Mapeamento de plataformas e suas marcas identificadoras
PLATFORM_MARKS = {
    "amazon": "▲",
    "apple": "▼",
    "binpar": "◆",
    "google": "●",
    "vitalsource": "■"
}

# Lista de plataformas na ordem de processamento
PLATFORMS = list(PLATFORM_MARKS.keys())

# Padrão de arquivos elegíveis para watermark (terminam com números, não são parte/seção)
# Exemplo: cap_001.xhtml, cap_002.xhtml, etc.
ELIGIBLE_FILE_PATTERN = r"cap_\d+\.xhtml$"

# Arquivos a excluir (partes e seções)
EXCLUDED_FILE_PATTERNS = [
    r"parte_\d+\.xhtml$",
    r"secao_\d+\.xhtml$"
]

# Número de arquivos a marcar por EPUB
NUM_FILES_TO_MARK = 3

# Template HTML da marca
MARK_TEMPLATE = '<p style="text-align: center;">{mark}</p>'

# Encoding padrão do MHTML
MHTML_ENCODING = "windows-1252"

# Encoding do EPUB
EPUB_ENCODING = "utf-8"
