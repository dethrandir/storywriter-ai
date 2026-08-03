# ops.py
"""
Model mutasyon operasyonları ve sonuç tipleri.

`auto=True` deseni: üretim/yansıtma fonksiyonları yapacakları değişiklikleri
`ModelOp` listesi olarak döndürür. `auto=True` ise executor bunları uygular;
`auto=False` ise sadece öneri olarak sunulur ve onay sonrası `apply_ops` çağrılır.
"""
from typing import Any, Literal

from pydantic import BaseModel, Field

OpKind = Literal["create", "update", "append_experience", "append_to_array"]


class ModelOp(BaseModel):
    kind: OpKind
    entity_type: str  # "character", "setting", "conflict", ...
    entity_id: str | None = None  # create için opsiyonel (yoksa yeni id üretilir)
    data: dict[str, Any] | None = None  # create/update payload'u
    field: str | None = None  # append_to_array için hedef jsonb alan
    note: str | None = None  # insan okunur açıklama


class MutationResult(BaseModel):
    ops: list[ModelOp] = Field(default_factory=list)
    applied: bool = False
    applied_ops: list[ModelOp] = Field(default_factory=list)
    created_ids: dict[str, str] = Field(default_factory=dict)  # op indeksi -> entity_id
    notes: list[str] = Field(default_factory=list)
