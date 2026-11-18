from __future__ import annotations

import io
from typing import Any

import pytest

from opencode_harness import llm
from opencode_harness.llm import (
    Agente,
    ChamadaFerramenta,
    Ferramenta,
    FerramentaDesconhecida,
    LimitePassosExcedido,
    Mensagem,
    ProvedorFalso,
    ProvedorIndisponivel,
    ProvedorOpenAI,
    Resposta,
    RespostaInvalida,
    SemResposta,
    argumentos_invalidos,
)


def somar(a: float, b: float) -> float:
    return a + b


def criar_ferramenta_soma() -> Ferramenta:
    return Ferramenta(
        nome="somar",
        descricao="Soma dois números",
        parametros={"a": "number", "b": "number"},
        funcao=somar,
    )


def test_mensagem_rejeita_papel_invalido() -> None:
    with pytest.raises(ValueError, match="papel inválido"):
        Mensagem("humano", "oi")


def test_resposta_exige_texto_ou_chamada() -> None:
    with pytest.raises(ValueError, match="texto ou de uma chamada"):
        Resposta()


def test_ferramenta_executa_com_argumentos_validos() -> None:
    assert criar_ferramenta_soma().executar({"a": 2, "b": 3}) == 5


def test_ferramenta_rejeita_argumentos_invalidos_sem_chamar_funcao() -> None:
    chamadas: list[dict[str, Any]] = []

    def espiao(**kwargs: Any) -> None:
        chamadas.append(kwargs)

    ferramenta = Ferramenta("espiao", "não deve rodar", {"a": "number"}, espiao)

    with pytest.raises(ValueError, match="faltando: a"):
        ferramenta.executar({})
    with pytest.raises(ValueError, match="desconhecido: c"):
        ferramenta.executar({"a": 1, "c": 2})

    assert chamadas == []


def test_argumentos_invalidos_lista_todos_os_problemas() -> None:
    problemas = argumentos_invalidos({"a": "number", "b": "number"}, {"b": 2, "c": 3})

    assert problemas == ["faltando: a", "desconhecido: c"]


def test_ferramenta_rejeita_nome_invalido() -> None:
    with pytest.raises(ValueError, match="nome de ferramenta inválido"):
        Ferramenta("nome com espaço", "x", {}, somar)


def test_ferramenta_gera_schema_openai() -> None:
    schema = criar_ferramenta_soma().para_openai()

    assert schema["type"] == "function"
    assert schema["function"]["name"] == "somar"
    assert schema["function"]["parameters"]["required"] == ["a", "b"]
    assert schema["function"]["parameters"]["additionalProperties"] is False


def test_agente_responde_texto_sem_ferramenta() -> None:
    agente = Agente(ProvedorFalso(padrao="não sei responder"), [])

    assert agente.perguntar("qual a cor do céu?") == "não sei responder"


def test_agente_executa_ferramenta_e_fecha_com_texto() -> None:
    provedor = ProvedorFalso(
        regras=[
            (
                "quanto é",
                Resposta(
                    chamada=ChamadaFerramenta("somar", {"a": 2, "b": 3}),
                    texto="vou somar",
                ),
            )
        ]
    )
    agente = Agente(provedor, [criar_ferramenta_soma()])

    assert agente.perguntar("quanto é 2 + 3?") == "Resultado: 5"


def test_agente_rejeita_ferramenta_nao_registrada() -> None:
    provedor = ProvedorFalso(
        regras=[("some", Resposta(chamada=ChamadaFerramenta("apagar_banco", {})))]
    )
    agente = Agente(provedor, [criar_ferramenta_soma()])

    with pytest.raises(FerramentaDesconhecida, match="apagar_banco"):
        agente.perguntar("some tudo")


def test_agente_respeita_limite_de_passos() -> None:
    class Insistente:
        def responder(self, mensagens: list[Mensagem], ferramentas: list[Ferramenta]) -> Resposta:
            return Resposta(chamada=ChamadaFerramenta("somar", {"a": 1, "b": 1}))

    agente = Agente(Insistente(), [criar_ferramenta_soma()], max_passos=2)

    with pytest.raises(LimitePassosExcedido, match="2 passos"):
        agente.perguntar("some para sempre")


def test_agente_rejeita_configuracao_invalida() -> None:
    with pytest.raises(ValueError, match="max_passos"):
        Agente(ProvedorFalso(padrao="ok"), [], max_passos=0)


