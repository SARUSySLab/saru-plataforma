---
titulo: "2.6. Modelo Térmico de Freios (Lumped-Mass)"
data: "2026-07-14"
origem: "_arquivo/saru-KB/20_vehicle_dynamics/modules/04_2_6_modelo_t_rmico_de_freios_lumped_mass.md"
status: "vigente"
area: "dinamica_veicular"
---

## 2.6. Modelo Térmico de Freios (Lumped-Mass)

- **Parâmetros GT3 R (Ferro 390mm/370mm):** O modelo *lumped-mass* para os rotores AP Racing/PFC assume disco com massa de ~10.9 kg e área convectiva total de ~0.25-0.35 m² (fricção + aletas).
- **Convecção (h):** Baseado nas equações clássicas de Limpert (1975) até correlações modernas, a eficiência de bombeamento centrífugo das aletas responde por >50% do cooling em alta velocidade. O coeficiente $h(v)$ varia quase linearmente de ~50 W/m²K (lento) até ~250 W/m²K (250 km/h).
- **Radiação e Emissividade:** Devido à severa oxidação térmica (>550°C), a emissividade ($\epsilon$) do ferro sobe para ~0.70. O termo radiativo ($T^4$) do balanço térmico passa a representar até 30-40% da dissipação nas zonas de baixa velocidade e pico de temperatura.
- **Equilíbrio de Endurance:** Em stints reais, calibra-se o *blanking* dos dutos para que a temperatura cíclica do disco oscile no range ideal de 500°C a 750°C. Picos estáveis acima de 750°C indicam subdimensionamento do resfriamento, induzindo oxidação destrutiva e degradação térmica massiva.

---
