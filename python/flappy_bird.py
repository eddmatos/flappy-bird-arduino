import random
import time
from collections import deque
from statistics import median

import pygame
import serial

# ============================================================
# 1. CONEXAO COM O ARDUINO
# ============================================================

PORTA = "COM6"       # Altere caso o Arduino esteja em outra porta COM
BAUD_RATE = 9600

try:
    arduino = serial.Serial(PORTA, BAUD_RATE, timeout=0)
except serial.SerialException as erro:
    print(f"Erro ao conectar com o Arduino na porta {PORTA}: {erro}")
    print("Feche o Monitor Serial da Arduino IDE e confira a porta em Ferramentas > Porta.")
    raise SystemExit(1)

# O Arduino reinicia quando a conexao serial e aberta.
time.sleep(2)

# Ultima distancia valida recebida do sensor.
distancia_cm = 20.0
buffer_serial = ""
leituras_sensor = deque(maxlen=5)


def atualizar_sensor():
    """Le dados enviados pelo Arduino e filtra pequenas oscilacoes."""
    global distancia_cm, buffer_serial

    quantidade = arduino.in_waiting
    if quantidade <= 0:
        return

    dados = arduino.read(quantidade)
    buffer_serial += dados.decode("utf-8", errors="ignore")

    # Evita que o buffer cresca indefinidamente se chegar algum dado incompleto.
    if len(buffer_serial) > 300:
        buffer_serial = buffer_serial[-150:]

    while "\n" in buffer_serial:
        linha, buffer_serial = buffer_serial.split("\n", 1)

        try:
            valor = float(linha.strip())

            # O Arduino envia -1 quando nao recebe o eco do ultrassom.
            if 2 <= valor <= 60:
                leituras_sensor.append(valor)

                # Comeca a filtrar assim que houver pelo menos 3 amostras.
                if len(leituras_sensor) >= 3:
                    distancia_cm = median(leituras_sensor)

        except ValueError:
            # Ignora linhas vazias ou dados que nao sejam numeros.
            continue


# ============================================================
# 2. CONFIGURACOES DO PYGAME E DA TELA
# ============================================================

pygame.init()
pygame.font.init()

LARGURA = 480
ALTURA = 640
CHAO_ALTURA = 42
ALTURA_TAMPA = 24
ALTURA_AREA_JOGO = ALTURA - CHAO_ALTURA

pygame.display.set_caption("Flappy Bird - Arduino Ultrassonico")

# Tenta abrir em tela cheia mantendo a resolucao logica e a proporcao.
try:
    tela = pygame.display.set_mode(
        (LARGURA, ALTURA),
        pygame.FULLSCREEN | pygame.SCALED
    )
except (pygame.error, AttributeError):
    # Compatibilidade com versoes antigas do Pygame sem SCALED.
    tela = pygame.display.set_mode((LARGURA, ALTURA), pygame.FULLSCREEN)

relogio = pygame.time.Clock()

# Fontes da interface.
fonte_hud_titulo = pygame.font.SysFont("consolas", 13, bold=True)
fonte_hud_valor = pygame.font.SysFont("consolas", 22, bold=True)
fonte_game_over = pygame.font.SysFont("consolas", 30, bold=True)
fonte_game_over_menor = pygame.font.SysFont("consolas", 15, bold=True)

# Paleta de cores.
AZUL_ESCURO = (10, 39, 78)
AZUL_BORDA = (90, 185, 235)
BRANCO = (255, 255, 255)
AMARELO = (255, 215, 65)

# ============================================================
# 3. CONFIGURACOES DO PASSARO E DO CONTROLE
# ============================================================

PASSARO_X = 110
PASSARO_RAIO = 15
passaro_y = ALTURA // 2

# Faixa ampla: a mao pode se movimentar entre 5 e 50 cm.
DISTANCIA_MIN = 5.0
DISTANCIA_MAX = 50.0

# Limites do centro do passaro na tela.
ALTURA_MIN = 55
ALTURA_MAX = ALTURA_AREA_JOGO - 38

# Quanto menor o valor, mais gradual fica o movimento.
FATOR_SUAVIZACAO = 0.08