def test_agente_rejeita_pergunta_vazia() -> None:
    agente = Agente(ProvedorFalso(padrao="ok"), [])

    with pytest.raises(ValueError, match="pergunta"):
        agente.perguntar("   ")


def test_agente_envia_prompt_de_sistema() -> None:
    recebidas: list[list[Mensagem]] = []

    class Gravador:
        def responder(self, mensagens: list[Mensagem], ferramentas: list[Ferramenta]) -> Resposta:
            recebidas.append(list(mensagens))
            return Resposta(texto="ok")

    agente = Agente(Gravador(), [], sistema="Você é um analista.")
    agente.perguntar("oi")

    assert [mensagem.papel for mensagem in recebidas[0]] == ["system", "user"]
    assert recebidas[0][0].conteudo == "Você é um analista."


def test_agente_rejeita_ferramenta_duplicada() -> None:
    with pytest.raises(ValueError, match="duplicada"):
        Agente(ProvedorFalso(padrao="ok"), [criar_ferramenta_soma(), criar_ferramenta_soma()])


def test_provedor_falso_sem_regra_e_sem_padrao_avisa() -> None:
    agente = Agente(ProvedorFalso(), [])

    with pytest.raises(SemResposta, match="nenhuma regra"):
        agente.perguntar("pergunta sem regra")


def test_provedor_falso_casa_palavra_chave_ignorando_caixa() -> None:
    provedor = ProvedorFalso(
        regras=[
            ("receita", Resposta(texto="receita")),
            ("ticket", Resposta(texto="ticket")),
        ]
    )

    assert provedor.responder([Mensagem("user", "Qual a RECEITA?")], []).texto == "receita"
    assert provedor.responder([Mensagem("user", "qual o ticket?")], []).texto == "ticket"


def test_provedor_openai_sem_chave_esta_indisponivel() -> None:
    provedor = ProvedorOpenAI(modelo="m", base_url="https://exemplo.invalid/v1", api_key="")

    assert not provedor.disponivel
    with pytest.raises(ProvedorIndisponivel, match="OPENAI_API_KEY"):
        provedor.responder([Mensagem("user", "oi")], [])


def test_provedor_openai_interpreta_tool_call(monkeypatch: pytest.MonkeyPatch) -> None:
    def post_falso(url: str, corpo: dict[str, Any], api_key: str, timeout: float) -> dict:
        return {
            "choices": [
                {
                    "message": {
                        "content": None,
                        "tool_calls": [
                            {
                                "function": {
                                    "name": "somar",
                                    "arguments": '{"a": 1, "b": 2}',
                                }
                            }
                        ],
                    }
                }
            ]
        }

    monkeypatch.setattr(llm, "_post_json", post_falso)
    provedor = ProvedorOpenAI(base_url="https://exemplo.invalid/v1", api_key="chave-de-teste")

    resposta = provedor.responder([Mensagem("user", "some 1 + 2")], [criar_ferramenta_soma()])

    assert resposta.texto == ""
    assert resposta.chamada == ChamadaFerramenta("somar", {"a": 1, "b": 2})


