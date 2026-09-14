"""Testes de validação dos parâmetros do Porsche 911 GT3 Cup (E-RF-09)."""

import math
import unittest

from parameters_gt3_cup import (
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


class TestPorscheGT3CupParameters(unittest.TestCase):
    """Testes dos parâmetros e modelos das três gerações do GT3 Cup."""

    def setUp(self):
        self.v991_1 = porsche_911_gt3_cup_991_1()
        self.v991_2 = porsche_911_gt3_cup_991_2()
        self.v992_1 = porsche_911_gt3_cup_992_1()

    def test_generations_instantiation(self):
        self.assertEqual(self.v991_1.generation, Generation.CUP_991_1)
        self.assertEqual(self.v991_2.generation, Generation.CUP_991_2)
        self.assertEqual(self.v992_1.generation, Generation.CUP_992_1)

    def test_mass_progression(self):
        """A massa deve seguir a progressão histórica homologada."""
        self.assertLess(
            self.v991_1.mass_geometry.mass_race_kg,
            self.v991_2.mass_geometry.mass_race_kg,
        )
        self.assertLess(
            self.v991_2.mass_geometry.mass_race_kg,
            self.v992_1.mass_geometry.mass_race_kg,
        )
        self.assertEqual(self.v991_1.mass_geometry.mass_race_kg, 1255.0)
        self.assertEqual(self.v991_2.mass_geometry.mass_race_kg, 1280.0)
        self.assertEqual(self.v992_1.mass_geometry.mass_race_kg, 1340.0)

    def test_engine_specifications(self):
        """Motores devem refletir fichas técnicas da Porsche Motorsport."""
        self.assertEqual(self.v991_1.engine.displacement_cm3, 3797)
        self.assertEqual(self.v991_1.engine.max_power_cv, 460.0)
        self.assertEqual(self.v991_1.engine.max_torque_Nm, 440.0)

        self.assertEqual(self.v991_2.engine.displacement_cm3, 3996)
        self.assertEqual(self.v991_2.engine.max_power_cv, 485.0)
        self.assertEqual(self.v991_2.engine.max_torque_Nm, 480.0)

        self.assertEqual(self.v992_1.engine.displacement_cm3, 3996)
        self.assertEqual(self.v992_1.engine.max_power_cv, 510.0)
        self.assertEqual(self.v992_1.engine.max_torque_Nm, 470.0)

    def test_wheelbase_and_chassis(self):
        """992 tem entre-eixos estendido (+39 mm) e bitola turbo larga."""
        self.assertAlmostEqual(self.v991_1.mass_geometry.wheelbase_m, 2.463)
        self.assertAlmostEqual(self.v991_2.mass_geometry.wheelbase_m, 2.463)
        self.assertAlmostEqual(self.v992_1.mass_geometry.wheelbase_m, 2.502)
        self.assertGreater(
            self.v992_1.mass_geometry.track_front_m,
            self.v991_2.mass_geometry.track_front_m,
        )

    def test_transmission_actuation(self):
        """992 abandonou compressor pneumático e adotou atuador elétrico."""
        self.assertIn("pneumática", self.v991_1.transmission.shift_actuation.lower())
        self.assertIn("pneumática", self.v991_2.transmission.shift_actuation.lower())
        self.assertIn("elétrico", self.v992_1.transmission.shift_actuation.lower())

    def test_preset_lookup(self):
        self.assertEqual(get_gt3_cup_preset("991.1").generation, Generation.CUP_991_1)
        self.assertEqual(get_gt3_cup_preset("991.2").generation, Generation.CUP_991_2)
        self.assertEqual(get_gt3_cup_preset("992").generation, Generation.CUP_992_1)

    def test_pacejka_tire_pure_slip(self):
        """Valida Magic Formula de slip puro desacoplado."""
        tire = PacejkaPureSlipTire(self.v992_1.tire)
        fz = 4000.0
        fy_small = abs(tire.lateral_force(math.radians(1.0), fz))
        fy_peak = abs(tire.lateral_force(math.radians(6.0), fz))
        self.assertGreater(fy_peak, fy_small)
        self.assertGreater(fy_peak, 4000.0)

        fx_small = tire.longitudinal_force(0.02, fz)
        fx_peak = tire.longitudinal_force(0.12, fz)
        self.assertGreater(fx_peak, fx_small)
        self.assertGreater(fx_peak, 4000.0)

    def test_combined_slip_tire_and_aliases(self):
        """Valida modelo combinado e resolução de colisão de nomes."""
        self.assertIs(PacejkaTire, PacejkaPureSlipTire)
        self.assertIs(TransientPacejkaTire, CombinedSlipPacejkaTire)

        comb_tire = CombinedSlipPacejkaTire(self.v992_1.tire)
        fz = 4000.0

        # Sem slip: forças nulas
        res_zero = comb_tire.compute_forces(fz, 0.0, 0.0)
        self.assertAlmostEqual(res_zero["Fx"], 0.0)
        self.assertAlmostEqual(res_zero["Fy"], 0.0)

        # Slip lateral puro
        res_lat = comb_tire.compute_forces(fz, math.radians(5.0), 0.0)
        self.assertAlmostEqual(res_lat["Fx"], 0.0)
        self.assertGreater(abs(res_lat["Fy"]), 4000.0)

        # Slip combinado: elipse de atrito reduz Fy quando Fx é grande
        res_comb = comb_tire.compute_forces(fz, math.radians(5.0), 0.10)
        self.assertGreater(res_comb["Fx"], 1000.0)
        self.assertLess(abs(res_comb["Fy"]), abs(res_lat["Fy"]))


if __name__ == "__main__":
    unittest.main()
