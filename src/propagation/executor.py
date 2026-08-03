# executor.py
"""
`ModelOp` listesini uygular. `auto=True` deseninin uygulama tarafı:
- `apply_ops(ops)`: ops'ları doğrudan uygular (auto modu)
- `execute(ops, auto)`: auto ise uygular, değilse onaysız döndürür
"""
from src.propagation.ops import ModelOp, MutationResult
from src.repositories import writer


async def apply_ops(ops: list[ModelOp]) -> MutationResult:
    result = MutationResult(ops=ops, applied=True)
    for op in ops:
        try:
            if op.kind == "create":
                entity_id = await writer.create(op.entity_type, op.data or {})
                result.created_ids[str(len(result.applied_ops))] = entity_id
                if op.note:
                    result.notes.append(op.note)
            elif op.kind == "update":
                if not op.entity_id:
                    raise ValueError(f"update op'unda entity_id zorunlu: {op}")
                await writer.update(op.entity_type, op.entity_id, op.data or {})
                if op.note:
                    result.notes.append(op.note)
            elif op.kind == "append_experience":
                if not op.entity_id or not op.data or "note" not in op.data:
                    raise ValueError(
                        f"append_experience op'unda entity_id ve data.note zorunlu: {op}"
                    )
                await writer.append_experience(
                    op.entity_type, op.entity_id, op.data["note"]
                )
                if op.note:
                    result.notes.append(op.note)
            elif op.kind == "append_to_array":
                if not op.entity_id or not op.field or not op.data or "value" not in op.data:
                    raise ValueError(
                        f"append_to_array op'unda entity_id, field ve data.value zorunlu: {op}"
                    )
                await writer.append_to_array(
                    op.entity_type, op.entity_id, op.field, op.data["value"]
                )
                if op.note:
                    result.notes.append(op.note)
            result.applied_ops.append(op)
        except Exception as exc:  # tek op başarısızsa diğerlerini engelleme
            result.notes.append(f"HATA ({op.kind}:{op.entity_type}): {exc}")
    return result


async def execute(ops: list[ModelOp], auto: bool) -> MutationResult:
    """auto=True ise uygular, değilse öneri olarak döndürür."""
    if auto:
        return await apply_ops(ops)
    return MutationResult(ops=ops, applied=False)
