from .providers import ScriptedProvider
from .tools.dispatch import dispatch

class InfoSpecialist:
    name = "info_specialist"
    write_tools = False

    def handle(self, action, args):
        if action == "slots":
            return dispatch("list_available_slots", {})
        if action == "policy":
            return dispatch("get_policy", {})
        raise ValueError("Info specialist received unsupported action.")

class PrintSpecialist:
    name = "print_specialist"
    write_tools = True

    def handle(self, action, args, student_id):
        if action == "book":
            return dispatch("book_print_slot", {
                "student_id": student_id,
                "slot_id": args["slot_id"],
                "material_grams": args["material_grams"],
                "idempotency_key": f"book:{student_id}:{args['slot_id']}"
            })
        if action == "cancel":
            return dispatch("cancel_print", {
                "student_id": student_id,
                "request_id": args["request_id"],
                "idempotency_key": f"cancel:{student_id}:{args['request_id']}"
            })
        raise ValueError("Print specialist received unsupported action.")

class Supervisor:
    def __init__(self):
        self.provider = ScriptedProvider()
        self.info = InfoSpecialist()
        self.print = PrintSpecialist()

    def run(self, question, student_id=1):
        plan = self.provider.respond(question)

        if plan["agent"] == "info_specialist":
            result = self.info.handle(plan["action"], plan["args"])
            return {
                "delegated_to":"info_specialist",
                "result":result
            }

        if plan["agent"] == "print_specialist":
            result = self.print.handle(
                plan["action"], plan["args"], student_id
            )
            if plan["action"] in ("book","cancel"):
                dispatch("notify_student", {
                    "student_id":student_id,
                    "message":f"Print request action completed: "
                              f"{result.get('status','completed')}.",
                    "idempotency_key":(
                        f"notify:{plan['action']}:{student_id}:"
                        f"{plan['args'].get('slot_id', plan['args'].get('request_id'))}"
                    )
                })
            return {
                "delegated_to":"print_specialist",
                "result":result
            }

        raise ValueError("Unknown agent.")
