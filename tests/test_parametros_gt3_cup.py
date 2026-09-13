"""Parametros do 911 GT3 Cup (E-RF-09): presets das tres geracoes e modelos de pneu.

Nao toca banco nem acervo. O que estes testes travam sao os numeros que separam
uma geracao da outra (massa, motor, entre-eixos, acionamento do cambio) e a
ordem de grandeza das forcas de pneu, para que uma edicao distraida no modulo
apareca antes de chegar a um solver.
"""

from __future__ import annotations

import math

import pytest

from saru_poc.fisica.parametros_gt3_cup import (
    CombinedSlipPacejkaTire,
    Generation,
    PacejkaPureSlipTire,
    PacejkaTire,
    TransientPacejkaTire,
    get_gt3_cup_preset,
    porsche_911_gt3_cup_991_1,
    porsche_911_gt3_cup_991_2,
    porsche_911_gt3_cup_992_1,
)


@pytest.fixture
def v991_1():
    return porsche_911_gt3_cup_991_1()


@pytest.fixture
def v991_2():
    return porsche_911_gt3_cup_991_2()


@pytest.fixture
def v992_1():
    return porsche_911_gt3_cup_992_1()


def test_cada_preset_declara_a_propria_geracao(v991_1, v991_2, v992_1) -> None:
    assert v991_1.generation == Generation.CUP_991_1
    assert v991_2.generation == Generation.CUP_991_2
    assert v992_1.generation == Generation.CUP_992_1


def test_massa_cresce_de_uma_geracao_para_a_seguinte(v991_1, v991_2, v992_1) -> None:
    """O carro engordou a cada geracao, e o preset tem de refletir isso."""
    assert v991_1.mass_geometry.mass_race_kg < v991_2.mass_geometry.mass_race_kg
    assert v991_2.mass_geometry.mass_race_kg < v992_1.mass_geometry.mass_race_kg
    assert v991_1.mass_geometry.mass_race_kg == 1255.0
    assert v991_2.mass_geometry.mass_race_kg == 1280.0
    assert v992_1.mass_geometry.mass_race_kg == 1340.0


def test_motor_bate_com_a_ficha_de_cada_geracao(v991_1, v991_2, v992_1) -> None:
    assert v991_1.engine.displacement_cm3 == 3797
    assert v991_1.engine.max_power_cv == 460.0
    assert v991_1.engine.max_torque_Nm == 440.0

    assert v991_2.engine.displacement_cm3 == 3996
    assert v991_2.engine.max_power_cv == 485.0
    assert v991_2.engine.max_torque_Nm == 480.0

    assert v992_1.engine.displacement_cm3 == 3996
    assert v992_1.engine.max_power_cv == 510.0
    assert v992_1.engine.max_torque_Nm == 470.0


def test_992_tem_entre_eixos_maior_e_bitola_larga(v991_1, v991_2, v992_1) -> None:
    """O 992.1 ganhou 39 mm de entre-eixos e a bitola larga da carroceria turbo."""
    assert v991_1.mass_geometry.wheelbase_m == pytest.approx(2.463)
    assert v991_2.mass_geometry.wheelbase_m == pytest.approx(2.463)
    assert v992_1.mass_geometry.wheelbase_m == pytest.approx(2.502)
    assert v992_1.mass_geometry.track_front_m > v991_2.mass_geometry.track_front_m


def test_992_troca_o_cambio_pneumatico_pelo_eletrico(v991_1, v991_2, v992_1) -> None:
    assert "pneumática" in v991_1.transmission.shift_actuation.lower()
    assert "pneumática" in v991_2.transmission.shift_actuation.lower()
    assert "elétrico" in v992_1.transmission.shift_actuation.lower()


def test_busca_por_rotulo_de_texto_acha_a_geracao_certa() -> None:
    assert get_gt3_cup_preset("991.1").generation == Generation.CUP_991_1
    assert get_gt3_cup_preset("991.2").generation == Generation.CUP_991_2
    assert get_gt3_cup_preset("992").generation == Generation.CUP_992_1


def test_busca_por_rotulo_desconhecido_recusa() -> None:
    with pytest.raises(ValueError, match="desconhecida"):
        get_gt3_cup_preset("911 RSR")


def test_pneu_de_slip_puro_cresce_com_o_angulo_e_com_o_escorregamento(v992_1) -> None:
    """Magic Formula desacoplada: mais deriva, mais forca, na ordem de grandeza do GT3."""
    tire = PacejkaPureSlipTire(v992_1.tire)
    fz = 4000.0

    fy_pequeno = abs(tire.lateral_force(math.radians(1.0), fz))
    fy_pico = abs(tire.lateral_force(math.radians(6.0), fz))
    assert fy_pico > fy_pequeno
    assert fy_pico > 4000.0

    fx_pequeno = tire.longitudinal_force(0.02, fz)
    fx_pico = tire.longitudinal_force(0.12, fz)
    assert fx_pico > fx_pequeno
    assert fx_pico > 4000.0


def test_pneu_sem_carga_nao_gera_forca(v992_1) -> None:
    tire = PacejkaPureSlipTire(v992_1.tire)
    assert tire.lateral_force(math.radians(5.0), 0.0) == 0.0
    assert tire.longitudinal_force(0.1, 0.0) == 0.0


def test_apelidos_apontam_para_as_classes_novas() -> None:
    assert PacejkaTire is PacejkaPureSlipTire
    assert TransientPacejkaTire is CombinedSlipPacejkaTire


def test_elipse_de_atrito_tira_forca_lateral_quando_ha_forca_longitudinal(v992_1) -> None:
    """Com tracao junto, sobra menos aderencia para a curva: Fy cai."""
    tire = CombinedSlipPacejkaTire(v992_1.tire)
    fz = 4000.0

    sem_slip = tire.compute_forces(fz, 0.0, 0.0)
    assert sem_slip["Fx"] == pytest.approx(0.0)
    assert sem_slip["Fy"] == pytest.approx(0.0)

    so_lateral = tire.compute_forces(fz, math.radians(5.0), 0.0)
    assert so_lateral["Fx"] == pytest.approx(0.0)
    assert abs(so_lateral["Fy"]) > 4000.0

    combinado = tire.compute_forces(fz, math.radians(5.0), 0.10)
    assert combinado["Fx"] > 1000.0
    assert abs(combinado["Fy"]) < abs(so_lateral["Fy"])


def test_pneu_combinado_sem_carga_devolve_tudo_zero(v992_1) -> None:
    tire = CombinedSlipPacejkaTire(v992_1.tire)
    resultado = tire.compute_forces(0.0, math.radians(5.0), 0.1)
    assert resultado == {"Fx": 0.0, "Fy": 0.0, "Mz": 0.0, "grip_factor": 0.0}
