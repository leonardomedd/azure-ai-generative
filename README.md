# 🌟 Projeto de Integração Azure OpenAI e Computer Vision 🌟

## 🚀 Visão Geral
Este projeto integra os serviços Azure OpenAI (GPT-4o) e Azure Computer Vision para análise de imagens e geração de texto contextual. O sistema permite que os usuários enviem imagens para obter descrições detalhadas e gerar respostas usando IA generativa.

## ✨ Funcionalidades
- 🖼️ Análise de imagens usando Azure Computer Vision
- 📝 Geração de descrições detalhadas e contextuais usando GPT-4o via Azure OpenAI
- 📊 Processamento de múltiplas imagens em lote
- 💾 Armazenamento de resultados em formato JSON

## 📂 Estrutura do Projeto
```
.
├── input/              # 📁 Pasta para imagens de entrada
├── output/             # 📁 Pasta para resultados processados
├── main.py             # 🔧 Script principal
├── .gitignore          # 🔒 Arquivo para ignorar arquivos sensíveis
└── README.md           # 📚 Documentação
```

> **⚠️ Nota de Segurança**: O arquivo `config.json` **não** está incluído no repositório por motivos de segurança, pois contém credenciais sensíveis. Você precisará criá-lo manualmente (veja a seção Instalação).

## 📋 Requisitos
- 🐍 Python 3.8 ou superior
- ☁️ Conta Azure com acesso aos serviços:
  - 👁️ Azure Computer Vision
  - 🧠 Azure OpenAI com acesso ao modelo GPT-4o

## 🔧 Instalação

### 1. Clone o repositório:
```bash
git clone https://github.com/leonardomedd/azure-ai-generative.git
cd azure-ai-generative
```

### 2. Crie e ative um ambiente virtual (opcional, mas recomendado):
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

### 3. Instale as dependências:
```bash
pip install -r requirements.txt
```

### 4. Crie e configure o arquivo `config.json` com suas credenciais Azure:
Crie um arquivo `config.json` no diretório raiz do projeto com o seguinte formato:

```json
{
    "vision": {
        "endpoint": "https://your-vision-service.cognitiveservices.azure.com/",
        "api_key": "your-vision-api-key"
    },
    "openai": {
        "endpoint": "https://your-openai-service.openai.azure.com/",
        "api_key": "your-openai-api-key",
        "api_version": "2023-12-01-preview",
        "deployment_name": "gpt-4o"
    }
}
```

#### Como obter as credenciais:
- 🔑 No Azure Portal, vá até o recurso Computer Vision e copie o endpoint e a `api_key` na seção "Keys and Endpoint"
- 🔄 Repita o processo para o recurso Azure OpenAI
- ✅ Certifique-se de que o `deployment_name` corresponde ao nome do deployment criado para o modelo GPT-4o no Azure OpenAI

## 📱 Uso

### Processamento de todas as imagens na pasta `input/`
Coloque as imagens que deseja processar na pasta `input/` e execute:
```bash
python main.py
```

### Processamento de uma imagem específica
```bash
python main.py --image caminho/para/imagem.jpg
```

### Especificar um arquivo de configuração alternativo
Se você criou o `config.json` em um local diferente, especifique o caminho:
```bash
python main.py --config caminho/para/config.json
```

## 📊 Detalhes dos Resultados
Os resultados são salvos na pasta `output/` como arquivos JSON contendo:
- ⏱️ **Timestamp**: Data e hora do processamento
- 🖼️ **Image Path**: Caminho da imagem processada
- 🔍 **Analysis**: Resultados da análise do Azure Computer Vision (legendas, tags, objetos detectados)
- 📝 **Generated Text**: Descrição detalhada gerada pelo GPT-4o


## 📬 Contato
- 🔗 **LinkedIn**: https://www.linkedin.com/in/leonardo-medeiros-de-almeida-996302254/
- 📧 **E-mail**: leonardomedd@gmail.com
