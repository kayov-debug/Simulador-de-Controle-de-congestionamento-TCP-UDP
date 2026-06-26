# Simulador de Controle de Congestionamento TCP/UDP

Este projeto é um simulador de rede desenvolvido para estudar o comportamento de congestionamento em ambientes com protocolos TCP e UDP. A ideia é demonstrar como diferentes estratégias de envio, limitação de taxa e perda de pacotes influenciam a comunicação entre clientes e servidor.

🔗 Repositório GitHub: https://github.com/kayov-debug/Simulador-de-Controle-de-congestionamento-TCP-UDP.git

🎥 Vídeo do projeto: https://youtu.be/UavewL2CnvI

## 📌 Objetivo

O simulador permite:

- testar o funcionamento de servidores e clientes TCP/UDP;
- simular cenários com diferentes taxas de envio e limitação de fluxo;
- gerar métricas de desempenho para análise;
- visualizar os resultados de forma mais intuitiva.

## 🚀 Funcionalidades

- Suporte a protocolos TCP e UDP;
- Simulação de múltiplos clientes simultâneos;
- Controle de taxa de envio;
- Configuração de perda de pacotes;
- Geração de arquivos de métricas;
- Visualização dos resultados por meio de gráficos.

## 🛠️ Tecnologias

- Python
- Socket TCP/UDP
- Matplotlib
- Threading para execução simultânea de clientes

## ▶️ Como executar

### 1. Instalar dependências

```bash
pip install -r requirements.txt
```

### 2. Iniciar o servidor

```bash
python run_server.py --protocol udp
```

Ou para TCP:

```bash
python run_server.py --protocol tcp
```

### 3. Iniciar os clientes

```bash
python run_clients.py --protocol udp --clients 5
```

Ou para TCP:

```bash
python run_clients.py --protocol tcp --clients 5
```

## 📁 Estrutura do projeto

```text
simulador_congestionamento/
├── cliente/           # Implementações dos clientes TCP/UDP
├── servidor/          # Implementações dos servidores TCP/UDP
├── analise/           # Ferramentas de visualização e análise
├── utilitarios/       # Métricas e rate limiter
├── run_server.py      # Script para iniciar o servidor
├── run_clients.py     # Script para iniciar os clientes
└── requirements.txt   # Dependências do projeto
```

## 📈 Resultados

As métricas geradas podem ser encontradas em arquivos JSON dentro da pasta de resultados e visualizadas com os scripts de análise.

## 👨‍💻 Autores

Projeto desenvolvido para fins acadêmicos no contexto de estudos de redes.
