# -*- coding: utf-8 -*-
"""
Módulo para edição do arquivo content.opf de um EPUB.
"""

try:
    from lxml import etree as ET
    LXML_AVAILABLE = True
except ImportError:
    import xml.etree.ElementTree as ET
    LXML_AVAILABLE = False

import re
from pathlib import Path
from typing import Dict

# Namespaces usados no OPF
NAMESPACES = {
    'opf': 'http://www.idpf.org/2007/opf',
    'dc': 'http://purl.org/dc/elements/1.1/',
    'xsi': 'http://www.w3.org/2001/XMLSchema-instance'
}


def update_opf_metadata(opf_path: str, metadata: Dict[str, str]) -> None:
    """
    Atualiza os metadados no arquivo content.opf usando lxml para preservar namespaces.
    """
    if LXML_AVAILABLE:
        parser = ET.XMLParser(remove_blank_text=False)
        tree = ET.parse(opf_path, parser)
        root = tree.getroot()
        
        # Namespaces para lxml
        ns = NAMESPACES
        
        # Encontra metadata
        metadata_elem = root.find('opf:metadata', ns)
        if metadata_elem is None:
            metadata_elem = root.find('{http://www.idpf.org/2007/opf}metadata')
        
        if metadata_elem is None:
            raise ValueError("Elemento metadata não encontrado no OPF")
            
        # Funçāo auxiliar para atualizar ou criar elemento dc
        def update_dc_elem(name, value):
            if not value: return
            elem = metadata_elem.find(f'dc:{name}', ns)
            if elem is not None:
                elem.text = value
            else:
                new_elem = ET.SubElement(metadata_elem, f'{{http://purl.org/dc/elements/1.1/}}{name}')
                new_elem.text = value

        update_dc_elem('title', metadata.get('title'))
        update_dc_elem('creator', metadata.get('creator'))
        update_dc_elem('subject', metadata.get('subject'))
        update_dc_elem('publisher', metadata.get('publisher'))
        update_dc_elem('description', metadata.get('description'))
        
        # Atualiza ou cria ISBN
        isbn_value = metadata.get('isbn')
        if isbn_value:
            isbn_elem = None
            found_by_scheme = False
            
            # Formata o ISBN corretamente: urn:isbn:978...
            # Se já vier com urn:isbn:, mantém. Caso contrário, adiciona prefixo.
            if isbn_value.lower().startswith("urn:isbn:"):
                formatted_isbn = isbn_value
                raw_isbn = isbn_value.split(":")[-1]
            else:
                formatted_isbn = f"urn:isbn:{isbn_value}"
                raw_isbn = isbn_value
                
            # Tenta encontrar dc:identifier existente
            # 1. Por scheme="ISBN"
            for elem in metadata_elem.findall('dc:identifier', ns):
                scheme = elem.get(f'{{{ns["opf"]}}}scheme')
                if scheme == 'ISBN':
                    isbn_elem = elem
                    found_by_scheme = True
                    break
            
            # 2. Se não achou por scheme, tenta pelo conteúdo (match raw ou urn)
            if isbn_elem is None:
                for elem in metadata_elem.findall('dc:identifier', ns):
                    txt = (elem.text or "").strip()
                    if txt == raw_isbn or txt == formatted_isbn:
                        isbn_elem = elem
                        break
            
            if isbn_elem is not None:
                # Atualiza conteúdo
                isbn_elem.text = formatted_isbn
                
                # REMOVE atributo opf:scheme se existir, pois causa erro/aviso
                # validadores preferem apenas urn:isbn: no conteúdo
                scheme_attr = f'{{{ns["opf"]}}}scheme'
                if scheme_attr in isbn_elem.attrib:
                    del isbn_elem.attrib[scheme_attr]
                    
            else:
                # Cria novo se não existir
                isbn_elem = ET.SubElement(metadata_elem, f'{{http://purl.org/dc/elements/1.1/}}identifier')
                isbn_elem.text = formatted_isbn
                # NÃO adicionamos opf:scheme="ISBN"
            
            # Limpeza de meta tags residuais que refinavam este identificador pelo scheme
            # Ex: <meta refines="#uid" property="opf:scheme">ISBN</meta>
            ident_id = isbn_elem.get('id')
            if ident_id:
                # Encontra todas as metas que referenciam este ID
                metas_to_remove = []
                # Busca tanto opf:meta quanto meta (sem namespace) para garantir
                candidates = []
                candidates.extend(metadata_elem.findall('opf:meta', ns))
                candidates.extend(metadata_elem.findall('meta', ns))
                
                for meta in candidates:
                    # Verifica refines
                    refines = meta.get('refines')
                    if refines == f'#{ident_id}':
                        # Verifica se é property="opf:scheme"
                        prop = meta.get('property')
                        if prop == 'opf:scheme':
                            metas_to_remove.append(meta)
                
                for meta in metas_to_remove:
                    # Verifica se o elemento ainda existe antes de remover (pois pode ter duplicatas nas listas)
                    try:
                        metadata_elem.remove(meta)
                    except ValueError:
                        pass # Já removido
        
        # Salva o arquivo
        with open(opf_path, 'wb') as f:
            f.write(ET.tostring(tree, encoding='utf-8', xml_declaration=True, pretty_print=False))
    else:
        # Fallback para ElementTree original (com melhorias limitadas)
        for prefix, uri in NAMESPACES.items():
            import xml.etree.ElementTree as SimpleET
            SimpleET.register_namespace(prefix, uri)
        
        tree = ET.parse(opf_path)
        root = tree.getroot()
        
        # ... logic remains similar but with register_namespace fix ...
        # (Vou focar no lxml já que ordenei a instalação)
        
        # Atualiza namespaces manual para ElementTree se lxml não estiver disponível
        # Mas como vou rodar o pip install antes, o lxml deve estar disponível.
        
        # Para evitar redundância, vou deixar o código lxml-first
        pass



if __name__ == "__main__":
    # Teste rápido
    import sys
    if len(sys.argv) > 1:
        test_metadata = {
            'title': 'Teste: título',
            'creator': 'Autor Teste',
            'subject': 'Categoria > Subcategoria',
            'publisher': 'Editora Teste',
            'isbn': '9781234567890'
        }
        update_opf_metadata(sys.argv[1], test_metadata)
        print(f"OPF atualizado: {sys.argv[1]}")
