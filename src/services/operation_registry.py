from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from src.domain.models import OperationInput, OperationResult


OperationHandler = Callable[[OperationInput], OperationResult]


@dataclass
class OperationRegistry:
    _operations: dict[str, OperationHandler]

    def register(self, name: str, handler: OperationHandler) -> None:
        self._operations[name] = handler

    def has(self, name: str) -> bool:
        return name in self._operations

    def run(self, name: str, operation_input: OperationInput) -> OperationResult:
        if name not in self._operations:
            raise KeyError(f"Operation not registered: {name}")
        return self._operations[name](operation_input)
