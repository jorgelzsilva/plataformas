# Projeto Plataformas

Este projeto é uma ferramenta de automação para edição de metadados de arquivos EPUB e inserção de marcas d'água (watermarks) identificadoras para diferentes plataformas (Amazon, Apple, Google, etc.).

## 🚀 Funcionalidades

- **Extração de Metadados**: Decodifica arquivos MHTML para extrair informações como Título, Autor, ISBN, Assunto e Descrição.
- **Edição de EPUB**: Atualiza o arquivo `content.opf` com os metadados extraídos, mantendo a integridade dos namespaces XML.
- **Gerenciamento de Marcas**: Insere símbolos identificadores aleatórios em arquivos XHTML selecionados para rastreabilidade por plataforma.
- **Verificação de Integridade**: Valida se o conteúdo do EPUB (contagem de caracteres) permanece inalterado após as modificações, exceto pelas marcas inseridas.

## 📁 Estrutura do Projeto

- `main.py`: Script principal que coordena o fluxo de extração, edição e marcação.
- `config.py`: Configurações centralizadas, como símbolos de plataformas e padrões de arquivos.
- `modules/`:
  - `mhtml_parser.py`: Lógica para decodificação e parsing de arquivos MHTML.
  - `opf_editor.py`: Manipulação do arquivo `content.opf` do EPUB usando `lxml`.
  - `watermark_manager.py`: Lógica para seleção de arquivos e inserção de marcas d'água.
  - `integrity_checker.py`: Ferramentas para contagem de caracteres e validação de integridade.

## 🛠️ Instalação

### Pré-requisitos
- Python 3.8 ou superior
- Pip (gerenciador de pacotes do Python)

### Passo a Passo

1. **Clonar o repositório**:
   ```bash
   git clone https://github.com/jorgelzsilva/plataformas.git
   cd plataformas
   ```

2. **Criar um ambiente virtual (recomendado)**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # No Windows: venv\Scripts\activate
   ```

3. **Instalar dependências**:
   ```bash
   pip install -r requirements.txt
   ```

## 💻 Como Usar

Para executar o processo completo, você pode simplesmente colocar os arquivos na pasta `input/` e rodar:

```bash
python main.py
```

Ou, se preferir especificar caminhos customizados:

```bash
python main.py "caminho/para/arquivo.mhtml" "caminho/para/livro.epub"
```

O script irá:
1. Extrair metadados do MHTML.
2. Criar cópias do EPUB para cada plataforma configurada em `config.py`.
3. Atualizar os metadados e inserir as marcas correspondentes em cada cópia.
4. Verificar a integridade de todas as versões geradas.
5. Salvar os resultados na pasta `output/`.

## ⚙️ Configuração

Você pode ajustar o comportamento do script no arquivo `config.py`:
- `PLATFORM_MARKS`: Define os símbolos usados para cada plataforma.
- `NUM_FILES_TO_MARK`: Quantidade de arquivos XHTML que receberão a marca em cada EPUB.
- `ELIGIBLE_FILE_PATTERN`: Regex para identificar quais arquivos podem ser marcados.

---
Desenvolvido para automação de fluxos editorial e distribuição multicanal.
