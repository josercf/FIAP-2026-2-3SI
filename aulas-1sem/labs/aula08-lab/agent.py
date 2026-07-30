# agent.py
class Command:
    def execute(self, **kwargs):
        pass

class RastrearPedido(Command):
    def execute(self, **kwargs):
        pedido_id = kwargs.get("pedido_id")
        return f"Pedido {pedido_id} está em trânsito."

# Simulando resposta do LLM
llm_response = {
    "tool": "rastrear",
    "args": {"pedido_id": "LOG-1234"}
}

tools = {"rastrear": RastrearPedido()}
comando = tools.get(llm_response["tool"])
if comando:
    print(comando.execute(**llm_response["args"]))
