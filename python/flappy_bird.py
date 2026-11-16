import random
import time
from collections import deque
from statistics import median

import pygame
import serial

# ============================================================
# 1. CONEXAO COM O ARDUINO
# ============================================================

PORTA = "COM6"  # Altere para a porta em que o Arduino aparece no Windows.
BAUD_RATE = 9600

try:
    arduino = serial.Serial(PORTA, BAUD_RATE, timeout=0)
except serial.SerialException as erro:
    print(f"Erro ao conectar com o Arduino na porta {PORTA}: {erro}")
    print("Feche o Monitor Serial da Arduino IDE e confira a porta em Ferramentas > Porta.")
    raise SystemExit(1)

# O Arduino pode reiniciar quando a conexao serial e aberta.
time.sleep(2)

distancia_cm = 20.0
buffer_serial = ""
leituras_sensor = deque(maxlen=5)


def atualizar_sensor():
    """Le os dados do Arduino e filtra pequenas oscilacoes do sensor."""
    global distancia_cm, buffer_serial

    quantidade = arduino.in_waiting
    if quantidade <= 0:
        return

    dados = arduino.read(quantidade)
    buffer_serial += dados.decode("utf-8", errors="ignore")

    # Evita que o buffer cresca indefinidamente com dados incompletos.
    if len(buffer_serial) > 300:
        buffer_serial = buffer_serial[-150:]

    while "\n" in buffer_serial:
        linha, buffer_serial = buffer_serial.split("\n", 1)

        try:
            valor = float(linha.strip())

            # O Arduino envia -1 quando nao recebe o eco do ultrassom.
            if 2 <= valor <= 60:
                leituras_sensor.append(valor)

                # Usa a mediana assim que houver pelo menos 3 leituras.
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

# Resolucao solicitada: 1366 x 768 pixels.
LARGURA = 1366
ALTURA = 768
CHAO_ALTURA = 52
ALTURA_TAMPA = 28
ALTURA_AREA_JOGO = ALTURA - CHAO_ALTURA

pygame.display.set_caption("Flappy Bird - Arduino Ultrassonico")

try:
    # Tela cheia na resolucao definida acima.
    tela = pygame.display.set_mode(
        (LARGURA, ALTURA),
        pygame.FULLSCREEN
    )
except pygame.error as erro:
    print(f"Nao foi possivel abrir a tela cheia: {erro}")
    print("Verifique se o monitor suporta 1366 x 768 pixels.")
    arduino.close()
    pygame.quit()
    raise SystemExit(1)

relogio = pygame.time.Clock()

# Fontes da interface, ampliadas para a resolucao 1366 x 768.
fonte_hud_titulo = pygame.font.SysFont("consolas", 16, bold=True)
fonte_hud_valor = pygame.font.SysFont("consolas", 27, bold=True)
fonte_game_over = pygame.font.SysFont("consolas", 40, bold=True)
fonte_game_over_menor = pygame.font.SysFont("consolas", 20, bold=True)

# Paleta de cores.
AZUL_ESCURO = (10, 39, 78)
AZUL_BORDA = (90, 185, 235)
BRANCO = (255, 255, 255)
AMARELO = (255, 215, 65)


# ============================================================
# 3. CONFIGURACOES DO PASSARO E DO CONTROLE
# ============================================================

PASSARO_X = int(LARGURA * 0.22)  # Aproximadamente 300 pixels.
PASSARO_RAIO = 15
passaro_y = ALTURA // 2

# Faixa ampla de controle da mao.
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

LARGURA_CANO = 82
ESPACO_CANOS = 190
VELOCIDADE = 230.0
INTERVALO_CANOS = 1.8


def criar_cano():
    """Cria um par de canos com abertura em uma posicao aleatoria."""
    centro_minimo = 180
    centro_maximo = ALTURA_AREA_JOGO - 180
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

    # Nuvens distribuidas por toda a largura da tela.
    nuvens = [
        (int(LARGURA * 0.02), 115, 0.90),
        (int(LARGURA * 0.19), 190, 0.75),
        (int(LARGURA * 0.37), 85, 0.70),
        (int(LARGURA * 0.54), 145, 0.85),
        (int(LARGURA * 0.72), 75, 0.75),
        (int(LARGURA * 0.86), 185, 0.90),
        (int(LARGURA * 0.94), 95, 0.65)
    ]

    for x, y, escala in nuvens:
        desenhar_nuvem(superficie, x, y, escala)

    # Predios ao fundo.
    base_predios = ALTURA_AREA_JOGO - 82

    for indice, x in enumerate(range(-5, LARGURA, 58)):
        largura = 39
        altura = 65 + (indice * 37 % 100)
        topo = base_predios - altura

        pygame.draw.rect(
            superficie,
            (55, 125, 180),
            (x, topo, largura, altura)
        )

        # Janelas dos predios.
        for wx in range(x + 8, x + largura - 4, 12):
            for wy in range(topo + 12, base_predios - 5, 19):
                pygame.draw.rect(
                    superficie,
                    (125, 190, 220),
                    (wx, wy, 5, 8)
                )

    # Vegetacao em camadas.
    for indice, x in enumerate(range(-60, LARGURA + 60, 105)):
        cor = (35 + (indice % 2) * 12, 143, 94)

        pygame.draw.ellipse(
            superficie,
            cor,
            (x, ALTURA_AREA_JOGO - 122, 130, 100)
        )

        pygame.draw.ellipse(
            superficie,
            (75, 190, 105),
            (x + 19, ALTURA_AREA_JOGO - 112, 75, 55)
        )


