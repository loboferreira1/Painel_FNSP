from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class DashboardConfig:
    project_root: Path
    portarias_csv: Path
    ti_municipio_table: Path
    municipios_shapefile: Path
    ti_shapefile: Path
    use_dummy_data: bool = True


DEFAULT_CONFIG = DashboardConfig(
    project_root=Path.cwd(),
    portarias_csv=Path("analysis_2025/analysis_2025/resultados/dou_publications_geral_normalizado.csv"),
    ti_municipio_table=Path("analysis_2025/outputs/dashboard_ready/ti_municipio_relacao.csv"),
    municipios_shapefile=Path("data/ti_dashboard_dummy/municipios.geojson"),
    ti_shapefile=Path("analysis_2025/outputs/dashboard_ready/tis_poligonais_raw.geojson"),
    use_dummy_data=False,
)
