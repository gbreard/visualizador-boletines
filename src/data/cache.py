"""
DataCache singleton: carga datos una vez, los sirve por referencia o copia.
"""

import threading
import pandas as pd


class DataCache:
    _instance = None
    _lock = threading.Lock()

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def __init__(self):
        self._data = {}

    def load(self, loader_fn):
        """Carga datos usando la funcion provista."""
        self._data = loader_fn()

    def get_ref(self, key):
        """Retorna referencia al DataFrame (solo lectura, no copiar)."""
        return self._data.get(key, pd.DataFrame())

    def get(self, key):
        """Retorna copia del DataFrame (seguro para mutar)."""
        df = self._data.get(key, pd.DataFrame())
        return df.copy() if not df.empty else df

    @property
    def periods(self):
        """Lista de periodos de C1.1 en orden cronologico."""
        c11 = self.get_ref('C1.1')
        if not c11.empty and 'Período' in c11.columns and 'Date' in c11.columns:
            sorted_df = c11.sort_values('Date')
            return sorted_df['Período'].unique().tolist()
        return []

    @property
    def last_period(self):
        """Ultimo periodo disponible (cronologicamente)."""
        c11 = self.get_ref('C1.1')
        if not c11.empty and 'Date' in c11.columns and 'Período' in c11.columns:
            return c11.loc[c11['Date'].idxmax(), 'Período']
        p = self.periods
        return p[-1] if p else 'No disponible'

    @property
    def data_keys(self):
        """Claves de datos disponibles."""
        return list(self._data.keys())


cache = DataCache.get_instance()
