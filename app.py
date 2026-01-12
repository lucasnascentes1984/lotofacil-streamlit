import streamlit as st
import requests
from typing import List, Optional, Dict, Any
from datetime import datetime, date


# --- Jogos ---
GAMES: List[List[int]] = [
    [2, 3, 4, 6, 7, 8, 11, 12, 14, 16, 17, 18, 21, 22, 23],
    [1, 4, 5, 8, 9, 10, 12, 13, 15, 19, 20, 22, 23, 24, 25],
    [1, 2, 4, 6, 7, 8, 9, 12, 13, 17, 18, 21, 22, 23, 24],
    [2, 4, 5, 6, 7, 8, 10, 14, 16, 18, 19, 20, 21, 24, 25],
]

EXTRA_GAMES: List[List[int]] = [
    [3, 4, 5, 8, 9, 10, 13, 14, 15, 18, 19, 20, 23, 24, 25],
    [3, 5, 6, 7, 10, 11, 12, 13, 16, 17, 18, 20, 21, 22, 23],
    [3, 4, 7, 8, 9, 11, 12, 13, 14, 17, 18, 19, 22, 23, 24],
]

BASE_URLS: List[str] = [
    "https://servicebus2.caixa.gov.br/portaldeloterias/api/lotofacil",
    "https://www.caixa.gov.br/loterias/_cache/webapi/lotofacil",
]


# --- Utilitários ---
def formatar_moeda_br(valor: float) -> str:
    valor_int = int(round(float(valor) * 100))
    reais = valor_int // 100
    centavos = valor_int % 100
    reais_str = f"{reais:,}".replace(",", ".")
    return f"R$ {reais_str},{centavos:02d}"


def _to_float_brasil(valor: Any) -> float:
    try:
        if isinstance(valor, (int, float)):
            return float(valor)
        s = str(valor).strip()
        s = s.replace("R$", "").strip()
        s = s.replace(".", "").replace(",", ".")
        return float(s)
    except Exception:
        return 0.0


def _headers() -> Dict[str, str]:
    return {"Accept": "application/json", "User-Agent": "Mozilla/5.0"}


def _is_json_response(resp: requests.Response) -> bool:
    content_type = (resp.headers.get("content-type") or "").lower()
    return "json" in content_type


@st.cache_data(ttl=3600)
def buscar_resultado(concurso: Optional[int]) -> Dict[str, Any]:
    last_error: Optional[Exception] = None

    for base in BASE_URLS:
        url = base if concurso is None else f"{base}/{concurso}"
        try:
            r = requests.get(url, headers=_headers(), timeout=20)
            r.raise_for_status()

            if not _is_json_response(r):
                raise RuntimeError("A resposta não veio em JSON (content-type inesperado).")

            data = r.json()

            if any(k in data for k in ("dezenasSorteadasOrdemSorteio", "listaDezenas", "dezenasSorteadas")):
                return data

            raise RuntimeError("JSON recebido, mas não encontrei campos esperados de dezenas.")
        except Exception as e:
            last_error = e
            continue

    raise RuntimeError(f"Não consegui consultar o resultado na Caixa. Detalhe: {last_error}")


def extrair_dezenas_sorteadas(data: Dict[str, Any]) -> List[int]:
    dezenas = (
        data.get("dezenasSorteadasOrdemSorteio")
        or data.get("listaDezenas")
        or data.get("dezenasSorteadas")
    )

    if not dezenas or not isinstance(dezenas, list):
        raise RuntimeError("Não encontrei as dezenas sorteadas no retorno da Caixa.")

    dezenas_int = [int(x) for x in dezenas]

    if len(dezenas_int) != 15:
        raise RuntimeError(f"Esperado 15 dezenas sorteadas, veio {len(dezenas_int)}.")

    if len(set(dezenas_int)) != 15:
        raise RuntimeError("As dezenas sorteadas não são únicas (duplicadas).")

    if any(d < 1 or d > 25 for d in dezenas_int):
        raise RuntimeError("Há dezenas sorteadas fora do intervalo 1..25.")

    return sorted(dezenas_int)


def calcular_premio_por_acertos(data: Dict[str, Any], acertos: int) -> float:
    if acertos < 11 or acertos > 15:
        return 0.0

    faixa_esperada = 16 - acertos
    rateios = data.get("listaRateioPremio") or []
    if not isinstance(rateios, list):
        return 0.0

    for item in rateios:
        if not isinstance(item, dict):
            continue
        if item.get("faixa") == faixa_esperada:
            return _to_float_brasil(item.get("valorPremio", 0))

    return 0.0


def formatar_numeros(nums: List[int]) -> str:
    return " ".join(f"{n:02d}" for n in nums)


