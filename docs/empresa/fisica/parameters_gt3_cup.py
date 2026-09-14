"""Parâmetros Canônicos do Porsche 911 GT3 Cup (991.1, 991.2 e 992.1).

Este módulo define os parâmetros técnicos e dinâmicos para simulação
veicular (2-DOF bicicleta, 3-DOF transiente e quasi-steady-state),
atendendo ao requisito E-RF-09 da SARU.

Fontes primárias:
1. Porsche Carrera Cup Brasil - Manual Técnico 991 Fase 1 e 2 (2021/2022)
2. Porsche AG - Technical Manual 911 GT3 Cup (Type 992, MY2021-2024)
3. Regulamento Técnico e Desportivo Porsche Cup Brasil (Sprint e Endurance)
4. Michelin Customer Racing Tyre Professional Guide (Slicks 18 pol)
5. PAGID Racing Technical Specifications (Composto RSL29)
6. Cosworth Electronics - Porsche Channels Manual

Resolução de colisão de nomes:
- PacejkaPureSlipTire: Magic Formula desacoplada (longitudinal e lateral)
- CombinedSlipPacejkaTire: Magic Formula com elipse de atrito e transiente
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum


class Generation(str, Enum):
    CUP_991_1 = "991.1"
    CUP_991_2 = "991.2"
    CUP_992_1 = "992.1"


class Provenance(str, Enum):
    OFFICIAL_MANUAL = "MANUAL_OFICIAL"
    HOMOLOGATION = "HOMOLOGACAO_REGULAMENTO"
    SUPPLIER_SPEC = "FORNECEDOR_TECNICO"
    ENGINEERING_ESTIMATE = "ESTIMATIVA_ENGENHARIA"


@dataclass
class ParameterValue:
    """Parâmetro com valor, unidade, fonte e proveniência."""
    value: float
    unit: str
    provenance: Provenance
    source: str


@dataclass
class VehicleMassGeometry:
    """Geometria e massas do veículo."""
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
    """Parâmetros de pneu para modelos lineares e Magic Formula (Pacejka)."""
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
    """Parâmetros aerodinâmicos."""
    drag_coefficient_cd: float
    frontal_area_m2: float
    lift_coefficient_cl: float
    downforce_200kmh_N: float
    downforce_250kmh_N: float
    wing_adjustment_positions: int
    wing_default_position: int


@dataclass
class EngineParams:
    """Parâmetros do trem de força e motorização."""
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
    """Parâmetros de transmissão e relações de marcha."""
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
    """Parâmetros do sistema de frenagem."""
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
    """Veículo completo consolidado para simulação da SARU."""
    generation: Generation
    name: str
    mass_geometry: VehicleMassGeometry
    tire: TireParams
    aero: AeroParams
    engine: EngineParams
    transmission: TransmissionParams
    brake: BrakeParams


# ---------------------------------------------------------------------------
# Resolução de Modelos de Pneu: desacoplado vs combinado
# ---------------------------------------------------------------------------

class PacejkaPureSlipTire:
    """Magic Formula Pacejka desacoplada (MF 5.2 simplificada).

    Utilizada em modelos quasi-steady-state (QSS) e 2-DOF onde
    os canais lateral e longitudinal são avaliados separadamente.
    """

    def __init__(self, params: TireParams) -> None:
        self.B = params.pacejka_B
        self.C = params.pacejka_C
        self.D = params.pacejka_D
        self.E = params.pacejka_E
        self.mu = params.friction_coefficient_mu
        self.k_fz = params.load_sensitivity_k

    def lateral_force(self, slip_angle_rad: float, fz_N: float) -> float:
        """Calcula a força lateral Fy em Newtons."""
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
        """Calcula a força longitudinal Fx em Newtons."""
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
    """Magic Formula com acoplamento por elipse de atrito e transiente.

    Esta classe resolve a colisão de nomes com tires_transient.py,
    fornecendo cálculo combinado com slip angle e slip ratio simultâneos.
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
        """Calcula forças combinadas Fx, Fy e momento de auto-alinhamento Mz."""
        if fz_N <= 0.1:
            return {"Fx": 0.0, "Fy": 0.0, "Mz": 0.0, "grip_factor": 0.0}

        t_delta = abs(self.t_surface - self.t_optimal)
        thermal_grip = max(0.5, min(1.0, 1.0 - 0.0003 * (t_delta ** 1.5)))

        fz0 = 3500.0
        mu_eff = self.mu * (1.0 + self.k_fz * (fz_N - fz0) / fz0) * thermal_grip
        d_eff = mu_eff * fz_N * self.D

        camber_stiffness = 0.08
        alpha_eq = alpha_rad + camber_stiffness * camber_rad

        kappa_mod = kappa / (1.0 + kappa) if kappa > -1.0 else -1.0
        alpha_mod = math.tan(alpha_eq) / (1.0 + kappa) if kappa > -1.0 else math.tan(alpha_eq)
        sigma = math.sqrt(kappa_mod ** 2 + alpha_mod ** 2)

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


