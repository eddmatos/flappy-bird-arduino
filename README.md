# 🐦 Flappy Bird com Arduino UNO

Um jogo interativo inspirado no clássico Flappy Bird, desenvolvido utilizando **Python, C++ e Arduino UNO**.

O projeto utiliza um sensor ultrassônico HC-SR04 para detectar a distância da mão do jogador e controlar a altura do pássaro em tempo real.

## 🎮 Demonstração

O jogador controla o personagem movimentando a mão diante do sensor ultrassônico:

- Aproximar a mão: o pássaro desce.
- Afastar a mão: o pássaro sobe.

O objetivo é desviar dos obstáculos, atravessar os canos e conseguir a maior pontuação possível!

## ✨ Funcionalidades

- Controle do personagem através de movimentos da mão.
- Comunicação serial entre Arduino e Python.
- Leitura de distância em tempo real.
- Filtro de leituras para reduzir oscilações do sensor.
- Movimentação gradual e calibrável.
- Obstáculos gerados continuamente.
- Sistema de pontuação.
- Recorde da partida.
- Detecção de colisões.
- Personagem e cenário com estilo pixel art.
- Animação das asas do pássaro.
- Interface gráfica personalizada.
- Modo de tela cheia.
- Sistema de reinicialização da partida.

## 🛠️ Tecnologias utilizadas

| Tecnologia | Finalidade |
|---|---|
| Python | Lógica e funcionamento do jogo |
| C++ | Programação do Arduino UNO |
| Pygame | Interface gráfica e animações |
| PySerial | Comunicação serial |
| Arduino UNO | Plataforma de hardware |
| HC-SR04 | Medição de distância |

## 📂 Estrutura do projeto

```text
flappy bird/
│
├── arduino/
│   └── flappybird.ino
│
├── python/
│   ├── flappy_bird.py
│   └── requirements.txt
│
└── README.md
```

## 🔌 Componentes eletrônicos

- 1 Arduino UNO.
- 1 sensor ultrassônico HC-SR04.
- Jumpers.
- 1 cabo USB para comunicação com o computador.

## ⚡ Ligações do sensor ultrassônico

| HC-SR04 | Arduino UNO |
|---|---|
| VCC | 5V |
| GND | GND |
| TRIG | Conforme configuração do código |
| ECHO | Conforme configuração do código |

## 💻 Programação do Arduino em C++

O arquivo `arduino/flappybird.ino` contém o código desenvolvido em C++, utilizando a API Arduino.

Suas principais responsabilidades são:

- Configurar os pinos do sensor ultrassônico.
- Enviar pulsos ultrassônicos.
- Calcular a distância da mão.
- Transmitir as medições pela comunicação serial.

## 🐍 Programação do jogo em Python

O arquivo `python/flappy_bird.py` contém a implementação do jogo utilizando Pygame.

Suas principais responsabilidades são:

- Receber os dados enviados pelo Arduino.
- Interpretar as distâncias medidas pelo sensor.
- Controlar a altura do personagem.
- Gerenciar os obstáculos e colisões.
- Calcular a pontuação e o recorde.
- Renderizar os gráficos e animações.

## 🚀 Como executar o projeto

### 1. Pré-requisitos

Instale os seguintes programas:

- Python.
- Visual Studio Code ou Arduino IDE.
- Arduino UNO conectado ao computador.

### 2. Instale as dependências Python

Abra o terminal na pasta principal do projeto e execute:

```bash
py -m pip install -r python/requirements.txt
```

### 3. Configure o Arduino

1. Abra o arquivo `arduino/flappybird.ino`.
2. Selecione a placa Arduino UNO.
3. Selecione a porta serial correspondente.
4. Carregue o código na placa.

### 4. Configure a comunicação serial

Abra `python/flappy_bird.py` e confira a configuração:

```python
PORTA = "COM6"
BAUD_RATE = 9600
```

Altere a porta COM caso seu Arduino esteja conectado em outra.

Feche o Monitor Serial da Arduino IDE antes de iniciar o jogo.

### 5. Execute o jogo

No terminal do VS Code, execute:

```bash
py python/flappy_bird.py
```

## 🕹️ Controles

| Ação | Comando |
|---|---|
| Fazer o pássaro descer | Aproximar a mão |
| Fazer o pássaro subir | Afastar a mão |
| Reiniciar a partida | ESPAÇO |
| Sair do jogo | ESC |

## 🎯 Objetivo do projeto

Desenvolver um jogo interativo que integra programação, eletrônica e desenvolvimento de jogos, explorando a comunicação entre hardware e software.

O projeto demonstra como sensores físicos podem ser utilizados como dispositivos de entrada para controlar aplicações desenvolvidas em Python.

## 👨‍💻 Desenvolvimento

Projeto desenvolvido utilizando Python, C++, Pygame e Arduino UNO.

**Flappy Bird com controle ultrassônico — uma experiência interativa entre eletrônica e programação.**