def parse_data_concurso(data: Dict[str, Any]) -> date:
    s = (data.get("dataApuracao") or data.get("data") or "").strip()
    if not s:
        raise RuntimeError("Não encontrei a data do concurso no retorno da Caixa.")

    try:
        return datetime.strptime(s, "%d/%m/%Y").date()
    except ValueError:
        pass

    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00")).date()
    except ValueError:
        raise RuntimeError(f"Formato de data inesperado: {s}")


def exibir_conferencia_de_jogos(
    titulo_bloco: str,
    jogos: List[List[int]],
    sorteadas: List[int],
    data: Dict[str, Any],
    prefixo_nome: str,
) -> float:
    total_bloco = 0.0
    st.markdown("---")
    st.subheader(titulo_bloco)

    for idx, jogo in enumerate(jogos, start=1):
        acertos_lista = sorted(set(jogo) & set(sorteadas))
        qtd = len(acertos_lista)
        premio = calcular_premio_por_acertos(data, qtd)
        total_bloco += premio

        st.markdown("---")
        st.subheader(f"{prefixo_nome} {idx}")
        st.write(f"**Números do jogo:** {formatar_numeros(sorted(jogo))}")
        st.write(f"**Acertos:** {qtd}")
        st.write(f"**Dezenas acertadas:** {formatar_numeros(acertos_lista) if acertos_lista else '—'}")

        faixa_txt = f"{qtd} acertos" if qtd >= 11 else "Não premiado"
        st.write(f"**Faixa:** {faixa_txt}")
        st.write(f"**Prêmio (conforme Caixa):** {formatar_moeda_br(premio)}")

        if qtd >= 11 and premio == 0.0:
            st.warning("Não consegui ler o valor do prêmio dessa faixa no retorno da Caixa (veio 0).")

    return total_bloco


def total_por_grupo(data: Dict[str, Any], sorteadas: List[int], jogos: List[List[int]]) -> float:
    total = 0.0
    sset = set(sorteadas)
    for jogo in jogos:
        acertos = len(set(jogo) & sset)
        total += calcular_premio_por_acertos(data, acertos)
    return total


# --- UI ---
st.set_page_config(page_title="Lotofácil 2026", layout="centered")
st.title("Lotofácil 2026")
st.caption("Lucas - Henrique - Bruno - Sergio")

# Checkboxes lado a lado (conferência normal)
col1, col2 = st.columns(2)
with col1:
    use_ultimo = st.checkbox("Usar último concurso", value=True)
with col2:
    usar_extras = st.checkbox("Jogos Extras", value=False)

concurso = st.number_input(
    "Número do concurso",
    min_value=1,
    step=1,
    disabled=use_ultimo,
    help="Desmarque 'Usar último concurso' para digitar um concurso específico.",
)

if st.button("Conferir", type="primary"):
    with st.spinner("Buscando dados do concurso na Caixa..."):
        try:
            concurso_num = None if use_ultimo else int(concurso)
            data = buscar_resultado(concurso_num)
            sorteadas = extrair_dezenas_sorteadas(data)

            numero_concurso = data.get("numero") or data.get("numeroConcurso") or (concurso_num if concurso_num else "N/A")
            data_apuracao = data.get("dataApuracao") or data.get("data") or "N/A"

            st.subheader(f"Concurso {numero_concurso} — Data: {data_apuracao}")
            st.write(f"**Dezenas sorteadas:** {formatar_numeros(sorteadas)}")

            total = 0.0

            total += exibir_conferencia_de_jogos(
                titulo_bloco="Jogos Fixos",
                jogos=GAMES,
                sorteadas=sorteadas,
                data=data,
                prefixo_nome="Jogo",
            )

            if usar_extras:
                with st.expander("Jogos Extras", expanded=True):
                    total += exibir_conferencia_de_jogos(
                        titulo_bloco="Conferência dos Jogos Extras",
                        jogos=EXTRA_GAMES,
                        sorteadas=sorteadas,
                        data=data,
                        prefixo_nome="Jogo Extra",
                    )

            st.markdown("---")
            st.subheader("Total")
            st.write(f"**Total ganho (somando os jogos selecionados):** {formatar_moeda_br(total)}")

        except Exception as e:
            st.error(f"Erro: {e}")


