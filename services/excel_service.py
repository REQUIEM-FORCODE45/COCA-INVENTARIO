from pathlib import Path
import pandas as pd
import re
from typing import Dict, List, Optional

BASE_DIR = Path(__file__).parent.parent


class ExcelService:
    def __init__(self):
        self.liquiya_path: Optional[Path] = None
        self.plantilla_path: Optional[Path] = None
        self._cache: Optional[List[Dict]] = None

    def set_paths(self, liquiya_path, plantilla_path):
        self.liquiya_path = Path(liquiya_path)
        self.plantilla_path = Path(plantilla_path)
        self._cache = None

    def _parse_producto(self, producto: str) -> tuple:
        match = re.match(r"^(\d+)\s*-\s*(.+)$", str(producto).strip())
        if match:
            return match.group(1), match.group(2).strip()
        return None, str(producto).strip()

    def _parse_codigo(self, codigo) -> Optional[str]:
        if pd.isna(codigo):
            return None
        codigo_str = str(codigo)
        if '.' in codigo_str:
            codigo_str = codigo_str.split('.')[0]
        return codigo_str.strip()

    def _load_piso_real_base(self) -> Dict[str, Dict]:
        df = pd.read_excel(self.plantilla_path, sheet_name="PLANTILLA INV. PISO (0)", header=0)
        codigos = {}
        for _, row in df.iterrows():
            codigo = self._parse_codigo(row.iloc[0])
            if codigo:
                codigos[codigo] = {
                    "unidades": int(row.iloc[21]) if pd.notna(row.iloc[21]) else 0,
                    "subunidades": int(row.iloc[22]) if pd.notna(row.iloc[22]) else 0
                }
        return codigos

    def _load_positivos_negativos(self) -> tuple:
        positivos = {}
        negativos = {}

        try:
            df_pos = pd.read_excel(self.liquiya_path, sheet_name="POSITIVO", header=None)
            for row_idx in range(2, len(df_pos)):
                for grupo in range(8):
                    col_cod = grupo * 3
                    col_cant = grupo * 3 + 1
                    col_und = grupo * 3 + 2

                    codigo = self._parse_codigo(df_pos.iloc[row_idx, col_cod] if col_cod < len(df_pos.columns) else None)
                    cantidad = df_pos.iloc[row_idx, col_cant] if col_cant < len(df_pos.columns) else None
                    und = df_pos.iloc[row_idx, col_und] if col_und < len(df_pos.columns) else None

                    if codigo:
                        positivos[codigo] = {
                            "unidades": int(cantidad) if pd.notna(cantidad) else 0,
                            "subunidades": int(und) if pd.notna(und) else 0
                        }
        except Exception:
            pass

        try:
            df_neg = pd.read_excel(self.liquiya_path, sheet_name="NEGATIVOS", header=None)
            for row_idx in range(2, len(df_neg)):
                for grupo in range(8):
                    col_cod = grupo * 3
                    col_cant = grupo * 3 + 1
                    col_und = grupo * 3 + 2

                    codigo = self._parse_codigo(df_neg.iloc[row_idx, col_cod] if col_cod < len(df_neg.columns) else None)
                    cantidad = df_neg.iloc[row_idx, col_cant] if col_cant < len(df_neg.columns) else None
                    und = df_neg.iloc[row_idx, col_und] if col_und < len(df_neg.columns) else None

                    if codigo:
                        negativos[codigo] = {
                            "unidades": int(cantidad) if pd.notna(cantidad) else 0,
                            "subunidades": int(und) if pd.notna(und) else 0
                        }
        except Exception:
            pass

        return positivos, negativos

    def _load_teorico(self) -> pd.DataFrame:
        df = pd.read_excel(self.liquiya_path, sheet_name="TEORICO", header=None, skiprows=3)
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

        piso_real_base = self._load_piso_real_base()
        positivos, negativos = self._load_positivos_negativos()
        inventario = self._load_teorico()

        print(f"Base Piso Real: {len(piso_real_base)} códigos")
        print(f"Positivos: {len(positivos)} códigos - {positivos}")
        print(f"Negativos: {len(negativos)} códigos - {negativos}")

        data = []
        for _, row in inventario.iterrows():
            codigo, nombre = self._parse_producto(row["producto"])

            base_u = 0
            base_su = 0
            if codigo and codigo in piso_real_base:
                base_u = piso_real_base[codigo]["unidades"]
                base_su = piso_real_base[codigo]["subunidades"]

            pos_u = positivos.get(codigo, {}).get("unidades", 0) if codigo else 0
            pos_su = positivos.get(codigo, {}).get("subunidades", 0) if codigo else 0
            neg_u = negativos.get(codigo, {}).get("unidades", 0) if codigo else 0
            neg_su = negativos.get(codigo, {}).get("subunidades", 0) if codigo else 0

            piso_u = base_u + pos_u - neg_u
            piso_su = base_su + pos_su - neg_su

            teorico_u = int(row["teorico_unidades"]) if pd.notna(row["teorico_unidades"]) else 0
            teorico_su = int(row["teorico_subunidades"]) if pd.notna(row["teorico_subunidades"]) else 0

            data.append({
                "codigo": codigo,
                "nombre": nombre,
                "teorico": {
                    "unidades": teorico_u,
                    "subunidades": teorico_su
                },
                "diferencias_reales": {
                    "unidades": piso_u - teorico_u,
                    "subunidades": piso_su - teorico_su
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
                    "unidades": piso_u - (int(row["fisico_unidades"]) if pd.notna(row["fisico_unidades"]) else 0),
                    "subunidades": piso_su - (int(row["fisico_subunidades"]) if pd.notna(row["fisico_subunidades"]) else 0)
                }
            })

        self._cache = data
        return data

    def clear_cache(self):
        self._cache = None

    def _load_nombres_productos(self) -> Dict[str, str]:
        nombres = {}
        try:
            df = pd.read_excel(self.liquiya_path, sheet_name="TEORICO", header=None, skiprows=3)
            for _, row in df.iterrows():
                producto = row.iloc[0]
                if pd.notna(producto):
                    match = re.match(r"^(\d+)\s*-\s*(.+)$", str(producto).strip())
                    if match:
                        codigo = match.group(1)
                        nombre = match.group(2).strip()
                        nombres[codigo] = nombre
        except Exception:
            pass
        return nombres

    def get_positivos_negativos(self) -> tuple:
        positivos, negativos = self._load_positivos_negativos()
        nombres = self._load_nombres_productos()

        positivos_list = [
            {
                "codigo": codigo,
                "nombre": nombres.get(codigo, "Sin nombre"),
                "unidades": data["unidades"],
                "subunidades": data["subunidades"]
            }
            for codigo, data in positivos.items()
        ]

        negativos_list = [
            {
                "codigo": codigo,
                "nombre": nombres.get(codigo, "Sin nombre"),
                "unidades": data["unidades"],
                "subunidades": data["subunidades"]
            }
            for codigo, data in negativos.items()
        ]

        return positivos_list, negativos_list


excel_service = ExcelService()