# Aliases para compatibilidade com bases de código existentes
PacejkaTire = PacejkaPureSlipTire
TransientPacejkaTire = CombinedSlipPacejkaTire


# ---------------------------------------------------------------------------
# Presets Oficiais das Três Gerações da Porsche Cup Brasil
# ---------------------------------------------------------------------------

def porsche_911_gt3_cup_991_1() -> PorscheCupVehicle:
    """Retorna a calibração do Porsche 911 GT3 Cup 991.1 (3.8 L, 2013-2016).

    Especificação homologada:
    - Motor 3.8 L aspirado MA1.75 com 460 cv e 440 Nm
    - Câmbio pneumático sequential dog-ring 6 marchas
    - Compressão paddle shift: 5,0 a 7,0 bar
    - Suspensão dianteira McPherson com uniball
    - Sem ABS de fábrica no regulamento Carrera Cup inicial
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
    """Retorna a calibração do Porsche 911 GT3 Cup 991.2 (4.0 L, 2017-2020).

    Especificação homologada:
    - Motor 4.0 L aspirado MDG.G com injeção direta DFI, 485 cv e 480 Nm
    - Câmbio sequencial dog-ring 6 marchas com paddle shift pneumático
    - Asa traseira ampliada de 1.840 mm
    - ABS Bosch de competição homologado com 10 posições
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
    """Retorna a calibração do Porsche 911 GT3 Cup 992.1 (4.0 L, 2021-2026).

    Especificação homologada com fontes primárias do manual técnico:
    - Motor 4.0 L aspirado MA2.75 com cárter seco rígido, 510 cv e 470 Nm
    - Limitador em 8.750 rpm, corte de segurança em 9.000 rpm
    - Câmbio sequencial de 6 marchas com atuador elétrico direto (sem compressor)
    - Suspensão dianteira double-wishbone do 911 RSR (bitola 1.920 mm)
    - Asa traseira swan-neck ajustável em 11 posições (-1 deg a +9 deg)
    - ABS Bosch M5 de competição com 10 níveis e Controle de Tração (TC)
    - Pneus Michelin slick 30/65-18 dianteiro e 31/71-18 traseiro
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
    """Busca o preset do Porsche Cup pela geração."""
    gen_str = str(generation).lower().replace("cup_", "").replace("type_", "")
    if "991.1" in gen_str or "991_1" in gen_str or "3.8" in gen_str or "38" in gen_str:
        return porsche_911_gt3_cup_991_1()
    elif "991.2" in gen_str or "991_2" in gen_str or "4.0" in gen_str or "40" in gen_str:
        return porsche_911_gt3_cup_991_2()
    elif "992" in gen_str:
        return porsche_911_gt3_cup_992_1()
    raise ValueError(f"Geração de Porsche GT3 Cup desconhecida: {generation}")


# ---------------------------------------------------------------------------
# Verificação Automática e Demonstração
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    v991_1 = porsche_911_gt3_cup_991_1()
    v991_2 = porsche_911_gt3_cup_991_2()
    v992_1 = porsche_911_gt3_cup_992_1()

    print("=" * 78)
    print("SARU - CATALOGO CANONICO PORSCHE 911 GT3 CUP (E-RF-09)")
    print("=" * 78)
    print(f"{'Grandeza':<32} | {'991.1 (3.8L)':<12} | {'991.2 (4.0L)':<12} | {'992.1 (4.0L)':<12}")
    print("-" * 78)
    print(f"{'Massa corrida (com piloto)':<32} | {v991_1.mass_geometry.mass_race_kg:>8.1f} kg | {v991_2.mass_geometry.mass_race_kg:>8.1f} kg | {v992_1.mass_geometry.mass_race_kg:>8.1f} kg")
    print(f"{'Potencia maxima':<32} | {v991_1.engine.max_power_cv:>8.1f} cv | {v991_2.engine.max_power_cv:>8.1f} cv | {v992_1.engine.max_power_cv:>8.1f} cv")
    print(f"{'Torque maximo':<32} | {v991_1.engine.max_torque_Nm:>8.1f} Nm | {v991_2.engine.max_torque_Nm:>8.1f} Nm | {v992_1.engine.max_torque_Nm:>8.1f} Nm")
    print(f"{'Entre-eixos':<32} | {v991_1.mass_geometry.wheelbase_m:>8.3f} m  | {v991_2.mass_geometry.wheelbase_m:>8.3f} m  | {v992_1.mass_geometry.wheelbase_m:>8.3f} m")
    print(f"{'Downforce a 250 km/h':<32} | {v991_1.aero.downforce_250kmh_N:>8.0f} N  | {v991_2.aero.downforce_250kmh_N:>8.0f} N  | {v992_1.aero.downforce_250kmh_N:>8.0f} N")
    print(f"{'Acionamento do cambio':<32} | {'Pneumatico':<12} | {'Pneumatico':<12} | {'Eletrico':<12}")
    print(f"{'ABS de competicao':<32} | {'Nao (orig)':<12} | {'Sim (10-ch)':<12} | {'Sim (10-ch)':<12}")
    print(f"{'Controle de tracao (TC)':<32} | {'Nao':<12} | {'Nao':<12} | {'Sim (10-ch)':<12}")
    print(f"{'Pneu dianteiro':<32} | {v991_1.tire.dimension_front:<12} | {v991_2.tire.dimension_front:<12} | {v992_1.tire.dimension_front:<12}")
    print(f"{'Pneu traseiro':<32} | {v991_1.tire.dimension_rear:<12} | {v991_2.tire.dimension_rear:<12} | {v992_1.tire.dimension_rear:<12}")
    print("-" * 78)

    # Teste unitario rapido de pneu
    t_pure = PacejkaPureSlipTire(v992_1.tire)
    t_comb = CombinedSlipPacejkaTire(v992_1.tire)
    fz_test = 4000.0  # N
    fy_pure = t_pure.lateral_force(math.radians(5.0), fz_test)
    res_comb = t_comb.compute_forces(fz_test, math.radians(5.0), 0.0)

    print(f"Teste de pneu a 5 graus e Fz={fz_test} N:")
    print(f"  PacejkaPureSlip:      Fy = {fy_pure:.1f} N")
    print(f"  CombinedSlipPacejka:  Fy = {res_comb['Fy']:.1f} N, Fx = {res_comb['Fx']:.1f} N, Mz = {res_comb['Mz']:.1f} Nm")
    assert abs(fy_pure) > 1000.0, "Força lateral pura fora da ordem de grandeza esperada"
    assert abs(res_comb["Fy"]) > 1000.0, "Força lateral combinada fora da ordem de grandeza esperada"
    print("Verificacao concluida com sucesso.")