# --- Histórico com seleção de dias com Extras ---
st.markdown("---")
with st.expander("📅 Histórico", expanded=False):
    c1, c2 = st.columns(2)
    with c1:
        dt_ini = st.date_input("Data inicial")
    with c2:
        dt_fim = st.date_input("Data final")

    st.caption("Primeiro pesquise o período. Depois selecione os dias dos **Jogos Extras**.")

    top_actions = st.columns(2)
    with top_actions[0]:
        pesquisar = st.button("Pesquisar histórico")
    with top_actions[1]:
        limpar_hist = st.button("Limpar resultados do histórico")

    if limpar_hist:
        for k in [
            "hist_dias",
            "hist_fixos",
            "hist_extras",
            "hist_dias_extras_selecionados",
            "hist_extras_multiselect",
            "hist_action",
        ]:
            if k in st.session_state:
                del st.session_state[k]
        st.rerun()

    if pesquisar:
        if dt_ini > dt_fim:
            st.error("A **Data inicial** não pode ser maior que a **Data final**.")
        else:
            with st.spinner("Buscando histórico na Caixa..."):
                try:
                    data_ultimo = buscar_resultado(None)
                    ultimo_num = int(data_ultimo.get("numero") or data_ultimo.get("numeroConcurso"))

                    totais_fixos_por_dia: Dict[str, float] = {}
                    totais_extras_por_dia: Dict[str, float] = {}

                    limite_concursos = 700
                    verificados = 0

                    for num in range(ultimo_num, 0, -1):
                        if verificados >= limite_concursos:
                            st.warning(f"Limite de {limite_concursos} concursos atingido. Parando a busca.")
                            break

                        verificados += 1

                        try:
                            data = buscar_resultado(num)
                            dt_concurso = parse_data_concurso(data)

                            if dt_concurso < dt_ini:
                                break

                            if dt_ini <= dt_concurso <= dt_fim:
                                sorteadas = extrair_dezenas_sorteadas(data)

                                total_fixos = total_por_grupo(data, sorteadas, GAMES)
                                total_extras = total_por_grupo(data, sorteadas, EXTRA_GAMES)

                                chave = dt_concurso.strftime("%d/%m/%Y")
                                totais_fixos_por_dia[chave] = totais_fixos_por_dia.get(chave, 0.0) + total_fixos
                                totais_extras_por_dia[chave] = totais_extras_por_dia.get(chave, 0.0) + total_extras

                        except Exception:
                            continue

                    dias_disponiveis = sorted(
                        totais_fixos_por_dia.keys(),
                        key=lambda x: datetime.strptime(x, "%d/%m/%Y")
                    )

                    st.session_state["hist_dias"] = dias_disponiveis
                    st.session_state["hist_fixos"] = totais_fixos_por_dia
                    st.session_state["hist_extras"] = totais_extras_por_dia

                    # seleção aplicada (vale para o total)
                    st.session_state["hist_dias_extras_selecionados"] = []

                    # valor do widget multiselect (precisa existir antes do widget)
                    st.session_state["hist_extras_multiselect"] = []

                    st.session_state["hist_action"] = None

                    st.rerun()

                except Exception as e:
                    st.error(f"Erro ao pesquisar histórico: {e}")

    # Se já pesquisou, mostra a seleção de dias com extras e o resultado
    if st.session_state.get("hist_dias"):
        dias = st.session_state["hist_dias"]
        fixos = st.session_state["hist_fixos"]
        extras = st.session_state["hist_extras"]

        # Aplicar ações ANTES de instanciar o multiselect
        action = st.session_state.get("hist_action")
        if action == "select_all":
            st.session_state["hist_extras_multiselect"] = list(dias)
            st.session_state["hist_dias_extras_selecionados"] = list(dias)
            st.session_state["hist_action"] = None
        elif action == "clear":
            st.session_state["hist_extras_multiselect"] = []
            st.session_state["hist_dias_extras_selecionados"] = []
            st.session_state["hist_action"] = None

        st.markdown("---")
        st.subheader("Selecionar dias com Jogos Extras")

        sel_actions = st.columns(3)
        with sel_actions[0]:
            if st.button("Marcar todos"):
                st.session_state["hist_action"] = "select_all"
                st.rerun()
        with sel_actions[1]:
            if st.button("Limpar seleção"):
                st.session_state["hist_action"] = "clear"
                st.rerun()
        with sel_actions[2]:
            aplicar = st.button("Aplicar seleção de extras")

        # Widget (não mexer no st.session_state dessa key depois disso, na mesma execução)
        selecionados = st.multiselect(
            "Marque os dias dos Jogos Extras:",
            options=dias,
            key="hist_extras_multiselect",
        )

        if aplicar:
            st.session_state["hist_dias_extras_selecionados"] = list(selecionados)
            st.rerun()

        dias_extras_set = set(st.session_state.get("hist_dias_extras_selecionados", []))

        st.markdown("---")
        st.subheader("Resultado no período")

        total_periodo = 0.0
        for dia in dias:
            total_dia = fixos.get(dia, 0.0) + (extras.get(dia, 0.0) if dia in dias_extras_set else 0.0)
            total_periodo += total_dia
            st.write(f"{dia} — {formatar_moeda_br(total_dia)}")

        st.subheader("Total no período")
        st.write(f"**{formatar_moeda_br(total_periodo)}**")
