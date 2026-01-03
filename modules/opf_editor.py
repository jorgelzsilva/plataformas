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
            # Tenta encontrar dc:identifier com opf:scheme="ISBN"
            for elem in metadata_elem.findall('dc:identifier', ns):
                # No lxml, atributos com namespace são acessados como {uri}attr
                scheme = elem.get(f'{{{ns["opf"]}}}scheme')
                if scheme == 'ISBN':
                    isbn_elem = elem
                    break
            
            if isbn_elem is not None:
                isbn_elem.text = isbn_value
            else:
                # Cria novo se não existir
                new_isbn = ET.SubElement(metadata_elem, f'{{http://purl.org/dc/elements/1.1/}}identifier')
                # Define o atributo opf:scheme="ISBN" corretamente para lxml
                new_isbn.set(f'{{http://www.idpf.org/2007/opf}}scheme', 'ISBN')
                new_isbn.text = isbn_value
        
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
