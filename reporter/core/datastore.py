import gzip
import pickle
import re
from typing import Optional, Callable, Union, List

from pandas import HDFStore as PandasHDFStore, DataFrame

import logging

log = logging.getLogger('root')


class DataStore(object):
    pass


class DataFrameStore(DataStore):

    def __init__(self, path: str, compute: Optional[Callable] = None) -> None:
        self.path = path
        if compute:
            log.info('Computing contents for DataFrame at {}'.format(path))
            self.save(compute())
        with gzip.open(self.path, 'rb') as f:
            log.debug('Loading DataFrame from {}'.format(path))
            self.dataframe = pickle.load(f)

    def query(self, query: str) -> DataFrame:
        log.debug('Running query "{}" against DataFrame at {}'.format(query, self.path))
        return self.dataframe.query(query)

    def all(self) -> DataFrame:
        return self.dataframe

    def save(self, dataframe: DataFrame) -> None:
        log.debug('Storing DataFrame at {}'.format(self.path))
        with gzip.open(self.path, 'wb') as f:
            pickle.dump(dataframe, f)


class HdfStore(DataStore):
    complevel = 9
    complib = 'blosc:zstd'

    def __init__(self, path: str, table: str, compute: Optional[Callable] = None) -> None:
        self.table = table
        if compute:
            self.store = PandasHDFStore(path, complevel=self.complevel, complib=self.complib)
            dataframe = compute()
            dataframe.sort_values(by='where', axis=0, inplace=True)
            self._mangle_where(dataframe)
            self.store.put(
                self.table,
                dataframe,
                append=False,
                format='table',
                expectedrows=len(dataframe),
                data_columns=[
                    'where_',
                    'where_type',
                    'who',
                    'who_type',
                    'when',
                    'when_type',
                ])
            # temp_store.create_table_index(self.table, columns=['where_', 'where_type', 'who', 'who_type'], optlevel=9, kind='full')
        else:
            self.store = PandasHDFStore(path, complevel=self.complevel, complib=self.complib, mode='r')

    def query(self, query: str) -> DataFrame:
        # print("Running query {}".format(query))
        query = self._mangle_where_in_query(query)
        df = self.store.select(self.table, where=query)
        self._unmangle_where(df)
        return df

    def _mangle_where(self, df: DataFrame) -> None:
        # See: https://github.com/PyTables/PyTables/issues/638
        df.rename(columns={'where': 'where_'}, inplace=True)

    def _unmangle_where(self, df: DataFrame) -> None:
        # See: https://github.com/PyTables/PyTables/issues/638
        df.rename(columns={'where_': 'where'}, inplace=True)

    def _mangle_where_in_query(self, query: Union[str, List[str]]) -> Union[str, List[str]]:
        # See: https://github.com/PyTables/PyTables/issues/638
        if isinstance(query, str):
            return re.sub("where([^_])", "where_\\1", query)
        else:
            return [self._mangle_where_in_query(subquery) for subquery in query]
