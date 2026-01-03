# -*- coding: utf-8 -*-
"""
Módulo para gerenciamento de marcas (watermarks) em arquivos XHTML.
"""

import os
import re
import random
from pathlib import Path
from typing import List, Tuple

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import ELIGIBLE_FILE_PATTERN, EXCLUDED_FILE_PATTERNS, NUM_FILES_TO_MARK, MARK_TEMPLATE


def find_eligible_files(oebps_path: str) -> List[str]:
    """
    Encontra arquivos XHTML elegíveis para receber marcas.
    
    Critérios:
    - Terminam com números (ex: cap_001.xhtml)
    - Não são parte ou seção
    
    Args:
        oebps_path: Caminho para a pasta OEBPS do EPUB.
        
    Returns:
        Lista de caminhos para arquivos elegíveis.
    """
    eligible = []
    oebps = Path(oebps_path)
    
    for xhtml_file in oebps.glob("*.xhtml"):
        filename = xhtml_file.name
        
        # Verifica se corresponde ao padrão de arquivo elegível
        if re.match(ELIGIBLE_FILE_PATTERN, filename):
            # Verifica se não está na lista de excluídos
            is_excluded = any(
                re.match(pattern, filename) 
                for pattern in EXCLUDED_FILE_PATTERNS
            )
            
            if not is_excluded:
                eligible.append(str(xhtml_file))
    
    return sorted(eligible)


def select_random_files(eligible_files: List[str], num_files: int = NUM_FILES_TO_MARK) -> List[str]:
    """
    Seleciona arquivos aleatórios para marcar.
    
    Args:
        eligible_files: Lista de arquivos elegíveis.
        num_files: Número de arquivos a selecionar.
        
    Returns:
        Lista de arquivos selecionados.
    """
    if len(eligible_files) <= num_files:
        return eligible_files
    
    return random.sample(eligible_files, num_files)


def insert_watermark(file_path: str, mark: str) -> bool:
    """
    Insere uma marca em um arquivo XHTML antes da tag </body>.
    
    Args:
        file_path: Caminho para o arquivo XHTML.
        mark: Símbolo da marca a inserir.
        
    Returns:
        True se a marca foi inserida com sucesso.
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Cria o HTML da marca
    mark_html = MARK_TEMPLATE.format(mark=mark)
    
    # Encontra a posição de </body> (pode ter espaços/newlines antes)
    # Procura pelo padrão: possivelmente </div> + espaços + </body>
    body_pattern = r'(</body>)'
    
    # Insere a marca antes de </body>
    # Primeiro verifica se há um </div> antes de </body> (estrutura comum)
    div_body_pattern = r'(</div>\s*)(</body>)'
    
    if re.search(div_body_pattern, content, re.IGNORECASE):
        # Insere após o </div> e antes de </body>
        new_content = re.sub(
            div_body_pattern,
            rf'\1{mark_html}\n\2',
            content,
            count=1,
            flags=re.IGNORECASE
        )
    else:
        # Insere diretamente antes de </body>
        new_content = re.sub(
            body_pattern,
            rf'{mark_html}\n\1',
            content,
            count=1,
            flags=re.IGNORECASE
        )
    
    # Verifica se houve alteração
    if new_content == content:
        return False
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    return True


def add_platform_watermarks(oebps_path: str, mark: str) -> List[Tuple[str, bool]]:
    """
    Adiciona marcas de plataforma a 3 arquivos aleatórios.
    
    Args:
        oebps_path: Caminho para a pasta OEBPS do EPUB.
        mark: Símbolo da marca da plataforma.
        
    Returns:
        Lista de tuplas (arquivo, sucesso).
    """
    # Encontra arquivos elegíveis
    eligible = find_eligible_files(oebps_path)
    
    if not eligible:
        return []
    
    # Seleciona arquivos aleatórios
    selected = select_random_files(eligible)
    
    # Insere marcas
    results = []
    for file_path in selected:
        success = insert_watermark(file_path, mark)
        results.append((os.path.basename(file_path), success))
    
    return results


if __name__ == "__main__":
    # Teste rápido
    import sys
    if len(sys.argv) > 2:
        oebps = sys.argv[1]
        mark = sys.argv[2]
        results = add_platform_watermarks(oebps, mark)
        print(f"Arquivos marcados com '{mark}':")
        for filename, success in results:
            status = "OK" if success else "FALHOU"
            print(f"  {filename}: {status}")
