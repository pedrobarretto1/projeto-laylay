"""Cena 2D e conversão da pose em amostras para o firmware de host."""

from dataclasses import asdict, dataclass
import math

LARGURA_ARENA_CM = 160
ALTURA_ARENA_CM = 110
AVANCO_SENSOR_CM = 9
ALCANCE_SENSOR_CM = 65


@dataclass
class Corpo:
    x: float = 80
    y: float = 75
    yaw: float = 0
    roll: float = 0
    pitch: float = 0
    segurando: bool = False


@dataclass
class Obstaculo:
    x: float = 109
    y: float = 43
    raio: float = 6


def limitar(valor: float, minimo: float, maximo: float) -> float:
    return min(maximo, max(minimo, valor))


class Cena:
    def __init__(self) -> None:
        self.corpo = Corpo()
        self.obstaculo = Obstaculo()
        self._anterior = Corpo()
        self._velocidade = (0., 0.)
        self._velocidade_rodas = (0., 0.)

    def retrato(self) -> dict:
        return {"corpo": asdict(self.corpo), "obstaculo": asdict(self.obstaculo)}

    def atualizar(self, dados: dict) -> None:
        if not isinstance(dados, dict) or dados.keys() - {"reset", "corpo", "obstaculo"}:
            raise ValueError("Cena inválida")
        alteracoes = []
        for grupo, limites in {
            "corpo": {"x": (10, 150), "y": (10, 100), "yaw": None,
                      "roll": (-180, 180), "pitch": (-180, 180), "segurando": None},
            "obstaculo": {"x": (6, 154), "y": (6, 104)},
        }.items():
            campos = dados.get(grupo, {})
            if not isinstance(campos, dict) or campos.keys() - limites.keys():
                raise ValueError(f"Campos inválidos em {grupo}")
            for nome, valor in campos.items():
                if nome == "segurando":
                    if type(valor) is not bool:
                        raise ValueError("Segurar exige um valor booleano")
                elif type(valor) not in (int, float) or not -1e6 <= valor <= 1e6:
                    raise ValueError("A pose precisa de números finitos")
                elif nome == "yaw":
                    valor %= 360
                else:
                    valor = limitar(valor, *limites[nome])
                alteracoes.append((grupo, nome, valor))
        if dados.get("reset") is True:
            self.__init__()
        for grupo, nome, valor in alteracoes:
            setattr(getattr(self, grupo), nome, valor)

    def sensor_frontal(self) -> int | None:
        corpo, alvo = self.corpo, self.obstaculo
        h = math.radians(corpo.yaw)
        dx, dy = math.sin(h), -math.cos(h)
        origem_x = corpo.x + dx * AVANCO_SENSOR_CM
        origem_y = corpo.y + dy * AVANCO_SENSOR_CM
        parede_x = math.inf if abs(dx) < 1e-9 else ((LARGURA_ARENA_CM if dx > 0 else 0) - origem_x) / dx
        parede_y = math.inf if abs(dy) < 1e-9 else ((ALTURA_ARENA_CM if dy > 0 else 0) - origem_y) / dy
        distancia = min(parede_x, parede_y)
        ox = alvo.x - origem_x
        oy = alvo.y - origem_y
        paralelo = ox * dx + oy * dy
        lateral = abs(ox * dy - oy * dx)
        if lateral <= alvo.raio:
            meia_corda = math.sqrt(alvo.raio**2 - lateral**2)
            if paralelo + meia_corda >= 0:
                distancia = min(distancia, paralelo - meia_corda)
        return max(1, round(distancia * 10)) if distancia <= ALCANCE_SENSOR_CM else None

    def passo(self, segundos: float, esquerda: int, direita: int) -> tuple[float, ...]:
        c, anterior = self.corpo, self._anterior
        if not c.segurando:
            rodas = []
            for atual, pwm in zip(self._velocidade_rodas, (esquerda, direita)):
                limite = (125 if not pwm else 70) * segundos
                rodas.append(atual + limitar(pwm * 28 / 255 - atual, -limite, limite))
            v_esq, v_dir = self._velocidade_rodas = tuple(rodas)
            giro = (v_esq - v_dir) / 13 * segundos
            h = math.radians(c.yaw) + giro / 2
            distancia = (v_esq + v_dir) / 2 * segundos
            c.x = limitar(c.x + math.sin(h) * distancia, 10, 150)
            c.y = limitar(c.y - math.cos(h) * distancia, 10, 100)
            c.yaw = (c.yaw + math.degrees(giro)) % 360
        else:
            self._velocidade_rodas = (0., 0.)

        ro, pi, h = map(math.radians, (c.roll, c.pitch, c.yaw))
        vx, vy = (c.x - anterior.x) / segundos, (c.y - anterior.y) / segundos
        ax = limitar((vx - self._velocidade[0]) / segundos / 981, -1.6, 1.6)
        ay = limitar((vy - self._velocidade[1]) / segundos / 981, -1.6, 1.6)
        self._velocidade = (vx, vy)
        gx = limitar((c.roll - anterior.roll) / segundos, -495, 495)
        gy = limitar((c.pitch - anterior.pitch) / segundos, -495, 495)
        delta_yaw = (c.yaw - anterior.yaw + 180) % 360 - 180
        gz = limitar(-delta_yaw / segundos, -495, 495)
        self._anterior = Corpo(**asdict(c))
        return (-math.sin(pi) + ax * math.sin(h) - ay * math.cos(h),
                math.sin(ro) * math.cos(pi) + ax * math.cos(h) + ay * math.sin(h),
                math.cos(ro) * math.cos(pi), gx, gy, gz)
