import json
from dataclasses import asdict

from Entities.TransactionMark import TransactionMark


class TransactionMarkException(Exception):
    mark: TransactionMark

    def __init__(self, mark):
        super().__init__(mark)
        self.mark = mark

    def __str__(self):
        return json.dumps(asdict(self.mark))
