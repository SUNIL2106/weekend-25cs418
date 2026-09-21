import json

def run_effect(con, key, effect_type, fn):
    row = con.execute(
        "SELECT result FROM effects WHERE idempotency_key=?", (key,)
    ).fetchone()
    if row:
        return json.loads(row["result"])

    result = fn()
    con.execute(
        "INSERT INTO effects(idempotency_key,effect_type,result) VALUES(?,?,?)",
        (key, effect_type, json.dumps(result, sort_keys=True))
    )
    return result
