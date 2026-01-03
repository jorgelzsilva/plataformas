# -*- coding: utf-8 -*-
"""
Módulo para extração de metadados de arquivos MHTML.
"""

import re
import quopri
from pathlib import Path
from bs4 import BeautifulSoup


import email
from email import policy

def decode_mhtml(mhtml_path: str) -> str:
    """
    Decodifica um arquivo MHTML extraindo a parte text/html.
    
    Args:
        mhtml_path: Caminho para o arquivo MHTML.
        
    Returns:
        Conteúdo HTML decodificado.
    """
    try:
        with open(mhtml_path, 'rb') as f:
            msg = email.message_from_binary_file(f, policy=policy.default)
        
        # Procura pela parte HTML
        for part in msg.walk():
            if part.get_content_type() == 'text/html':
                payload = part.get_payload(decode=True)
                charset = part.get_content_charset() or 'windows-1252'
                return payload.decode(charset, errors='replace')
    except Exception as e:
        print(f"Erro ao decodificar MHTML via MIME: {e}")
        
    # Fallback para o método anterior se falhar
    with open(mhtml_path, 'rb') as f:
        content = f.read()
    try:
        decoded = quopri.decodestring(content)
        return decoded.decode('windows-1252', errors='replace')
    except Exception:
        return decoded.decode('utf-8', errors='replace')


def extract_input_value(html: str, field_name: str) -> str:
    """
    Extrai o valor de um campo input pelo atributo name.
    
    Args:
        html: Conteúdo HTML.
        field_name: Nome do campo input.
        
    Returns:
        Valor do campo ou string vazia se não encontrado.
    """
    # Padrão para encontrar input com name específico e extrair value
    pattern = rf'name\s*=\s*["\']?{re.escape(field_name)}["\']?\s+[^>]*value\s*=\s*["\']([^"\']*)["\']'
    match = re.search(pattern, html, re.IGNORECASE | re.DOTALL)
    if match:
        return match.group(1).strip()
    
    # Tentar padrão alternativo (value antes de name)
    pattern = rf'value\s*=\s*["\']([^"\']*)["\'][^>]*name\s*=\s*["\']?{re.escape(field_name)}["\']?'
    match = re.search(pattern, html, re.IGNORECASE | re.DOTALL)
    if match:
        return match.group(1).strip()
    
    return ""


def extract_checked_checkbox(html: str, field_name: str) -> str:
    """
    Extrai o texto associado a um checkbox marcado.
    
    Args:
        html: Conteúdo HTML.
        field_name: Nome do grupo de checkboxes.
        
    Returns:
        Nome do selo/editora marcado.
    """
    # Procura por checkbox com checked e extrai o texto após
    pattern = rf'<input[^>]*name\s*=\s*["\']?{re.escape(field_name)}\[\]["\']?[^>]*checked\s*=\s*["\']?checked["\']?[^>]*>\s*([^<]+)'
    match = re.search(pattern, html, re.IGNORECASE | re.DOTALL)
    if match:
        return match.group(1).strip()
    
    # Tentar padrão com checked antes dos outros atributos
    pattern = rf'<input[^>]*checked\s*=\s*["\']?checked["\']?[^>]*name\s*=\s*["\']?{re.escape(field_name)}\[\]["\']?[^>]*>\s*([^<]+)'
    match = re.search(pattern, html, re.IGNORECASE | re.DOTALL)
    if match:
        return match.group(1).strip()
    
    return ""


def parse_subject_from_classification(classification: str) -> str:
    """
    Parseia o assunto a partir da classificação mercadológica.
    Exemplo: "33.01.09 - Terapia Cognitivo-Comportamental" -> "Psicologia > Terapia Cognitivo-Comportamental"
    
    Args:
        classification: String de classificação do site.
        
    Returns:
        Assunto formatado.
    """
    if not classification:
        return ""
    
    # Remove código numérico inicial
    parts = classification.split(" - ", 1)
    if len(parts) == 2:
        subject = parts[1].strip()
        # Adiciona categoria pai baseada no código
        if classification.startswith("33"):
            return f"Psicologia > {subject}"
        return subject
    
    return classification


