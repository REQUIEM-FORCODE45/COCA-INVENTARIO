from pathlib import Path
import pandas as pd
import re
from typing import Dict, List, Optional

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"


class ExcelService:
    def __init__(self):
        self.inventario_path: Optional[Path] = None
        self.plantilla_path: Optional[Path] = None
        self._cache: Optional[List[Dict]] = None

    def set_paths(self, inventario_path, plantilla_path):
        self.inventario_path = Path(inventario_path)
        self.plantilla_path = Path(plantilla_path)
        self._cache = None

    def _parse_producto(self, producto: str) -> tuple:
        match = re.match(r"^(\d+)\s*-\s*(.+)$", str(producto).strip())
        if match:
            return match.group(1), match.group(2).strip()
        return None, str(producto).strip()

    def _load_plantilla_codigos(self) -> Dict[str, Dict]:
        df = pd.read_excel(
            self.plantilla_path,
            sheet_name="PLANTILLA INV. PISO (0)",
            header=0
        )
        codigos = {}
        for _, row in df.iterrows():
            codigo = row.iloc[0]
            if pd.notna(codigo):
                codigos[str(int(codigo)) if isinstance(codigo, float) else str(codigo)] = {
                    "unidades": int(row.iloc[21]) if pd.notna(row.iloc[21]) else 0,
                    "subunidades": int(row.iloc[22]) if pd.notna(row.iloc[22]) else 0
                }
        return codigos

    def _load_inventario(self) -> pd.DataFrame:
        df = pd.read_excel(self.inventario_path, header=None, skiprows=3)
        df.columns = [
            "producto", "teorico_unidades", "teorico_subunidades",
            "fisico_unidades", "fisico_subunidades",
            "diferencias_unidades", "diferencias_subunidades"
        ]
        df = df.dropna(subset=["producto"])
        return df

    def get_inventario_data(self) -> List[Dict]:
        if self._cache is not None:
            return self._cache

        codigos_map = self._load_plantilla_codigos()
        inventario = self._load_inventario()

        data = []
        for _, row in inventario.iterrows():
            codigo, nombre = self._parse_producto(row["producto"])
            if codigo and codigo in codigos_map:
                piso_real = codigos_map[codigo]
            else:
                piso_real = {"unidades": 0, "subunidades": 0}

            teorico_u = int(row["teorico_unidades"]) if pd.notna(row["teorico_unidades"]) else 0
            teorico_su = int(row["teorico_subunidades"]) if pd.notna(row["teorico_subunidades"]) else 0
            piso_u = int(piso_real["unidades"])
            piso_su = int(piso_real["subunidades"])

            data.append({
                "codigo": codigo,
                "nombre": nombre,
                "teorico": {
                    "unidades": teorico_u,
                    "subunidades": teorico_su
                },
                "diferencias_reales": {
                    "unidades":   piso_u - teorico_u,
                    "subunidades": piso_su -teorico_su
                },
                "piso_real": {
                    "unidades": piso_u,
                    "subunidades": piso_su
                },
                "fisico": {
                    "unidades": int(row["fisico_unidades"]) if pd.notna(row["fisico_unidades"]) else 0,
                    "subunidades": int(row["fisico_subunidades"]) if pd.notna(row["fisico_subunidades"]) else 0
                },
                "diferencias": {
                    "unidades": int(row["diferencias_unidades"]) if pd.notna(row["diferencias_unidades"]) else 0,
                    "subunidades": int(row["diferencias_subunidades"]) if pd.notna(row["diferencias_subunidades"]) else 0
                },
                "ajuste_liquido": {
                    "unidades": piso_u - int(row["fisico_unidades"]) if pd.notna(row["fisico_unidades"]) else 0,
                    "subunidades": piso_su - int(row["fisico_subunidades"]) if pd.notna(row["fisico_subunidades"]) else 0
                }
            })

        self._cache = data
        return data

    def clear_cache(self):
        self._cache = None


excel_service = ExcelService()
