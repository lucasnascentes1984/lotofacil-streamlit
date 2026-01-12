import streamlit as st
import requests
from typing import List, Optional, Dict, Any


# Jogos fixos da Lotofácil
GAMES: List[List[int]] = [
    [2, 3, 4, 6, 7, 8, 11, 12, 14, 16, 17, 18, 21, 22, 23],
    [1, 4, 5, 8, 9, 10, 12, 13, 15, 19, 20, 22, 23, 24, 25],
    [1, 2, 4, 6, 7, 8, 9, 12, 13, 17, 18, 21, 22, 23, 24],
    [2, 4, 5, 6, 7, 8, 10, 14, 16, 18, 19, 20, 21, 24, 25],
]

# Jogos extras (ocasionais)
EXTRA_GAMES: List[List[int]] = [
    [3, 4, 5, 8, 9, 10, 13, 14, 15, 18, 19, 20, 23, 24, 25],
    [3, 5, 6, 7, 10, 11, 12, 13, 16, 17, 18, 20, 21, 22, 23],
    [3, 4, 7, 8, 9, 11, 12, 13, 14, 17, 18, 19, 22, 23, 24],
]

BASE_URLS: List[str] = [
    "https://servicebus2.caixa.gov.br/portaldeloterias/api/lotofacil",
    "https://www.caixa.gov.br/loterias/_cache/webapi/lotofacil",
]


def formatar_moeda_br(valor: float) -> str:
    # Formata: R$ 1.234,56 (sem depender de locale do sistema)
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


def buscar_resultado(concurso: Optional[int]) -> Dict[str, Any]:
    last_error = None

    for base in BASE_URLS:
        url = base if concurso is None else f"{base}/{concurso}"
        try:
            r = requests.get(url, headers=_headers(), timeout=20)
            r.raise_for_status()

            if not _is_json_response(r):
                raise RuntimeError("A resposta não veio em JSON (content-type inesperado).")

            data = r.json()

            # Heurística simples: se tem alguma das chaves de dezenas, consideramos OK
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
    # faixa: 1=15, 2=14, 3=13, 4=12, 5=11  => faixa = 16 - acertos
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


# --- UI ---
st.set_page_config(page_title="Lotofácil 2026", layout="centered")
st.title("Lotofácil 2026")
st.caption("Lucas - Henrique - Bruno - Sergio")

# Checkboxes lado a lado (como você sugeriu)
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

            # Jogos fixos (sempre)
            total += exibir_conferencia_de_jogos(
                titulo_bloco="Jogos Fixos",
                jogos=GAMES,
                sorteadas=sorteadas,
                data=data,
                prefixo_nome="Jogo",
            )

            # Jogos extras (só quando marcado)
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