# O fundo e estatico, entao e desenhado uma unica vez para poupar processamento.
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
        (x + 8, y, LARGURA_CANO - 16, altura)
    )

    # Corpo verde.
    pygame.draw.rect(
        superficie,
        (25, 155, 65),
        (x + 11, y + 3, LARGURA_CANO - 22, altura - 6)
    )

    # Reflexos e sombra lateral.
    pygame.draw.rect(
        superficie,
        (133, 244, 88),
        (x + 14, y + 3, 11, altura - 6)
    )

    pygame.draw.rect(
        superficie,
        (75, 205, 65),
        (x + 29, y + 3, 10, altura - 6)
    )

    pygame.draw.rect(
        superficie,
        (12, 105, 53),
        (x + LARGURA_CANO - 25, y + 3, 10, altura - 6)
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
        (x + 8, y + 5, 15, ALTURA_TAMPA - 10)
    )

    pygame.draw.rect(
        superficie,
        (80, 215, 70),
        (x + 28, y + 5, 14, ALTURA_TAMPA - 10)
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
        (0, y + 9, LARGURA, CHAO_ALTURA - 9)
    )

    # Grama e faixa iluminada.
    pygame.draw.rect(superficie, (65, 180, 60), (0, y, LARGURA, 11))
    pygame.draw.rect(superficie, (155, 235, 75), (0, y, LARGURA, 4))

    # Textura do chao, com movimento para dar sensacao de velocidade.
    deslocamento = int(deslocamento % 26)
    for x in range(-26, LARGURA + 26, 26):
        xx = x - deslocamento

        pygame.draw.rect(
            superficie,
            (160, 95, 50),
            (xx + 3, y + 16, 14, 8)
        )
        pygame.draw.rect(
            superficie,
            (90, 48, 32),
            (xx + 12, y + 31, 10, 7)
        )


def desenhar_painel(superficie, x, titulo, valor, largura):
    painel = pygame.Rect(x, 18, largura, 76)

    pygame.draw.rect(
        superficie,
        AZUL_ESCURO,
        painel,
        border_radius=12
    )
    pygame.draw.rect(
        superficie,
        AZUL_BORDA,
        painel,
        2,
        border_radius=12
    )

    texto_titulo = fonte_hud_titulo.render(
        titulo, True, (190, 225, 255)
    )
    texto_valor = fonte_hud_valor.render(
        str(valor), True, AMARELO
    )

    superficie.blit(
        texto_titulo,
        (painel.centerx - texto_titulo.get_width() // 2, painel.y + 8)
    )
    superficie.blit(
        texto_valor,
        (painel.centerx - texto_valor.get_width() // 2, painel.y + 36)
    )


def desenhar_hud(superficie):
    largura_distancia = 190
    largura_pontos = 170
    largura_recorde = 190
    margem = 28

    # Distancia da mao, no canto esquerdo.
    desenhar_painel(
        superficie,
        margem,
        "DISTANCIA DA MAO",
        f"{distancia_cm:.1f} cm",
        largura_distancia
    )

    # Pontuacao, centralizada.
    desenhar_painel(
        superficie,
        (LARGURA - largura_pontos) // 2,
        "PONTOS",
        pontuacao,
        largura_pontos
    )

    # Recorde, no canto direito.
    desenhar_painel(
        superficie,
        LARGURA - largura_recorde - margem,
        "RECORDE",
        recorde,
        largura_recorde
    )


def desenhar_game_over(superficie):
    camada = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)
    camada.fill((5, 15, 35, 175))
    superficie.blit(camada, (0, 0))

    largura_painel = 540
    altura_painel = 230
    painel = pygame.Rect(
        (LARGURA - largura_painel) // 2,
        (ALTURA - altura_painel) // 2,
        largura_painel,
        altura_painel
    )

    pygame.draw.rect(
        superficie,
        AZUL_ESCURO,
        painel,
        border_radius=22
    )
    pygame.draw.rect(
        superficie,
        AMARELO,
        painel,
        3,
        border_radius=22
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
        (painel.centerx - titulo.get_width() // 2, painel.y + 35)
    )
    superficie.blit(
        texto,
        (painel.centerx - texto.get_width() // 2, painel.y + 105)
    )
    superficie.blit(
        reiniciar,
        (painel.centerx - reiniciar.get_width() // 2, painel.y + 160)
    )


# ============================================================
# 8. VARIAVEIS DA PARTIDA
# ============================================================

pontuacao = 0
recorde = 0  # O recorde permanece enquanto o programa estiver aberto.
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

        # Le os dados do sensor mesmo durante a tela de fim de jogo.
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

                    # Retangulos de colisao incluem as tampas.
                    cano_cima = pygame.Rect(
                        x,
                        0,
                        LARGURA_CANO,
                        limite_superior
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
