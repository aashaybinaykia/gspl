import json
import frappe


def _safe_json(val):
    """Safely parse JSON fields that may be stored as text."""
    if not val:
        return None
    if isinstance(val, (dict, list)):
        return val
    try:
        return json.loads(val)
    except Exception:
        return None


def _normalize_col(col):
    """
    Normalize a column definition to a usable key.
    Supports:
      - "item_code"
      - {"label": "Item", "fieldname": "item_code"}
    """
    if isinstance(col, dict):
        return (col.get("fieldname") or col.get("label") or "").strip()
    if isinstance(col, str):
        return col.strip()
    return ""


def _get_prepared_payload(prep_name: str):
    """
    Returns (columns, rows) from a Prepared Report document.
    Tries multiple possible fieldnames because ERPNext/Frappe versions vary.
    """
    doc = frappe.get_doc("Prepared Report", prep_name)

    payload = None
    # Common fieldnames where prepared output may be stored
    for field in ("result", "data", "report_result", "output"):
        if hasattr(doc, field):
            payload = _safe_json(getattr(doc, field))
            if payload:
                break

    # Typical payload formats:
    # 1) {"columns":[...], "result":[...]} or {"columns":[...], "data":[...]}
    # 2) rows list directly
    if isinstance(payload, dict):
        columns = payload.get("columns")
        rows = payload.get("result") or payload.get("data") or payload.get("rows") or []
    else:
        columns = None
        rows = payload or []

    return columns, rows


def _infer_colset(columns, rows):
    """Get a set of column keys from columns metadata OR dict row keys."""
    if columns:
        return {_normalize_col(c) for c in columns if _normalize_col(c)}
    if rows and isinstance(rows[0], dict):
        return set(rows[0].keys())
    return set()


def _row_to_dict(row, cols_norm):
    """Convert list/tuple row into dict using normalized columns."""
    if isinstance(row, dict):
        return row
    out = {}
    for i, c in enumerate(cols_norm or []):
        if c:
            out[c] = row[i] if i < len(row) else None
    return out


def _is_number(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool)


@frappe.whitelist()
def get_common_columns(prep_a: str, prep_b: str):
    """
    Called from report JS to populate the join_key dropdown.
    Returns only columns that exist in BOTH prepared reports.
    """
    cols_a, rows_a = _get_prepared_payload(prep_a)
    cols_b, rows_b = _get_prepared_payload(prep_b)

    set_a = _infer_colset(cols_a, rows_a)
    set_b = _infer_colset(cols_b, rows_b)

    return sorted(list(set_a.intersection(set_b)))


def execute(filters=None):
    """
    Joins two Prepared Reports (A and B) using a chosen common column.
    - Left Join or Inner Join
    - Duplicate handling for B: First / Sum Numeric / Error
    """
    filters = filters or {}

    prep_a = filters.get("prep_a")
    prep_b = filters.get("prep_b")
    join_key = filters.get("join_key")
    join_type = filters.get("join_type") or "Left Join"
    dup_rule = filters.get("dup_rule") or "First"

    if not prep_a or not prep_b or not join_key:
        return [], []

    cols_a, rows_a = _get_prepared_payload(prep_a)
    cols_b, rows_b = _get_prepared_payload(prep_b)

    # Normalize columns to keys
    cols_a_norm = [_normalize_col(c) for c in (cols_a or []) if _normalize_col(c)]
    cols_b_norm = [_normalize_col(c) for c in (cols_b or []) if _normalize_col(c)]

    # Convert rows to dicts
    A = [_row_to_dict(r, cols_a_norm) for r in rows_a]
    B = [_row_to_dict(r, cols_b_norm) for r in rows_b]

    # Index B by join_key
    b_first = {}
    b_dups = {}

    for r in B:
        k = r.get(join_key)
        if k is None:
            continue
        if k in b_first:
            b_dups.setdefault(k, []).append(r)
        else:
            b_first[k] = r

    if b_dups and dup_rule == "Error":
        keys = list(b_dups.keys())
        frappe.throw(
            f"Duplicate keys found in Prepared Report B for join key '{join_key}'. "
            f"Example keys: {keys[:10]}"
        )

    def reduce_dups(first_row, dup_rows):
        if dup_rule == "First":
            return first_row
        if dup_rule == "Sum Numeric":
            agg = dict(first_row)
            for dr in dup_rows:
                for k2, v2 in dr.items():
                    if k2 == join_key:
                        continue
                    if _is_number(v2):
                        agg[k2] = (agg.get(k2) or 0) + v2
            return agg
        return first_row

    # Merge (A left join B by default)
    merged = []
    for ar in A:
        k = ar.get(join_key)
        br = b_first.get(k)

        if br and k in b_dups:
            br = reduce_dups(br, b_dups[k])

        if join_type == "Inner Join" and not br:
            continue

        out = dict(ar)

        # Add B fields with prefix to avoid collisions
        if br:
            for k2, v2 in br.items():
                if k2 == join_key:
                    continue
                out[f"b__{k2}"] = v2

        merged.append(out)

    # Output columns: A columns + prefixed B columns (excluding join_key)
    out_columns = [{"label": c, "fieldname": c, "fieldtype": "Data"} for c in cols_a_norm]
    for c in cols_b_norm:
        if c == join_key:
            continue
        out_columns.append({"label": f"B: {c}", "fieldname": f"b__{c}", "fieldtype": "Data"})

    return out_columns, merged