def test_provedor_openai_rejeita_resposta_fora_do_formato(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(llm, "_post_json", lambda *args, **kwargs: {"choices": []})
    provedor = ProvedorOpenAI(base_url="https://exemplo.invalid/v1", api_key="chave-de-teste")

    with pytest.raises(RespostaInvalida, match="choices"):
        provedor.responder([Mensagem("user", "oi")], [])


def test_ferramenta_valida_tipo_dos_argumentos() -> None:
    ferramenta = Ferramenta("contar", "x", {"n": "integer"}, lambda n: n)

    with pytest.raises(ValueError, match="tipo inválido"):
        ferramenta.executar({"n": "2"})
    with pytest.raises(ValueError, match="tipo inválido"):
        ferramenta.executar({"n": 2.5})
    with pytest.raises(ValueError, match="tipo inválido"):
        ferramenta.executar({"n": True})
    assert ferramenta.executar({"n": 2}) == 2


def test_ferramenta_aceita_number_e_rejeita_numero_em_string() -> None:
    numero = Ferramenta("numero", "x", {"v": "number"}, lambda v: v)
    assert numero.executar({"v": 2}) == 2
    assert numero.executar({"v": 2.5}) == 2.5

    texto = Ferramenta("texto", "x", {"v": "string"}, lambda v: v)
    with pytest.raises(ValueError, match="tipo inválido"):
        texto.executar({"v": 1})

    with pytest.raises(ValueError, match="tipo inválido"):
        numero.executar({"v": "10.5"})


def test_agente_executa_multiplas_ferramentas_na_mesma_rodada() -> None:
    historicos: list[list[Mensagem]] = []

    class DuasChamadas:
        def responder(
            self,
            mensagens: list[Mensagem],
            ferramentas: list[Ferramenta],
        ) -> Resposta:
            historicos.append(list(mensagens))
            if mensagens[-1].papel == "tool":
                return Resposta(texto="pronto")
            return Resposta(
                chamadas=(
                    ChamadaFerramenta("somar", {"a": 1, "b": 1}, id="c1"),
                    ChamadaFerramenta("somar", {"a": 2, "b": 2}, id="c2"),
                )
            )

    agente = Agente(DuasChamadas(), [criar_ferramenta_soma()])

    assert agente.perguntar("some dois pares") == "pronto"

    segunda = historicos[-1]
    assistente = next(mensagem for mensagem in segunda if mensagem.papel == "assistant")
    assert [chamada["id"] for chamada in assistente.tool_calls] == ["c1", "c2"]
    ferramentas = [mensagem for mensagem in segunda if mensagem.papel == "tool"]
    assert [mensagem.tool_call_id for mensagem in ferramentas] == ["c1", "c2"]


def test_agente_gera_id_local_quando_provedor_nao_manda() -> None:
    historicos: list[list[Mensagem]] = []

    class SemId:
        def responder(
            self,
            mensagens: list[Mensagem],
            ferramentas: list[Ferramenta],
        ) -> Resposta:
            historicos.append(list(mensagens))
            if any(mensagem.papel == "tool" for mensagem in mensagens):
                return Resposta(texto="ok")
            return Resposta(chamada=ChamadaFerramenta("somar", {"a": 1, "b": 2}))

    agente = Agente(SemId(), [criar_ferramenta_soma()])

    assert agente.perguntar("some") == "ok"
    ferramenta = next(mensagem for mensagem in historicos[-1] if mensagem.papel == "tool")
    assert ferramenta.tool_call_id == "call_0_0"


def test_provedor_openai_interpreta_varias_chamadas(monkeypatch: pytest.MonkeyPatch) -> None:
    def post_falso(url: str, corpo: dict[str, Any], api_key: str, timeout: float) -> dict:
        return {
            "choices": [
                {
                    "message": {
                        "content": None,
                        "tool_calls": [
                            {
                                "id": "c1",
                                "function": {"name": "somar", "arguments": '{"a": 1, "b": 2}'},
                            },
                            {
                                "id": "c2",
                                "function": {"name": "somar", "arguments": '{"a": 3, "b": 4}'},
                            },
                        ],
                    }
                }
            ]
        }

    monkeypatch.setattr(llm, "_post_json", post_falso)
    provedor = ProvedorOpenAI(base_url="https://exemplo.invalid/v1", api_key="chave")

    resposta = provedor.responder([Mensagem("user", "some")], [criar_ferramenta_soma()])

    assert [chamada.id for chamada in resposta.chamadas] == ["c1", "c2"]
    assert resposta.chamada is not None
    assert resposta.chamada.id == "c1"


def test_provedor_openai_envia_tool_call_id_e_estrutura(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    capturado: dict[str, Any] = {}

    def post_falso(url: str, corpo: dict[str, Any], api_key: str, timeout: float) -> dict:
        capturado.update(corpo)
        return {"choices": [{"message": {"content": "fim"}}]}

    monkeypatch.setattr(llm, "_post_json", post_falso)
    provedor = ProvedorOpenAI(base_url="https://exemplo.invalid/v1", api_key="chave")
    mensagens = [
        Mensagem(
            "assistant",
            "",
            tool_calls=(
                {
                    "id": "c1",
                    "type": "function",
                    "function": {"name": "somar", "arguments": "{}"},
                },
            ),
        ),
        Mensagem("tool", "3", tool_call_id="c1"),
    ]

    provedor.responder(mensagens, [])

    assert capturado["messages"][0]["tool_calls"][0]["id"] == "c1"
    assert capturado["messages"][0]["content"] is None
    assert capturado["messages"][1]["tool_call_id"] == "c1"


def test_provedor_openai_usa_endpoint_padrao(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)

    provedor = ProvedorOpenAI(api_key="chave")

    assert provedor.disponivel
    assert provedor.base_url == "https://api.openai.com/v1"


def test_agente_devolve_erro_da_ferramenta_ao_modelo() -> None:
    historicos: list[list[Mensagem]] = []

    def explodir() -> None:
        raise RuntimeError("banco fora do ar")

    class ComErro:
        def responder(
            self,
            mensagens: list[Mensagem],
            ferramentas: list[Ferramenta],
        ) -> Resposta:
            historicos.append(list(mensagens))
            if mensagens[-1].papel == "tool":
                return Resposta(texto=f"falhou: {mensagens[-1].conteudo}")
            return Resposta(chamada=ChamadaFerramenta("explodir"))

    agente = Agente(ComErro(), [Ferramenta("explodir", "x", {}, explodir)])

    resposta = agente.perguntar("consulte")

    assert "RuntimeError: banco fora do ar" in resposta
    resultado = next(mensagem for mensagem in historicos[-1] if mensagem.papel == "tool")
    assert resultado.tool_call_id == "call_0_0"


def test_agente_devolve_erro_de_resultado_nao_serializavel() -> None:
    class ComObjeto:
        def responder(
            self,
            mensagens: list[Mensagem],
            ferramentas: list[Ferramenta],
        ) -> Resposta:
            if mensagens[-1].papel == "tool":
                return Resposta(texto=mensagens[-1].conteudo)
            return Resposta(chamada=ChamadaFerramenta("objeto"))

    ferramenta = Ferramenta("objeto", "x", {}, object)
    agente = Agente(ComObjeto(), [ferramenta])

    resposta = agente.perguntar("me de um objeto")

    assert "TypeError" in resposta
    assert "não serializável" in resposta


def test_provedor_openai_traduz_http_error(monkeypatch: pytest.MonkeyPatch) -> None:
    def urlopen_que_falha(*args: Any, **kwargs: Any) -> Any:
        raise llm.error.HTTPError(
            "https://exemplo.invalid/v1/chat/completions",
            401,
            "Unauthorized",
            {},
            None,
        )

    monkeypatch.setattr(llm.request, "urlopen", urlopen_que_falha)
    provedor = ProvedorOpenAI(base_url="https://exemplo.invalid/v1", api_key="chave")

    with pytest.raises(ProvedorIndisponivel, match="HTTP 401"):
        provedor.responder([Mensagem("user", "oi")], [])


def test_provedor_openai_inclui_corpo_do_http_error(monkeypatch: pytest.MonkeyPatch) -> None:
    def urlopen_que_falha(*args: Any, **kwargs: Any) -> Any:
        raise llm.error.HTTPError(
            "https://exemplo.invalid/v1/chat/completions",
            400,
            "Bad Request",
            {},
            io.BytesIO(b'{"error": {"message": "schema invalido"}}'),
        )

    monkeypatch.setattr(llm.request, "urlopen", urlopen_que_falha)
    provedor = ProvedorOpenAI(base_url="https://exemplo.invalid/v1", api_key="chave")

    with pytest.raises(ProvedorIndisponivel, match="schema invalido"):
        provedor.responder([Mensagem("user", "oi")], [])


def test_agente_devolve_erro_de_schema_ao_modelo() -> None:
    # Contrato quebrado não derruba o loop: o modelo vê o erro e pode corrigir os argumentos.
    class ComSchemaErrado:
        def responder(
            self,
            mensagens: list[Mensagem],
            ferramentas: list[Ferramenta],
        ) -> Resposta:
            if mensagens[-1].papel == "tool":
                return Resposta(texto=mensagens[-1].conteudo)
            return Resposta(chamada=ChamadaFerramenta("contar", {"n": "dois"}))

    ferramenta = Ferramenta("contar", "x", {"n": "integer"}, lambda n: n)
    agente = Agente(ComSchemaErrado(), [ferramenta])

    resposta = agente.perguntar("conte")

    assert "tipo inválido" in resposta


def test_provedor_openai_traduz_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    def urlopen_que_estoura(*args: Any, **kwargs: Any) -> Any:
        raise TimeoutError("demorou")

    monkeypatch.setattr(llm.request, "urlopen", urlopen_que_estoura)
    provedor = ProvedorOpenAI(base_url="https://exemplo.invalid/v1", api_key="chave")

    with pytest.raises(ProvedorIndisponivel, match="timeout"):
        provedor.responder([Mensagem("user", "oi")], [])


def test_provedor_openai_traduz_timeout_embrulhado_em_urlerror(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def urlopen_que_estoura(*args: Any, **kwargs: Any) -> Any:
        raise llm.error.URLError(TimeoutError("timed out"))

    monkeypatch.setattr(llm.request, "urlopen", urlopen_que_estoura)
    provedor = ProvedorOpenAI(base_url="https://exemplo.invalid/v1", api_key="chave")

    with pytest.raises(ProvedorIndisponivel, match="timeout"):
        provedor.responder([Mensagem("user", "oi")], [])


def test_provedor_openai_preserva_texto_junto_da_chamada(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def post_falso(url: str, corpo: dict[str, Any], api_key: str, timeout: float) -> dict:
        return {
            "choices": [
                {
                    "message": {
                        "content": "vou consultar",
                        "tool_calls": [
                            {"id": "c1", "function": {"name": "somar", "arguments": "{}"}}
                        ],
                    }
                }
            ]
        }

    monkeypatch.setattr(llm, "_post_json", post_falso)
    provedor = ProvedorOpenAI(base_url="https://exemplo.invalid/v1", api_key="chave")

    resposta = provedor.responder([Mensagem("user", "some")], [criar_ferramenta_soma()])

    assert resposta.texto == "vou consultar"
    assert resposta.chamada == ChamadaFerramenta("somar", {}, id="c1")


def test_provedor_falso_finaliza_com_todos_os_resultados_da_rodada() -> None:
    provedor = ProvedorFalso(finalizador=lambda conteudo: conteudo)
    mensagens = [
        Mensagem("user", "some"),
        Mensagem("assistant", "", tool_calls=({"id": "c1"}, {"id": "c2"})),
        Mensagem("tool", "3", tool_call_id="c1"),
        Mensagem("tool", "7", tool_call_id="c2"),
    ]

    resposta = provedor.responder(mensagens, [])

    assert resposta.texto == "3 | 7"


def test_ferramenta_rejeita_nan_e_infinito() -> None:
    numero = Ferramenta("numero", "x", {"v": "number"}, lambda v: v)

    with pytest.raises(ValueError, match="tipo inválido"):
        numero.executar({"v": float("nan")})
    with pytest.raises(ValueError, match="tipo inválido"):
        numero.executar({"v": float("inf")})


def test_ferramenta_rejeita_tipo_desconhecido_no_schema() -> None:
    with pytest.raises(ValueError, match="tipo inválido para 'v'"):
        Ferramenta("x", "x", {"v": "stringg"}, lambda v: v)


def test_agente_propaga_memory_error() -> None:
    def sem_memoria() -> None:
        raise MemoryError("acabou a memoria")

    class Teimoso:
        def responder(
            self,
            mensagens: list[Mensagem],
            ferramentas: list[Ferramenta],
        ) -> Resposta:
            return Resposta(chamada=ChamadaFerramenta("sem_memoria"))

    agente = Agente(Teimoso(), [Ferramenta("sem_memoria", "x", {}, sem_memoria)])

    with pytest.raises(MemoryError):
        agente.perguntar("consulte")


def test_provedor_openai_inclui_mensagem_de_erro_da_api(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        llm, "_post_json", lambda *args, **kwargs: {"error": {"message": "cota excedida"}}
    )
    provedor = ProvedorOpenAI(base_url="https://exemplo.invalid/v1", api_key="chave")

    with pytest.raises(RespostaInvalida, match="cota excedida"):
        provedor.responder([Mensagem("user", "oi")], [])


def test_provedor_openai_normaliza_argumentos_nulos(monkeypatch: pytest.MonkeyPatch) -> None:
    def post_falso(url: str, corpo: dict[str, Any], api_key: str, timeout: float) -> dict:
        return {
            "choices": [
                {
                    "message": {
                        "content": None,
                        "tool_calls": [
                            {"id": "c1", "function": {"name": "somar", "arguments": "null"}}
                        ],
                    }
                }
            ]
        }

    monkeypatch.setattr(llm, "_post_json", post_falso)
    provedor = ProvedorOpenAI(base_url="https://exemplo.invalid/v1", api_key="chave")

    resposta = provedor.responder([Mensagem("user", "some")], [criar_ferramenta_soma()])

    assert resposta.chamada == ChamadaFerramenta("somar", {}, id="c1")
