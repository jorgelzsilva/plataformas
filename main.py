# -*- coding: utf-8 -*-
"""
Script principal para edição de metadados EPUB e marcação de plataformas.

Uso:
    python main.py <caminho_mhtml> <caminho_epub_zip>

Exemplo:
    python main.py "arquivo.mhtml" "9786558823230.epub"
"""

import os
import sys
import time
import shutil
import zipfile
import argparse
from pathlib import Path

# Adiciona o diretório atual ao path para imports
sys.path.insert(0, str(Path(__file__).parent))

from config import PLATFORMS, PLATFORM_MARKS
from modules.mhtml_parser import extract_metadata_from_mhtml
from modules.opf_editor import update_opf_metadata
from modules.watermark_manager import add_platform_watermarks
from modules.integrity_checker import count_xhtml_characters, verify_all_platforms


def print_header(text: str) -> None:
    """Imprime um cabeçalho formatado."""
    print("\n" + "=" * 60)
    print(f" {text}")
    print("=" * 60)


def print_step(step: int, text: str) -> None:
    """Imprime um passo formatado."""
    print(f"\n[{step}] {text}")


def extract_epub(epub_path: str, dest_path: str) -> str:
    """
    Extrai um arquivo EPUB para um diretório.
    
    Args:
        epub_path: Caminho para o arquivo EPUB/ZIP.
        dest_path: Diretório de destino.
        
    Returns:
        Caminho para a pasta OEBPS.
    """
    with zipfile.ZipFile(epub_path, 'r') as zf:
        zf.extractall(dest_path)
    
    # Encontra a pasta OEBPS
    oebps = Path(dest_path) / "OEBPS"
    if oebps.exists():
        return str(oebps)
    
    # Procura em subdiretórios
    for subdir in Path(dest_path).iterdir():
        if subdir.is_dir():
            oebps = subdir / "OEBPS"
            if oebps.exists():
                return str(oebps)
    
    raise FileNotFoundError("Pasta OEBPS não encontrada no EPUB")


