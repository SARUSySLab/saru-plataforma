---
titulo: "8. Arquitetura Avançada de Geometria de Pista"
data: "2026-07-14"
origem: "_arquivo/saru-KB/40_software_arch/modules/09_8_arquitetura_avan_ada_de_geometria_de_pista.md"
status: "vigente"
area: "dinamica_veicular"
---

## 8. Arquitetura Avançada de Geometria de Pista

A simulação transiente 14-DOF impõe restrições severas à representação da geometria 3D da pista. Descontinuidades causam singularidades matemáticas nas equações diferencias de contato do pneu.

### 8.1. Estratégia Bimodal (Horizonte I e II)
- **Horizonte I (Causal Python 2D):** Conversão de telemetria GNSS RTK/IMU. Transforma-se domínio do tempo para distância da pista ($s$), alinhando traçados ortogonalmente via Non-Linear Least Squares. Filtros Savitzky-Golay extraem curvatura analítica suave, persistida no flat-database HDF5 legado.
- **Horizonte II (Acausal Julia 14-DOF):** Adoção canônica de **ASAM OpenDRIVE** (macroscópico via polinômios cúbicos ao longo de $s$) e **ASAM OpenCRG** (micro-textura LiDAR 0.05m $\times$ 0.05m) para estabilidade extrema.

### 8.2. Banco de Dados Espaço-Temporal
- Utilização de **PostgreSQL + TimescaleDB** para retenção analítica. Telemetria (100Hz+) armazenada em `Hypertables` particionadas por sessão. Chunks antigos ativam compressão colunar aglutinando por `session_id`, colapsando bilhões de registros com ~90% de compressão. *Continuous Aggregates* alimentam dashboards instantâneos. 
- Formato **Apache Parquet** para Business Intelligence, e **HDF5** estrito para carregamento paralelo e em bloco direto para o solver físico (Julia `h5read`).

---
