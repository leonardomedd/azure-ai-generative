import os
import json
import argparse
import time
from datetime import datetime
from typing import List, Dict, Any
import io  # Adicionado para manipulação de fluxos de bytes

import requests
from azure.core.credentials import AzureKeyCredential
from openai import AzureOpenAI

# Tente usar a versão mais recente da API de visão
try:
    from azure.ai.vision import VisionServiceOptions, ImageAnalysisOptions, ImageAnalysisService
    from azure.ai.vision.imageanalysis import VisualFeatures
    USE_NEW_VISION_API = True
except ImportError:
    # Fallback para a API mais antiga
    from azure.cognitiveservices.vision.computervision import ComputerVisionClient
    from msrest.authentication import CognitiveServicesCredentials
    USE_NEW_VISION_API = False
    print("Usando a API Computer Vision legacy. Considere atualizar para a versão mais recente.")

class AzureVisionOpenAIIntegration:
    """
    Classe principal para a integração dos serviços Azure Computer Vision e Azure OpenAI.
    """
    def __init__(self, config_path: str = "config.json"):
        """
        Inicializa a instância com as configurações dos serviços Azure.
        
        Args:
            config_path: Caminho para o arquivo de configuração JSON
        """
        self.config = self._load_config(config_path)
        self.vision_client = self._initialize_vision_client()
        self.openai_client = self._initialize_openai_client()
        self._setup_directories()
        
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """
        Carrega as configurações do arquivo JSON.
        
        Args:
            config_path: Caminho para o arquivo de configuração
            
        Returns:
            Dicionário com as configurações
        """
        try:
            with open(config_path, 'r') as file:
                return json.load(file)
        except FileNotFoundError:
            print(f"Arquivo de configuração '{config_path}' não encontrado.")
            print("Criando arquivo de configuração de exemplo...")
            
            example_config = {
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
            
            with open(config_path, 'w') as file:
                json.dump(example_config, file, indent=4)
                
            print(f"Arquivo de configuração de exemplo criado em '{config_path}'.")
            print("Por favor, edite-o com suas credenciais antes de executar o programa novamente.")
            exit(1)
    
    def _initialize_vision_client(self):
        """
        Inicializa o cliente do Azure Computer Vision.
        
        Returns:
            Cliente do Azure Computer Vision
        """
        vision_endpoint = self.config["vision"]["endpoint"]
        vision_key = self.config["vision"]["api_key"]
        
        if USE_NEW_VISION_API:
            service_options = VisionServiceOptions(vision_endpoint, vision_key)
            return ImageAnalysisService(service_options)
        else:
            # Para a API legacy
            return ComputerVisionClient(
                endpoint=vision_endpoint,
                credentials=CognitiveServicesCredentials(vision_key)
            )
    
    def _initialize_openai_client(self) -> AzureOpenAI:
        """
        Inicializa o cliente do Azure OpenAI.
        
        Returns:
            Cliente do Azure OpenAI
        """
        openai_endpoint = self.config["openai"]["endpoint"]
        openai_key = self.config["openai"]["api_key"]
        api_version = self.config["openai"].get("api_version", "2023-12-01-preview")
        
        return AzureOpenAI(
            azure_endpoint=openai_endpoint,
            api_key=openai_key,
            api_version=api_version
        )
    
    def _setup_directories(self) -> None:
        """
        Cria as pastas input e output se não existirem.
        """
        os.makedirs("input", exist_ok=True)
        os.makedirs("output", exist_ok=True)
        
    def analyze_image(self, image_path: str) -> Dict[str, Any]:
        """
        Analisa uma imagem usando o Azure Computer Vision.
        
        Args:
            image_path: Caminho para a imagem a ser analisada
            
        Returns:
            Dicionário com os resultados da análise
        """
        print(f"Analisando imagem: {image_path}")
        
        # Lê o arquivo de imagem
        with open(image_path, "rb") as image_file:
            image_data = image_file.read()
        
        if USE_NEW_VISION_API:
            # Usando a API mais recente
            analysis_options = ImageAnalysisOptions()
            analysis_options.features = (
                VisualFeatures.CAPTION | 
                VisualFeatures.DENSE_CAPTIONS | 
                VisualFeatures.TAGS | 
                VisualFeatures.OBJECTS
            )
            analysis_options.language = "pt"
            analysis_options.model_version = "latest"
            
            result = self.vision_client.analyze(
                image_data=image_data,
                options=analysis_options
            )
            
            # Organiza os resultados
            analysis_result = {
                "caption": result.caption.text if result.caption else "",
                "confidence": result.caption.confidence if result.caption else 0,
                "dense_captions": [
                    {"text": caption.text, "confidence": caption.confidence}
                    for caption in (result.dense_captions or [])
                ],
                "tags": [
                    {"name": tag.name, "confidence": tag.confidence}
                    for tag in (result.tags or [])
                ],
                "objects": [
                    {
                        "name": obj.name, 
                        "confidence": obj.confidence,
                        "bounding_box": {
                            "x": obj.bounding_box.x,
                            "y": obj.bounding_box.y,
                            "width": obj.bounding_box.width,
                            "height": obj.bounding_box.height
                        }
                    }
                    for obj in (result.objects or [])
                ]
            }
        else:
            # Usando a API legacy
            language = "pt"
            max_descriptions = 3
            
            # Cria um fluxo de bytes a partir dos dados lidos
            image_stream = io.BytesIO(image_data)
            
            # Análise da imagem - usando os métodos in_stream que aceitam fluxo
            describe_results = self.vision_client.describe_image_in_stream(image_stream, max_descriptions, language)
            
            # Reinicia o fluxo para reutilizá-lo
            image_stream.seek(0)
            tags_results = self.vision_client.tag_image_in_stream(image_stream, language)
            
            # Reinicia o fluxo novamente
            image_stream.seek(0)
            detect_objects_results = self.vision_client.detect_objects_in_stream(image_stream)
            
            # Organiza os resultados
            analysis_result = {
                "caption": describe_results.captions[0].text if describe_results.captions else "",
                "confidence": describe_results.captions[0].confidence if describe_results.captions else 0,
                "dense_captions": [
                    {"text": caption.text, "confidence": caption.confidence}
                    for caption in describe_results.captions
                ],
                "tags": [
                    {"name": tag.name, "confidence": tag.confidence}
                    for tag in tags_results.tags
                ],
                "objects": [
                    {
                        "name": obj.object_property, 
                        "confidence": obj.confidence,
                        "bounding_box": {
                            "x": obj.rectangle.x,
                            "y": obj.rectangle.y,
                            "width": obj.rectangle.w,
                            "height": obj.rectangle.h
                        }
                    }
                    for obj in detect_objects_results.objects
                ]
            }
        
        return analysis_result
    
    def generate_text(self, analysis_result: Dict[str, Any]) -> str:
        """
        Gera texto descritivo baseado na análise da imagem usando o Azure OpenAI.
        
        Args:
            analysis_result: Resultados da análise da imagem
            
        Returns:
            Texto gerado
        """
        print("Gerando descrição detalhada com GPT-4o...")
        
        # Preparando o prompt para o modelo
        prompt = f"""
        Você é um assistente especializado em descrever imagens de forma detalhada e contextualizada.
        
        Analise os seguintes dados extraídos de uma imagem usando o Azure Computer Vision e forneça:
        1. Uma descrição detalhada da imagem
        2. Um contexto possível para a imagem
        3. Pontos de interesse na imagem
        4. Possíveis usos ou aplicações para esta imagem
        
        Dados da análise:
        - Legenda principal: {analysis_result["caption"]}
        - Confiança da legenda: {analysis_result["confidence"]}
        - Legendas detalhadas: {[dc["text"] for dc in analysis_result["dense_captions"]]}
        - Tags identificadas: {[tag["name"] for tag in analysis_result["tags"]]}
        - Objetos detectados: {[obj["name"] for obj in analysis_result["objects"]]}
        
        Forneça sua resposta em português, de forma estruturada e completa.
        """
        
        # Enviando para o modelo GPT-4o
        deployment_name = self.config["openai"]["deployment_name"]
        
        try:
            response = self.openai_client.chat.completions.create(
                model=deployment_name,
                messages=[
                    {"role": "system", "content": "Você é um assistente especializado em análise e descrição de imagens."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            
            return response.choices[0].message.content
        except Exception as e:
            print(f"Erro ao gerar texto com o OpenAI: {str(e)}")
            return f"Não foi possível gerar uma descrição. Erro: {str(e)}"
    
    def process_image(self, image_path: str) -> Dict[str, Any]:
        """
        Processa uma imagem, realizando análise e geração de texto.
        
        Args:
            image_path: Caminho para a imagem a ser processada
            
        Returns:
            Dicionário com os resultados do processamento
        """
        try:
            # Analisa a imagem
            analysis_result = self.analyze_image(image_path)
            
            # Gera texto baseado na análise
            generated_text = self.generate_text(analysis_result)
            
            # Compila os resultados
            result = {
                "timestamp": datetime.now().isoformat(),
                "image_path": image_path,
                "analysis": analysis_result,
                "generated_text": generated_text
            }
            
            # Salva os resultados
            self._save_result(result, image_path)
            
            return result
        
        except Exception as e:
            print(f"Erro ao processar a imagem {image_path}: {str(e)}")
            return {
                "timestamp": datetime.now().isoformat(),
                "image_path": image_path,
                "error": str(e)
            }
    
    def _save_result(self, result: Dict[str, Any], image_path: str) -> None:
        """
        Salva o resultado do processamento em um arquivo JSON.
        
        Args:
            result: Resultado do processamento
            image_path: Caminho da imagem processada
        """
        # Cria um nome de arquivo baseado no nome da imagem original
        base_name = os.path.basename(image_path)
        file_name = os.path.splitext(base_name)[0]
        output_path = f"output/{file_name}_{int(time.time())}.json"
        
        # Salva o resultado
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=4)
            
        print(f"Resultado salvo em: {output_path}")
    
    def process_all_images(self) -> None:
        """
        Processa todas as imagens na pasta input.
        """
        input_dir = "input"
        image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.gif']
        
        # Lista todos os arquivos na pasta input
        files = os.listdir(input_dir)
        image_files = [f for f in files if os.path.splitext(f.lower())[1] in image_extensions]
        
        if not image_files:
            print("Nenhuma imagem encontrada na pasta 'input'.")
            return
        
        print(f"Encontradas {len(image_files)} imagens para processar.")
        
        # Processa cada imagem
        for image_file in image_files:
            image_path = os.path.join(input_dir, image_file)
            print(f"\nProcessando: {image_file}")
            self.process_image(image_path)
            
        print("\nProcessamento concluído!")


def main():
    """
    Função principal para execução do script.
    """
    parser = argparse.ArgumentParser(description="Azure Vision OpenAI Integration")
    parser.add_argument("--config", default="config.json", help="Caminho para o arquivo de configuração")
    parser.add_argument("--image", help="Caminho para uma imagem específica a ser processada")
    args = parser.parse_args()
    
    # Inicializa o integrador
    integrator = AzureVisionOpenAIIntegration(args.config)
    
    # Processa uma imagem específica ou todas as imagens na pasta input
    if args.image:
        if os.path.exists(args.image):
            integrator.process_image(args.image)
        else:
            print(f"Imagem não encontrada: {args.image}")
    else:
        integrator.process_all_images()


if __name__ == "__main__":
    main()