def create_epub(source_dir: str, epub_path: str) -> None:
    """
    Cria um arquivo EPUB a partir de um diretório.
    
    Args:
        source_dir: Diretório fonte (raiz do EPUB extraído).
        epub_path: Caminho para o arquivo EPUB de saída.
    """
    with zipfile.ZipFile(epub_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        # O mimetype deve ser o primeiro arquivo e sem compressão
        mimetype_path = Path(source_dir) / "mimetype"
        if mimetype_path.exists():
            zf.write(mimetype_path, "mimetype", compress_type=zipfile.ZIP_STORED)
        
        # Adiciona todos os outros arquivos
        for root, dirs, files in os.walk(source_dir):
            for file in files:
                if file == "mimetype":
                    continue
                file_path = Path(root) / file
                arcname = file_path.relative_to(source_dir)
                zf.write(file_path, arcname)


def main():
    """Função principal."""
    # Inicia timer
    start_time = time.time()
    
    print_header("EPUB Metadata Editor & Platform Watermarking")
    
    # Parse argumentos
    parser = argparse.ArgumentParser(description='Edita metadados EPUB e adiciona marcas de plataforma.')
    parser.add_argument('mhtml', nargs='?', help='Caminho para o arquivo MHTML de cadastro')
    parser.add_argument('epub', nargs='?', help='Caminho para o arquivo EPUB (.epub ou .zip)')
    args = parser.parse_args()
    
    # Configura diretórios
    base_dir = Path(__file__).parent
    input_dir = base_dir / "input"
    output_base_dir = base_dir / "output"
    
    # Garante que diretórios existam
    input_dir.mkdir(exist_ok=True)
    output_base_dir.mkdir(exist_ok=True)
    
    if args.mhtml:
        mhtml_path = args.mhtml
    else:
        # Procura por arquivos MHTML na pasta input
        mhtml_files = list(input_dir.glob("*.mhtml"))
        if not mhtml_files:
            print("ERRO: Nenhum arquivo MHTML encontrado na pasta 'input'.")
            sys.exit(1)
        mhtml_path = str(mhtml_files[0])
        print(f"  Usando MHTML: {mhtml_files[0].name}")
    
    if args.epub:
        epub_path = args.epub
    else:
        # Procura por arquivos EPUB/ZIP na pasta input
        epub_files = list(input_dir.glob("*.epub")) + list(input_dir.glob("*.zip"))
        if not epub_files:
            print("ERRO: Nenhum arquivo EPUB/ZIP encontrado na pasta 'input'.")
            sys.exit(1)
        epub_path = str(epub_files[0])
        print(f"  Usando EPUB: {epub_files[0].name}")
    
    # Passo 1: Extrair metadados do MHTML
    print_step(1, f"Extraindo metadados de: {Path(mhtml_path).name}")
    metadata = extract_metadata_from_mhtml(mhtml_path)
    
    isbn = metadata.get('isbn')
    if not isbn:
        print("ERRO: ISBN não encontrado nos metadados.")
        sys.exit(1)
        
    print(f"  ISBN identificado: {isbn}")
    print("  Metadados extraídos:")
    for key, value in metadata.items():
        print(f"    {key}: {value}")
    
    # Passo 2: Criar diretórios de saída baseados no ISBN
    print_step(2, f"Criando diretórios de saída em output/{isbn}/...")
    isbn_dir = output_base_dir / isbn
    isbn_dir.mkdir(exist_ok=True)
    
    platform_dirs = {}
    for platform in PLATFORMS:
        platform_dir = isbn_dir / platform
        platform_dir.mkdir(exist_ok=True)
        platform_dirs[platform] = str(platform_dir)
        print(f"    ✓ {platform}/")
    
    # Passo 3: Copiar e extrair EPUB para cada plataforma
    print_step(3, "Copiando e extraindo EPUB para cada plataforma...")
    
    # Pasta temporária para extração original
    temp_original = base_dir / "_temp_original"
    if temp_original.exists():
        shutil.rmtree(temp_original)
    temp_original.mkdir()
    
    try:
        original_oebps = extract_epub(epub_path, str(temp_original))
    except Exception as e:
        print(f"ERRO ao extrair EPUB: {e}")
        shutil.rmtree(temp_original)
        sys.exit(1)
        
    original_count = count_xhtml_characters(original_oebps, exclude_marks=True)
    print(f"    Contagem original de caracteres: {original_count:,}")
    
    platform_oebps = {}
    
    for platform in PLATFORMS:
        platform_extract = Path(platform_dirs[platform]) / "epub_content"
        if platform_extract.exists():
            shutil.rmtree(platform_extract)
        
        # Copia o EPUB extraído
        shutil.copytree(temp_original, platform_extract)
        
        oebps_path = str(platform_extract / "OEBPS")
        if not Path(oebps_path).exists():
            # Procura em subdiretórios
            for subdir in platform_extract.iterdir():
                if subdir.is_dir():
                    oebps = subdir / "OEBPS"
                    if oebps.exists():
                        oebps_path = str(oebps)
                        break
        
        platform_oebps[platform] = oebps_path
        print(f"    ✓ {platform}: extraído")
    
    # Passo 4: Atualizar metadados em cada cópia
    print_step(4, "Atualizando metadados em cada cópia...")
    
    for platform, oebps_path in platform_oebps.items():
        opf_path = Path(oebps_path) / "content.opf"
        if opf_path.exists():
            update_opf_metadata(str(opf_path), metadata)
            print(f"    ✓ {platform}: content.opf atualizado")
        else:
            print(f"    ✗ {platform}: content.opf não encontrado")
    
    # Passo 5: Adicionar watermarks
    print_step(5, "Adicionando marcas de plataforma...")
    
    for platform, oebps_path in platform_oebps.items():
        mark = PLATFORM_MARKS[platform]
        results = add_platform_watermarks(oebps_path, mark)
        
        files_marked = [f for f, success in results if success]
        print(f"    ✓ {platform} ({mark}): {len(files_marked)} arquivos marcados")
    
    # Passo 6: Verificar integridade
    print_step(6, "Verificando integridade do conteúdo...")
    
    integrity_results = verify_all_platforms(original_oebps, platform_oebps)
    all_passed = True
    
    for platform, result in integrity_results['platforms'].items():
        if result['passed']:
            print(f"    ✓ {platform}: OK ({result['count']:,} caracteres)")
        else:
            print(f"    ✗ {platform}: FALHOU (diferença: {result['difference']:+,})")
            all_passed = False
    
    if all_passed:
        print("\n  ✓ INTEGRIDADE VERIFICADA: Todos os conteúdos permanecem consistentes")
    else:
        print("\n  ✗ ALERTA: Algumas verificações falharam")
    
    # Passo 7: Criar EPUBs finais
    print_step(7, "Criando arquivos EPUB finais...")
    
    for platform in PLATFORMS:
        platform_extract = Path(platform_dirs[platform]) / "epub_content"
        output_epub = Path(platform_dirs[platform]) / f"{isbn}.epub"
        
        create_epub(str(platform_extract), str(output_epub))
        print(f"    ✓ {platform}/{isbn}.epub")
        
        # Remove pasta temporária
        shutil.rmtree(platform_extract)
    
    # Limpa pasta temporária original
    shutil.rmtree(temp_original)
    
    # Calcula tempo total
    end_time = time.time()
    elapsed = end_time - start_time
    
    print_header("PROCESSO CONCLUÍDO")
    print(f"\n  Tempo total: {elapsed:.2f} segundos")
    print(f"  EPUBs gerados: {len(PLATFORMS)}")
    print(f"  Localização: {isbn_dir.relative_to(base_dir)}")
    print()


if __name__ == "__main__":
    main()