def controlar_passaro():
    """Converte a distancia da mao em altura, com movimento gradual."""
    global passaro_y

    distancia = max(
        DISTANCIA_MIN,
        min(DISTANCIA_MAX, distancia_cm)
    )

    # Controle invertido: mao perto = passaro desce; mao longe = sobe.
    proporcao = 1 - (
        (distancia - DISTANCIA_MIN) /
        (DISTANCIA_MAX - DISTANCIA_MIN)
    )

    altura_desejada = (
        ALTURA_MIN + proporcao * (ALTURA_MAX - ALTURA_MIN)
    )

    passaro_y += (
        altura_desejada - passaro_y
    ) * FATOR_SUAVIZACAO


# ============================================================
# 4. CONFIGURACOES DOS CANOS
# ============================================================

LARGURA_CANO = 70
ESPACO_CANOS = 175
VELOCIDADE = 210.0
INTERVALO_CANOS = 1.5


def criar_cano():
    """Cria um par de canos com abertura em uma posicao aleatoria."""
    centro_minimo = 165
    centro_maximo = ALTURA_AREA_JOGO - 165
    centro = random.randint(centro_minimo, centro_maximo)

    return {
        "x": float(LARGURA),
        "centro": centro,
        "pontuado": False
    }


# ============================================================
# 5. FUNCOES VISUAIS: CENARIO
# ============================================================


def desenhar_nuvem(superficie, x, y, escala=1.0):
    sombra = (175, 218, 240)
    branco = (248, 253, 255)

    pygame.draw.ellipse(
        superficie,
        sombra,
        (int(x), int(y + 10 * escala),
         int(90 * escala), int(25 * escala))
    )

    partes = [
        (15, 8, 35, 30),
        (35, -5, 40, 40),
        (60, 8, 35, 30)
    ]

    for px, py, largura, altura in partes:
        pygame.draw.ellipse(
            superficie,
            branco,
            (int(x + px * escala),
             int(y + py * escala),
             int(largura * escala),
             int(altura * escala))
        )


def desenhar_fundo(superficie):
    """Desenha o ceu, as nuvens, a cidade e a vegetacao distante."""

    # Ceu em degradê.
    for y in range(ALTURA):
        proporcao = y / max(1, ALTURA - 1)
        cor = (
            int(35 + 85 * proporcao),
            int(145 + 85 * proporcao),
            int(220 + 25 * proporcao)
        )
        pygame.draw.line(superficie, cor, (0, y), (LARGURA, y))

    # Nuvens do cenario.
    desenhar_nuvem(superficie, 15, 115, 0.90)
    desenhar_nuvem(superficie, 245, 185, 0.75)
    desenhar_nuvem(superficie, 370, 85, 0.65)

    # Predios ao fundo.
    base_predios = ALTURA_AREA_JOGO - 66

    for indice, x in enumerate(range(-5, LARGURA, 43)):
        largura = 28
        altura = 55 + (indice * 29 % 58)
        topo = base_predios - altura

        pygame.draw.rect(
            superficie,
            (55, 125, 180),
            (x, topo, largura, altura)
        )

        # Janelas dos predios.
        for wx in range(x + 7, x + largura - 4, 9):
            for wy in range(topo + 9, base_predios - 5, 14):
                pygame.draw.rect(
                    superficie,
                    (125, 190, 220),
                    (wx, wy, 4, 6)
                )

    # Vegetacao em camadas.
    for indice, x in enumerate(range(-45, LARGURA + 30, 78)):
        cor = (35 + (indice % 2) * 12, 143, 94)

        pygame.draw.ellipse(
            superficie,
            cor,
            (x, ALTURA - 116, 105, 85)
        )

        pygame.draw.ellipse(
            superficie,
            (75, 190, 105),
            (x + 16, ALTURA - 105, 60, 44)
        )


# O fundo e estatico, entao desenhamos uma unica vez para poupar processamento.
fundo = pygame.Surface((LARGURA, ALTURA))
desenhar_fundo(fundo)


# ============================================================
# 6. FUNCOES VISUAIS: CANOS
# ============================================================