def extract_sinopse_from_html(html: str) -> str:
    """
    Extrai o texto da Sinopse do HTML decodificado.
    
    Args:
        html: Conteúdo HTML decodificado.
        
    Returns:
        Texto da sinopse limpo.
    """
    soup = BeautifulSoup(html, 'html.parser')
    
    # Procura pelo <td> que contém "Sinopse"
    sinopse_label = soup.find('td', string=re.compile(r'Sinopse', re.IGNORECASE))
    if sinopse_label:
        # Pega o próximo <td> que deve conter o texto
        sinopse_content = sinopse_label.find_next_sibling('td')
        if sinopse_content:
            # Pega o texto, preservando parágrafos com quebras de linha se necessário
            # ou apenas o texto limpo como solicitado
            text = sinopse_content.get_text(separator=' ', strip=True)
            # Remove múltiplos espaços e quebras de linha estranhas
            text = re.sub(r'\s+', ' ', text).strip()
            return text
            
    return ""


def extract_subarea_from_html(html: str) -> str:
    """
    Extrai o texto da Subárea do HTML decodificado.
    
    Args:
        html: Conteúdo HTML decodificado.
        
    Returns:
        Texto da subárea limpo (ex: "Administração > Finanças").
    """
    soup = BeautifulSoup(html, 'html.parser')
    
    # Procura pelo <td> que contém "Subárea"
    subarea_label = soup.find('td', string=re.compile(r'^Subárea$', re.IGNORECASE))
    if not subarea_label:
        # Tenta sem o acento se necessário ou parcial
        subarea_label = soup.find('td', string=re.compile(r'Subárea', re.IGNORECASE))
        
    if subarea_label:
        # Pega o próximo <td> que deve conter o texto
        subarea_content = subarea_label.find_next_sibling('td')
        if subarea_content:
            text = subarea_content.get_text(strip=True)
            # Converte HTML entities como &gt; se o BS4 não o fez (ele costuma fazer)
            return text
            
    return ""


def extract_metadata_from_mhtml(mhtml_path: str) -> dict:
    """
    Extrai metadados de um arquivo MHTML de cadastro.
    
    Args:
        mhtml_path: Caminho para o arquivo MHTML.
        
    Returns:
        Dicionário com metadados extraídos:
        - title: Título completo (título + subtítulo)
        - creator: Autor(es)
        - subject: Classificação/Assunto
        - publisher: Editora/Selo
        - isbn: ISBN eletrônico
    """
    html = decode_mhtml(mhtml_path)
    
    # Extrai campos
    titulo = extract_input_value(html, "titulo")
    subtitulo = extract_input_value(html, "subtitulomkt")
    autores = extract_input_value(html, "autores")
    classificacao = extract_input_value(html, "classificacaoSite")
    isbn = extract_input_value(html, "ISBNEletr")
    selo = extract_checked_checkbox(html, "selo")
    
    # Formata título completo
    if subtitulo:
        title = f"{titulo}: {subtitulo.lower()}"
    else:
        title = titulo
    
    # Parseia assunto (tenta Subárea primeiro, fallback para classificação)
    subarea = extract_subarea_from_html(html)
    if subarea:
        subject = subarea
    else:
        subject = parse_subject_from_classification(classificacao)
    
    # Extrai sinopse
    description = extract_sinopse_from_html(html)
    
    return {
        "title": title,
        "creator": autores,
        "subject": subject,
        "publisher": selo,
        "isbn": isbn,
        "description": description
    }


if __name__ == "__main__":
    # Teste rápido
    import sys
    if len(sys.argv) > 1:
        metadata = extract_metadata_from_mhtml(sys.argv[1])
        print("Metadados extraídos:")
        for key, value in metadata.items():
            print(f"  {key}: {value}")
