# -*- coding: utf-8 -*-
"""
Módulo para verificação de integridade do conteúdo EPUB.
"""

import re
from pathlib import Path
from typing import Tuple, List

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import PLATFORM_MARKS, MARK_TEMPLATE


def get_mark_patterns() -> List[str]:
    """
    Retorna padrões regex para todas as marcas de plataforma.
    
    Returns:
        Lista de padrões regex.
    """
    patterns = []
    for mark in PLATFORM_MARKS.values():
        # Escapa o caractere e cria padrão para a linha completa
        pattern = rf'<p[^>]*style\s*=\s*["\']text-align:\s*center;?["\'][^>]*>\s*{re.escape(mark)}\s*</p>\s*'
        patterns.append(pattern)
    return patterns


def count_characters(content: str, exclude_marks: bool = True) -> int:
    """
    Conta caracteres em um conteúdo, opcionalmente excluindo marcas.
    
    Args:
        content: Conteúdo a contar.
        exclude_marks: Se True, remove marcas antes de contar.
        
    Returns:
        Número de caracteres.
    """
    if exclude_marks:
        # Remove todas as marcas de plataforma
        for pattern in get_mark_patterns():
            content = re.sub(pattern, '', content, flags=re.IGNORECASE)
    
    return len(content)


def count_xhtml_characters(oebps_path: str, exclude_marks: bool = True) -> int:
    """
    Conta caracteres totais de todos os arquivos XHTML.
    
    Args:
        oebps_path: Caminho para a pasta OEBPS.
        exclude_marks: Se True, exclui marcas da contagem.
        
    Returns:
        Número total de caracteres.
    """
    total = 0
    oebps = Path(oebps_path)
    
    for xhtml_file in oebps.glob("*.xhtml"):
        with open(xhtml_file, 'r', encoding='utf-8') as f:
            content = f.read()
        total += count_characters(content, exclude_marks)
    
    return total


def verify_integrity(original_path: str, modified_path: str) -> Tuple[bool, int, int]:
    """
    Verifica se o conteúdo permanece o mesmo (exceto marcas).
    
    Args:
        original_path: Caminho para OEBPS original.
        modified_path: Caminho para OEBPS modificado.
        
    Returns:
        Tupla (passou, contagem_original, contagem_modificada).
    """
    original_count = count_xhtml_characters(original_path, exclude_marks=True)
    modified_count = count_xhtml_characters(modified_path, exclude_marks=True)
    
    passed = original_count == modified_count
    return passed, original_count, modified_count


def verify_all_platforms(original_oebps: str, platform_dirs: dict) -> dict:
    """
    Verifica integridade de todas as cópias de plataforma.
    
    Args:
        original_oebps: Caminho para OEBPS original.
        platform_dirs: Dicionário {plataforma: caminho_oebps}.
        
    Returns:
        Dicionário com resultados por plataforma.
    """
    original_count = count_xhtml_characters(original_oebps, exclude_marks=True)
    
    results = {
        'original_count': original_count,
        'platforms': {}
    }
    
    for platform, oebps_path in platform_dirs.items():
        modified_count = count_xhtml_characters(oebps_path, exclude_marks=True)
        passed = original_count == modified_count
        
        results['platforms'][platform] = {
            'count': modified_count,
            'passed': passed,
            'difference': modified_count - original_count
        }
    
    return results


if __name__ == "__main__":
    # Teste rápido
    import sys
    if len(sys.argv) > 1:
        oebps = sys.argv[1]
        count = count_xhtml_characters(oebps)
        print(f"Total de caracteres (sem marcas): {count}")