def desenhar_corpo_cano(superficie, x, y, altura):
    altura = int(altura)
    if altura <= 6:
        return

    # Contorno externo.
    pygame.draw.rect(
        superficie,
        (12, 62, 42),
        (x + 7, y, LARGURA_CANO - 14, altura)
    )

    # Corpo verde.
    pygame.draw.rect(
        superficie,
        (25, 155, 65),
        (x + 10, y + 3, LARGURA_CANO - 20, altura - 6)
    )

    # Reflexos e sombra lateral.
    pygame.draw.rect(
        superficie,
        (133, 244, 88),
        (x + 12, y + 3, 9, altura - 6)
    )

    pygame.draw.rect(
        superficie,
        (75, 205, 65),
        (x + 23, y + 3, 8, altura - 6)
    )

    pygame.draw.rect(
        superficie,
        (12, 105, 53),
        (x + LARGURA_CANO - 22, y + 3, 8, altura - 6)
    )


def desenhar_tampa_cano(superficie, x, y):
    # Borda escura da tampa.
    pygame.draw.rect(
        superficie,
        (8, 55, 37),
        (x, y, LARGURA_CANO, ALTURA_TAMPA)
    )

    # Interior.
    pygame.draw.rect(
        superficie,
        (30, 170, 70),
        (x + 3, y + 3, LARGURA_CANO - 6, ALTURA_TAMPA - 6)
    )

    # Brilhos.
    pygame.draw.rect(
        superficie,
        (160, 250, 95),
        (x + 7, y + 4, 12, ALTURA_TAMPA - 8)
    )

    pygame.draw.rect(
        superficie,
        (80, 215, 70),
        (x + 22, y + 4, 12, ALTURA_TAMPA - 8)
    )


def desenhar_cano_superior(superficie, x, limite):
    altura_corpo = max(0, limite - ALTURA_TAMPA)
    desenhar_corpo_cano(superficie, x, 0, altura_corpo)
    desenhar_tampa_cano(superficie, x, limite - ALTURA_TAMPA)


def desenhar_cano_inferior(superficie, x, inicio):
    desenhar_tampa_cano(superficie, x, inicio)

    y_corpo = inicio + ALTURA_TAMPA
    altura_corpo = ALTURA_AREA_JOGO - y_corpo
    desenhar_corpo_cano(superficie, x, y_corpo, altura_corpo)


# ============================================================
# 7. FUNCOES VISUAIS: PASSARO, CHAO E INTERFACE
# ============================================================


