class ScriptedProvider:
    # Deterministic model substitute: no API key is required.
    def respond(self, question):
        q = question.lower()
        if "book" in q:
            return {
                "agent": "print_specialist",
                "action": "book",
                "args": {"slot_id": 2, "material_grams": 50}
            }
        if "cancel" in q:
            return {
                "agent": "print_specialist",
                "action": "cancel",
                "args": {"request_id": 2}
            }
        if "policy" in q or "limit" in q:
            return {"agent":"info_specialist","action":"policy","args":{}}
        return {"agent":"info_specialist","action":"slots","args":{}}
