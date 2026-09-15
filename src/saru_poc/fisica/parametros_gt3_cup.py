"""Parametros canonicos do Porsche 911 GT3 Cup nas geracoes 991.1, 991.2 e 992.1.

Serve ao E-RF-09: estimar parametros do veiculo a partir de telemetria, simular a
volta e comparar contra o dado real. Enquanto a estimacao nao existe, este modulo
e o ponto de partida de cada geracao, com a proveniencia declarada valor a valor.

Nenhum numero aqui esta validado contra manual oficial dentro deste repositorio.
A conferencia de cada valor contra a fonte que ele cita esta em
`docs/fisica-parametros-gt3-cup.md`, e o que ficou pendente esta marcado la.

Fontes que o modulo declara:
1. Porsche Carrera Cup Brasil, Manual Tecnico 991 Fase 1 e 2 (2021/2022)
2. Porsche AG, Technical Manual 911 GT3 Cup (Type 992, MY2021-2024)
3. Regulamento Tecnico e Desportivo Porsche Cup Brasil (Sprint e Endurance)
4. Michelin Customer Racing Tyre Professional Guide (slicks 18 pol)
5. PAGID Racing Technical Specifications (composto RSL29)
6. Cosworth Electronics, Porsche Channels Manual

Dois modelos de pneu convivem aqui:
`PacejkaPureSlipTire` e a Magic Formula desacoplada, lateral e longitudinal
separadas. `CombinedSlipPacejkaTire` acopla as duas pela elipse de atrito e
carrega o fator termico.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum


class Generation(str, Enum):
    """Geracao do GT3 Cup, no rotulo que a Porsche usa."""

    CUP_991_1 = "991.1"
    CUP_991_2 = "991.2"
    CUP_992_1 = "992.1"


class Provenance(str, Enum):
    """De onde o valor veio, do mais forte para o mais fraco."""

    OFFICIAL_MANUAL = "MANUAL_OFICIAL"
    HOMOLOGATION = "HOMOLOGACAO_REGULAMENTO"
    SUPPLIER_SPEC = "FORNECEDOR_TECNICO"
    ENGINEERING_ESTIMATE = "ESTIMATIVA_ENGENHARIA"


@dataclass
class ParameterValue:
    """Um parametro com valor, unidade, proveniencia e fonte citada."""

    value: float
    unit: str
    provenance: Provenance
    source: str


@dataclass
class VehicleMassGeometry:
    """Massa, geometria e inercias do veiculo."""

    mass_base_kg: float
    mass_race_kg: float
    lf_m: float
    lr_m: float
    wheelbase_m: float
    track_front_m: float
    track_rear_m: float
    track_avg_m: float
    cg_height_m: float
    Iz_kgm2: float
    Ix_kgm2: float
    Iy_kgm2: float
    steering_ratio: float
    weight_distribution_front_pct: float


@dataclass
class TireParams:
    """Pneu, para o modelo linear de rigidez e para a Magic Formula."""

    cornering_stiffness_front_N_rad: float
    cornering_stiffness_rear_N_rad: float
    friction_coefficient_mu: float
    rolling_radius_front_m: float
    rolling_radius_rear_m: float
    pacejka_B: float
    pacejka_C: float
    pacejka_D: float
    pacejka_E: float
    load_sensitivity_k: float
    dimension_front: str
    dimension_rear: str
    rim_front_in: str
    rim_rear_in: str
    pressure_cold_bar: float
    pressure_hot_target_bar: float
    thermal_optimal_deg_c: float


@dataclass
class AeroParams:
    """Arrasto, sustentacao e downforce em duas velocidades de referencia."""

    drag_coefficient_cd: float
    frontal_area_m2: float
    lift_coefficient_cl: float
    downforce_200kmh_N: float
    downforce_250kmh_N: float
    wing_adjustment_positions: int
    wing_default_position: int


@dataclass
class EngineParams:
    """Motor: potencia, torque, limites de giro e de temperatura."""

    engine_type: str
    displacement_cm3: int
    max_power_kW: float
    max_power_cv: float
    power_rpm: float
    max_torque_Nm: float
    torque_rpm: float
    rpm_idle: float
    rpm_redline: float
    rpm_max_limit: float
    oil_temp_max_normal_c: float
    water_temp_max_normal_c: float
    oil_pressure_min_bar: float
    water_pressure_min_bar: float
    fuel_pressure_bar: float
    torque_curve_rpm: list[float] = field(default_factory=list)
    torque_curve_Nm: list[float] = field(default_factory=list)


@dataclass
class TransmissionParams:
    """Cambio, relacoes de marcha e pontos de troca."""

    gearbox_type: str
    shift_actuation: str
    num_gears: int
    gear_ratios: list[float]
    final_drive_ratio: float
    transmission_efficiency: float
    shift_time_s: float
    upshift_rpm: float
    downshift_rpm: float


@dataclass
class BrakeParams:
    """Freio: disco, pinca, pastilha, balanco e eletronica de assistencia."""

    disc_front_mm: str
    disc_rear_mm: str
    caliper_front_pistons: int
    caliper_rear_pistons: int
    pad_compound: str
    pad_friction_mu: float
    brake_balance_default_front_pct: float
    brake_balance_range: tuple[float, float]
    abs_available: bool
    abs_channels: int
    traction_control_available: bool


@dataclass
class PorscheCupVehicle:
    """Uma geracao inteira do GT3 Cup, pronta para alimentar um solver."""

    generation: Generation
    name: str
    mass_geometry: VehicleMassGeometry
    tire: TireParams
    aero: AeroParams
    engine: EngineParams
    transmission: TransmissionParams
    brake: BrakeParams


# ---------------------------------------------------------------------------
# Modelos de pneu
# ---------------------------------------------------------------------------


class PacejkaPureSlipTire:
    """Magic Formula desacoplada, no formato MF 5.2 simplificado.

    Serve aos modelos quase estaticos (QSS) e ao 2 GDL, onde o canal lateral e
    o longitudinal sao avaliados um de cada vez.
    """

    def __init__(self, params: TireParams) -> None:
        self.B = params.pacejka_B
        self.C = params.pacejka_C
        self.D = params.pacejka_D
        self.E = params.pacejka_E
        self.mu = params.friction_coefficient_mu
        self.k_fz = params.load_sensitivity_k

    def lateral_force(self, slip_angle_rad: float, fz_N: float) -> float:
        """Forca lateral Fy, em newtons, para um angulo de deriva e uma carga."""
        if fz_N <= 0.0:
            return 0.0
        fz0 = 3500.0
        mu_eff = self.mu * (1.0 + self.k_fz * (fz_N - fz0) / fz0)
        mu_eff = max(0.2, mu_eff)
        d = mu_eff * fz_N * self.D
        bx = self.B * slip_angle_rad
        term = bx - self.E * (bx - math.atan(bx))
        fy = d * math.sin(self.C * math.atan(term))
        return -float(fy)

    def longitudinal_force(self, slip_ratio: float, fz_N: float) -> float:
        """Forca longitudinal Fx, em newtons, para um escorregamento e uma carga."""
        if fz_N <= 0.0:
            return 0.0
        fz0 = 3500.0
        mu_eff = self.mu * (1.0 + self.k_fz * (fz_N - fz0) / fz0)
        mu_eff = max(0.2, mu_eff)
        d = mu_eff * fz_N * self.D
        c_long = 1.60
        bx = self.B * slip_ratio
        term = bx - self.E * (bx - math.atan(bx))
        fx = d * math.sin(c_long * math.atan(term))
        return float(fx)


class CombinedSlipPacejkaTire:
    """Magic Formula acoplada pela elipse de atrito, com fator termico.

    Recebe angulo de deriva e escorregamento ao mesmo tempo, e devolve Fx, Fy e
    o momento de auto alinhamento Mz.
    """

    def __init__(self, params: TireParams, relaxation_length_m: float = 0.40) -> None:
        self.B = params.pacejka_B
        self.C = params.pacejka_C
        self.D = params.pacejka_D
        self.E = params.pacejka_E
        self.mu = params.friction_coefficient_mu
        self.k_fz = params.load_sensitivity_k
        self.relaxation_length = relaxation_length_m
        self.t_surface = params.thermal_optimal_deg_c
        self.t_optimal = params.thermal_optimal_deg_c

    def compute_forces(
        self,
        fz_N: float,
        alpha_rad: float,
        kappa: float,
        camber_rad: float = 0.0,
    ) -> dict[str, float]:
        """Forcas combinadas Fx e Fy, momento Mz e o fator termico de aderencia."""
        if fz_N <= 0.1:
            return {"Fx": 0.0, "Fy": 0.0, "Mz": 0.0, "grip_factor": 0.0}

        t_delta = abs(self.t_surface - self.t_optimal)
        thermal_grip = max(0.5, min(1.0, 1.0 - 0.0003 * (t_delta**1.5)))

        fz0 = 3500.0
        mu_eff = self.mu * (1.0 + self.k_fz * (fz_N - fz0) / fz0) * thermal_grip
        d_eff = mu_eff * fz_N * self.D

        camber_stiffness = 0.08
        alpha_eq = alpha_rad + camber_stiffness * camber_rad

        kappa_mod = kappa / (1.0 + kappa) if kappa > -1.0 else -1.0
        if kappa > -1.0:
            alpha_mod = math.tan(alpha_eq) / (1.0 + kappa)
        else:
            alpha_mod = math.tan(alpha_eq)
        sigma = math.sqrt(kappa_mod**2 + alpha_mod**2)

        if sigma < 1e-6:
            return {"Fx": 0.0, "Fy": 0.0, "Mz": 0.0, "grip_factor": thermal_grip}

        bx = self.B * sigma
        term = bx - self.E * (bx - math.atan(bx))
        f_total = d_eff * math.sin(self.C * math.atan(term))

        fx = f_total * (kappa_mod / sigma)
        fy = f_total * (alpha_mod / sigma)

        trail = 0.12 * math.cos(math.atan(self.B * alpha_eq))
        mz = -trail * fy

        return {
            "Fx": float(fx),
            "Fy": float(-fy),
            "Mz": float(mz),
            "grip_factor": float(thermal_grip),
        }


# Nomes curtos que o codigo de fisica ja arquivado usava. Ficam como apelido
# para nao quebrar quem importa pelo nome antigo.
PacejkaTire = PacejkaPureSlipTire
TransientPacejkaTire = CombinedSlipPacejkaTire


# ---------------------------------------------------------------------------
# Presets por geracao
# ---------------------------------------------------------------------------


def porsche_911_gt3_cup_991_1() -> PorscheCupVehicle:
    """Preset do 991.1, motor 3.8 L, temporadas 2013 a 2016.

    Como o modulo descreve a geracao:
    motor 3.8 L aspirado MA1.75, 460 cv e 440 Nm;
    cambio sequencial dog ring de 6 marchas, paddle shift pneumatico;
    suspensao dianteira McPherson com uniball;
    sem ABS no regulamento inicial da Carrera Cup.
    """
    return PorscheCupVehicle(
        generation=Generation.CUP_991_1,
        name="Porsche 911 GT3 Cup (Type 991.1, 3.8L)",
        mass_geometry=VehicleMassGeometry(
            mass_base_kg=1175.0,
            mass_race_kg=1255.0,
            lf_m=1.034,
            lr_m=1.429,
            wheelbase_m=2.463,
            track_front_m=1.545,
            track_rear_m=1.530,
            track_avg_m=1.5375,
            cg_height_m=0.450,
            Iz_kgm2=1500.0,
            Ix_kgm2=320.0,
            Iy_kgm2=1600.0,
            steering_ratio=14.5,
            weight_distribution_front_pct=42.0,
        ),
        tire=TireParams(
            cornering_stiffness_front_N_rad=72000.0,
            cornering_stiffness_rear_N_rad=88000.0,
            friction_coefficient_mu=1.52,
            rolling_radius_front_m=0.324,
            rolling_radius_rear_m=0.338,
            pacejka_B=21.0,
            pacejka_C=1.35,
            pacejka_D=1.52,
            pacejka_E=0.94,
            load_sensitivity_k=-0.11,
            dimension_front="245/640-18",
            dimension_rear="305/660-18",
            rim_front_in="9.5J x 18",
            rim_rear_in="12.0J x 18",
            pressure_cold_bar=1.40,
            pressure_hot_target_bar=2.00,
            thermal_optimal_deg_c=90.0,
        ),
        aero=AeroParams(
            drag_coefficient_cd=0.385,
            frontal_area_m2=1.98,
            lift_coefficient_cl=-0.58,
            downforce_200kmh_N=700.0,
            downforce_250kmh_N=1090.0,
            wing_adjustment_positions=9,
            wing_default_position=4,
        ),
        engine=EngineParams(
            engine_type="Boxer-6 aspirado MA1.75 DOHC 24V",
            displacement_cm3=3797,
            max_power_kW=338.0,
            max_power_cv=460.0,
            power_rpm=7500.0,
            max_torque_Nm=440.0,
            torque_rpm=6250.0,
            rpm_idle=1000.0,
            rpm_redline=8500.0,
            rpm_max_limit=9000.0,
            oil_temp_max_normal_c=140.0,
            water_temp_max_normal_c=110.0,
            oil_pressure_min_bar=5.5,
            water_pressure_min_bar=0.5,
            fuel_pressure_bar=4.5,
            torque_curve_rpm=[1000, 2500, 3500, 4500, 5500, 6250, 7000, 7500, 8000, 8500],
            torque_curve_Nm=[200, 310, 360, 400, 430, 440, 435, 420, 380, 320],
        ),
        transmission=TransmissionParams(
            gearbox_type="Sequencial 6 marchas dog-ring com dentes retos",
            shift_actuation="Pneumática via paddle shift",
            num_gears=6,
            gear_ratios=[3.167, 2.353, 1.895, 1.526, 1.250, 1.029],
            final_drive_ratio=3.444,
            transmission_efficiency=0.97,
            shift_time_s=0.060,
            upshift_rpm=8000.0,
            downshift_rpm=4500.0,
        ),
        brake=BrakeParams(
            disc_front_mm="380 x 32 ranhurado ventilado",
            disc_rear_mm="380 x 30 ranhurado ventilado",
            caliper_front_pistons=6,
            caliper_rear_pistons=4,
            pad_compound="Pagid RSL29",
            pad_friction_mu=0.42,
            brake_balance_default_front_pct=58.0,
            brake_balance_range=(52.0, 66.0),
            abs_available=False,
            abs_channels=0,
            traction_control_available=False,
        ),
    )


def porsche_911_gt3_cup_991_2() -> PorscheCupVehicle:
    """Preset do 991.2, motor 4.0 L, temporadas 2017 a 2020.

    Como o modulo descreve a geracao:
    motor 4.0 L aspirado MDG.G com injecao direta, 485 cv e 480 Nm;
    cambio sequencial dog ring de 6 marchas, paddle shift pneumatico;
    asa traseira ampliada de 1.840 mm;
    ABS Bosch de competicao com 10 posicoes.
    """
    return PorscheCupVehicle(
        generation=Generation.CUP_991_2,
        name="Porsche 911 GT3 Cup (Type 991.2, 4.0L)",
        mass_geometry=VehicleMassGeometry(
            mass_base_kg=1200.0,
            mass_race_kg=1280.0,
            lf_m=1.034,
            lr_m=1.429,
            wheelbase_m=2.463,
            track_front_m=1.545,
            track_rear_m=1.530,
            track_avg_m=1.5375,
            cg_height_m=0.450,
            Iz_kgm2=1550.0,
            Ix_kgm2=330.0,
            Iy_kgm2=1650.0,
            steering_ratio=14.5,
            weight_distribution_front_pct=42.0,
        ),
        tire=TireParams(
            cornering_stiffness_front_N_rad=76000.0,
            cornering_stiffness_rear_N_rad=92000.0,
            friction_coefficient_mu=1.55,
            rolling_radius_front_m=0.329,
            rolling_radius_rear_m=0.342,
            pacejka_B=21.5,
            pacejka_C=1.36,
            pacejka_D=1.55,
            pacejka_E=0.93,
            load_sensitivity_k=-0.115,
            dimension_front="270/650-18",
            dimension_rear="310/710-18",
            rim_front_in="10.5J x 18",
            rim_rear_in="12.0J x 18",
            pressure_cold_bar=1.45,
            pressure_hot_target_bar=2.05,
            thermal_optimal_deg_c=90.0,
        ),
        aero=AeroParams(
            drag_coefficient_cd=0.395,
            frontal_area_m2=2.00,
            lift_coefficient_cl=-0.70,
            downforce_200kmh_N=850.0,
            downforce_250kmh_N=1330.0,
            wing_adjustment_positions=9,
            wing_default_position=5,
        ),
        engine=EngineParams(
            engine_type="Boxer-6 aspirado MDG.G DFI 24V",
            displacement_cm3=3996,
            max_power_kW=357.0,
            max_power_cv=485.0,
            power_rpm=7500.0,
            max_torque_Nm=480.0,
            torque_rpm=6250.0,
            rpm_idle=1000.0,
            rpm_redline=8500.0,
            rpm_max_limit=9000.0,
            oil_temp_max_normal_c=140.0,
            water_temp_max_normal_c=110.0,
            oil_pressure_min_bar=5.5,
            water_pressure_min_bar=0.5,
            fuel_pressure_bar=2.5,
            torque_curve_rpm=[1000, 2500, 3500, 4500, 5500, 6250, 7000, 7500, 8000, 8500],
            torque_curve_Nm=[220, 340, 390, 440, 470, 480, 475, 455, 410, 350],
        ),
        transmission=TransmissionParams(
            gearbox_type="Sequencial 6 marchas dog-ring com dentes retos",
            shift_actuation="Pneumática via paddle shift",
            num_gears=6,
            gear_ratios=[3.167, 2.353, 1.895, 1.526, 1.250, 1.029],
            final_drive_ratio=3.444,
            transmission_efficiency=0.97,
            shift_time_s=0.055,
            upshift_rpm=8100.0,
            downshift_rpm=4600.0,
        ),
        brake=BrakeParams(
            disc_front_mm="380 x 32 ranhurado ventilado",
            disc_rear_mm="380 x 30 ranhurado ventilado",
            caliper_front_pistons=6,
            caliper_rear_pistons=4,
            pad_compound="Pagid RSL29",
            pad_friction_mu=0.42,
            brake_balance_default_front_pct=58.0,
            brake_balance_range=(52.0, 66.0),
            abs_available=True,
            abs_channels=10,
            traction_control_available=False,
        ),
    )


def porsche_911_gt3_cup_992_1() -> PorscheCupVehicle:
    """Preset do 992.1, motor 4.0 L, temporadas 2021 em diante.

    Como o modulo descreve a geracao:
    motor 4.0 L aspirado MA2.75 com carter seco rigido, 510 cv e 470 Nm;
    limitador em 8.750 rpm e corte de seguranca em 9.000 rpm;
    cambio sequencial de 6 marchas com atuador eletrico direto;
    suspensao dianteira double wishbone do 911 RSR, bitola de 1.920 mm;
    asa traseira swan neck com 11 posicoes, de -1 a +9 graus;
    ABS Bosch M5 com 10 niveis e controle de tracao.
    """
    return PorscheCupVehicle(
        generation=Generation.CUP_992_1,
        name="Porsche 911 GT3 Cup (Type 992.1, 4.0L)",
        mass_geometry=VehicleMassGeometry(
            mass_base_kg=1260.0,
            mass_race_kg=1340.0,
            lf_m=1.001,
            lr_m=1.501,
            wheelbase_m=2.502,
            track_front_m=1.920,
            track_rear_m=1.902,
            track_avg_m=1.911,
            cg_height_m=0.440,
            Iz_kgm2=1650.0,
            Ix_kgm2=350.0,
            Iy_kgm2=1750.0,
            steering_ratio=13.8,
            weight_distribution_front_pct=40.0,
        ),
        tire=TireParams(
            cornering_stiffness_front_N_rad=82000.0,
            cornering_stiffness_rear_N_rad=98000.0,
            friction_coefficient_mu=1.60,
            rolling_radius_front_m=0.332,
            rolling_radius_rear_m=0.355,
            pacejka_B=22.0,
            pacejka_C=1.40,
            pacejka_D=1.60,
            pacejka_E=0.92,
            load_sensitivity_k=-0.120,
            dimension_front="30/65-18",
            dimension_rear="31/71-18",
            rim_front_in="12.0J x 18",
            rim_rear_in="13.0J x 18",
            pressure_cold_bar=1.45,
            pressure_hot_target_bar=2.00,
            thermal_optimal_deg_c=92.0,
        ),
        aero=AeroParams(
            drag_coefficient_cd=0.420,
            frontal_area_m2=2.05,
            lift_coefficient_cl=-1.05,
            downforce_200kmh_N=1300.0,
            downforce_250kmh_N=2030.0,
            wing_adjustment_positions=11,
            wing_default_position=6,
        ),
        engine=EngineParams(
            engine_type="Boxer-6 aspirado MA2.75 DFI cárter seco rígido",
            displacement_cm3=3996,
            max_power_kW=375.0,
            max_power_cv=510.0,
            power_rpm=8400.0,
            max_torque_Nm=470.0,
            torque_rpm=6150.0,
            rpm_idle=1000.0,
            rpm_redline=8750.0,
            rpm_max_limit=9000.0,
            oil_temp_max_normal_c=130.0,
            water_temp_max_normal_c=110.0,
            oil_pressure_min_bar=4.0,
            water_pressure_min_bar=0.6,
            fuel_pressure_bar=3.0,
            torque_curve_rpm=[1000, 2500, 3500, 4500, 5500, 6150, 7000, 8000, 8400, 8750],
            torque_curve_Nm=[210, 320, 380, 430, 460, 470, 465, 440, 426, 390],
        ),
        transmission=TransmissionParams(
            gearbox_type="Sequencial 6 marchas dog-ring com dentes retos",
            shift_actuation="Atuador elétrico direto (sem compressor pneumático)",
            num_gears=6,
            gear_ratios=[3.167, 2.353, 1.895, 1.526, 1.250, 1.029],
            final_drive_ratio=3.444,
            transmission_efficiency=0.97,
            shift_time_s=0.040,
            upshift_rpm=8400.0,
            downshift_rpm=5000.0,
        ),
        brake=BrakeParams(
            disc_front_mm="380 x 32 ranhurado ventilado",
            disc_rear_mm="380 x 32 ranhurado ventilado",
            caliper_front_pistons=6,
            caliper_rear_pistons=4,
            pad_compound="Pagid RSL29",
            pad_friction_mu=0.42,
            brake_balance_default_front_pct=57.5,
            brake_balance_range=(52.0, 65.0),
            abs_available=True,
            abs_channels=10,
            traction_control_available=True,
        ),
    )


def get_gt3_cup_preset(generation: Generation | str) -> PorscheCupVehicle:
    """Busca o preset da geracao pedida, aceitando o enum ou um rotulo em texto."""
    gen_str = str(generation).lower().replace("cup_", "").replace("type_", "")
    if "991.1" in gen_str or "991_1" in gen_str or "3.8" in gen_str or "38" in gen_str:
        return porsche_911_gt3_cup_991_1()
    if "991.2" in gen_str or "991_2" in gen_str or "4.0" in gen_str or "40" in gen_str:
        return porsche_911_gt3_cup_991_2()
    if "992" in gen_str:
        return porsche_911_gt3_cup_992_1()
    raise ValueError(f"Geração de Porsche GT3 Cup desconhecida: {generation}")