def desenhar_passaro(superficie, x, y):
    """Desenha um passaro amarelo com asa animada."""
    cx = int(x)
    cy = int(y)
    fase = (pygame.time.get_ticks() // 130) % 3
    posicoes_asas = [-9, 0, 8]
    asa_y = posicoes_asas[fase]

    contorno = (45, 39, 43)

    # Cauda.
    pygame.draw.polygon(
        superficie,
        contorno,
        [(cx - 15, cy), (cx - 29, cy - 8), (cx - 25, cy + 9)]
    )
    pygame.draw.polygon(
        superficie,
        (235, 125, 30),
        [(cx - 17, cy), (cx - 26, cy - 5), (cx - 23, cy + 6)]
    )

    # Asa animada.
    pygame.draw.polygon(
        superficie,
        contorno,
        [
            (cx - 8, cy + 2),
            (cx - 16, cy + asa_y),
            (cx + 1, cy + asa_y - 2),
            (cx + 5, cy + 7)
        ]
    )
    pygame.draw.polygon(
        superficie,
        (235, 132, 35),
        [
            (cx - 7, cy + 2),
            (cx - 14, cy + asa_y),
            (cx - 1, cy + asa_y),
            (cx + 2, cy + 6)
        ]
    )

    # Corpo externo e corpo amarelo.
    pygame.draw.ellipse(
        superficie,
        contorno,
        (cx - 20, cy - 17, 40, 35)
    )
    pygame.draw.ellipse(
        superficie,
        (255, 193, 40),
        (cx - 17, cy - 14, 34, 29)
    )

    # Barriga clara.
    pygame.draw.ellipse(
        superficie,
        (255, 245, 220),
        (cx - 8, cy + 3, 22, 11)
    )

    # Detalhe laranja no corpo.
    pygame.draw.rect(
        superficie,
        (240, 140, 30),
        (cx - 10, cy - 12, 8, 4)
    )

    # Olho.
    pygame.draw.circle(superficie, contorno, (cx + 9, cy - 7), 8)
    pygame.draw.circle(superficie, BRANCO, (cx + 9, cy - 7), 6)
    pygame.draw.circle(superficie, (25, 30, 40), (cx + 11, cy - 7), 3)

    # Bico.
    pygame.draw.polygon(
        superficie,
        contorno,
        [(cx + 14, cy - 1), (cx + 29, cy + 3), (cx + 14, cy + 9)]
    )
    pygame.draw.polygon(
        superficie,
        (255, 120, 35),
        [(cx + 16, cy), (cx + 26, cy + 3), (cx + 16, cy + 6)]
    )


def desenhar_chao(superficie, deslocamento):
    y = ALTURA_AREA_JOGO

    # Terra.
    pygame.draw.rect(
        superficie,
        (125, 73, 42),
        (0, y + 8, LARGURA, CHAO_ALTURA - 8)
    )

    # Grama e faixa iluminada.
    pygame.draw.rect(superficie, (65, 180, 60), (0, y, LARGURA, 10))
    pygame.draw.rect(superficie, (155, 235, 75), (0, y, LARGURA, 4))

    # Textura do chao, com movimento para dar sensacao de velocidade.
    deslocamento = int(deslocamento % 24)
    for x in range(-24, LARGURA + 24, 24):
        xx = x - deslocamento

        pygame.draw.rect(
            superficie,
            (160, 95, 50),
            (xx + 3, y + 14, 13, 7)
        )
        pygame.draw.rect(
            superficie,
            (90, 48, 32),
            (xx + 11, y + 27, 9, 6)
        )


def desenhar_painel(superficie, x, titulo, valor, largura):
    painel = pygame.Rect(x, 12, largura, 59)

    pygame.draw.rect(
        superficie,
        AZUL_ESCURO,
        painel,
        border_radius=10
    )
    pygame.draw.rect(
        superficie,
        AZUL_BORDA,
        painel,
        2,
        border_radius=10
    )

    texto_titulo = fonte_hud_titulo.render(
        titulo, True, (190, 225, 255)
    )
    texto_valor = fonte_hud_valor.render(
        str(valor), True, AMARELO
    )

    superficie.blit(
        texto_titulo,
        (painel.centerx - texto_titulo.get_width() // 2, painel.y + 5)
    )
    superficie.blit(
        texto_valor,
        (painel.centerx - texto_valor.get_width() // 2, painel.y + 26)
    )


def desenhar_hud(superficie):
    desenhar_painel(
        superficie, 8, "DISTANCIA", f"{distancia_cm:.1f} cm", 145
    )
    desenhar_painel(
        superficie, 176, "PONTOS", pontuacao, 128
    )
    desenhar_painel(
        superficie, 327, "RECORDE", recorde, 145
    )


def desenhar_game_over(superficie):
    camada = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)
    camada.fill((5, 15, 35, 165))
    superficie.blit(camada, (0, 0))

    painel = pygame.Rect(35, 245, LARGURA - 70, 155)

    pygame.draw.rect(
        superficie,
        AZUL_ESCURO,
        painel,
        border_radius=18
    )
    pygame.draw.rect(
        superficie,
        AMARELO,
        painel,
        3,
        border_radius=18
    )

    titulo = fonte_game_over.render(
        "FIM DE JOGO", True, (255, 105, 75)
    )
    texto = fonte_game_over_menor.render(
        f"PONTUACAO: {pontuacao}", True, BRANCO
    )
    reiniciar = fonte_game_over_menor.render(
        "PRESSIONE ESPACO PARA REINICIAR", True, AMARELO
    )

    superficie.blit(
        titulo,
        (painel.centerx - titulo.get_width() // 2, 265)
    )
    superficie.blit(
        texto,
        (painel.centerx - texto.get_width() // 2, 320)
    )
    superficie.blit(
        reiniciar,
        (painel.centerx - reiniciar.get_width() // 2, 355)
    )


# ============================================================
# 8. VARIAVEIS DA PARTIDA
# ============================================================

pontuacao = 0
recorde = 0  # Recorde permanece enquanto o programa estiver aberto.
canos = []
tempo_cano = 0.0
passaro_y = ALTURA // 2
deslocamento_chao = 0.0
jogando = True
jogando_partida = True


# ============================================================
# 9. LOOP PRINCIPAL
# ============================================================

try:
    while jogando:
        # Limita a 60 FPS e evita saltos grandes se houver uma travada.
        dt = min(relogio.tick(60) / 1000.0, 0.05)

        # Le dados do sensor mesmo durante a tela de fim de jogo.
        atualizar_sensor()

        # ----------------------------
        # Eventos do teclado e janela
        # ----------------------------
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                jogando = False

            elif evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_ESCAPE:
                    jogando = False

                elif evento.key == pygame.K_SPACE and not jogando_partida:
                    # Reinicia a partida sem zerar o recorde.
                    pontuacao = 0
                    canos = []
                    tempo_cano = 0.0
                    passaro_y = ALTURA // 2
                    deslocamento_chao = 0.0
                    jogando_partida = True

        if not jogando:
            break

        # ----------------------------
        # Atualizacao da partida
        # ----------------------------
        if jogando_partida:
            controlar_passaro()

            tempo_cano += dt
            if tempo_cano >= INTERVALO_CANOS:
                canos.append(criar_cano())
                tempo_cano = 0.0

            # Move os canos para a esquerda.
            for cano in canos:
                cano["x"] -= VELOCIDADE * dt

            # Remove canos que sairam da tela.
            canos = [
                cano for cano in canos
                if cano["x"] > -LARGURA_CANO
            ]

            deslocamento_chao += VELOCIDADE * dt

            # Area de colisao um pouco menor que o desenho do passaro.
            passaro_rect = pygame.Rect(
                PASSARO_X - 16,
                int(passaro_y) - 13,
                34,
                27
            )

            # Colisao com teto e chao.
            if (
                passaro_rect.top <= 0
                or passaro_rect.bottom >= ALTURA_AREA_JOGO
            ):
                jogando_partida = False
                recorde = max(recorde, pontuacao)

            # Colisao com canos e pontuacao.
            if jogando_partida:
                for cano in canos:
                    x = int(cano["x"])
                    limite_superior = (
                        cano["centro"] - ESPACO_CANOS // 2
                    )
                    inicio_inferior = (
                        cano["centro"] + ESPACO_CANOS // 2
                    )

                    # Retangulos de colisao incluem as tampas dos canos.
                    cano_cima = pygame.Rect(
                        x, 0, LARGURA_CANO, limite_superior
                    )
                    cano_baixo = pygame.Rect(
                        x,
                        inicio_inferior,
                        LARGURA_CANO,
                        ALTURA_AREA_JOGO - inicio_inferior
                    )

                    if (
                        passaro_rect.colliderect(cano_cima)
                        or passaro_rect.colliderect(cano_baixo)
                    ):
                        jogando_partida = False
                        recorde = max(recorde, pontuacao)
                        break

                    # Marca um ponto quando o cano passa pelo passaro.
                    if (
                        not cano["pontuado"]
                        and cano["x"] + LARGURA_CANO < PASSARO_X
                    ):
                        pontuacao += 1
                        cano["pontuado"] = True
                        recorde = max(recorde, pontuacao)

        # ----------------------------
        # Desenho de todos os elementos
        # ----------------------------
        tela.blit(fundo, (0, 0))

        for cano in canos:
            x = int(cano["x"])
            limite_superior = (
                cano["centro"] - ESPACO_CANOS // 2
            )
            inicio_inferior = (
                cano["centro"] + ESPACO_CANOS // 2
            )

            desenhar_cano_superior(tela, x, limite_superior)
            desenhar_cano_inferior(tela, x, inicio_inferior)

        desenhar_passaro(tela, PASSARO_X, passaro_y)
        desenhar_chao(tela, deslocamento_chao)
        desenhar_hud(tela)

        if not jogando_partida:
            desenhar_game_over(tela)

        pygame.display.flip()

finally:
    # Garante o fechamento da porta serial e do Pygame ao sair.
    if arduino.is_open:
        arduino.close()
    pygame.quit()
