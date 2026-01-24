import streamlit as st
import requests
import os
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, date

st.set_page_config(page_title="Lotofácil 2026", layout="centered")
st.write("Feito por: Lucas Nascentes")

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
    [2, 4, 5, 6, 7, 8, 10, 14, 16, 18, 19, 20, 21, 24, 25],
]

BASE_URLS: List[str] = [
    "https://servicebus2.caixa.gov.br/portaldeloterias/api/lotofacil",
    "https://www.caixa.gov.br/loterias/_cache/webapi/lotofacil",
]

# Custo dos extras (3 jogos x R$ 3,50)
VALOR_JOGO_EXTRA = 3.50
QTD_JOGOS_EXTRAS_DIA = 3


# --- Visual (CSS) ---
def aplicar_tema_visual(modo: str):
    """
    modo: "Claro" ou "Escuro"
    """

    light_vars = """
      :root{
        --max: 900px;
        --space-1: 6px;
        --space-2: 10px;
        --space-3: 14px;
        --space-4: 18px;
        --space-5: 22px;
        --radius-1: 10px;
        --radius-2: 14px;

        --blue: #1F5AFF;
        --blue-border: rgba(31,90,255,0.16);

        --text: rgba(15,23,42,0.92);
        --muted: rgba(15,23,42,0.70);

        --card-bg: rgba(2, 6, 23, 0.02);

        --chip-bg: rgba(31,90,255,0.07);
        --chip-border: rgba(31,90,255,0.20);

        --chip-muted-bg: rgba(148,163,184,0.12);
        --chip-muted-border: rgba(148,163,184,0.35);
        --chip-muted-text: #334155;

        --chip-ok-bg: rgba(16,185,129,0.10);
        --chip-ok-border: rgba(16,185,129,0.25);
        --chip-ok-text: #059669;

        --header-grad-a: rgba(31,90,255,0.14);
        --header-grad-b: rgba(31,90,255,0.03);
        --header-splash: rgba(31,90,255,0.34);
        --header-caption: rgba(15, 23, 42, 0.62);

        /* >>> TOGGLE VISUAL (CLARO) */
        --toggle-track-off: rgba(148,163,184,0.60);
        --toggle-track-on: rgba(31,90,255,0.95);
        --toggle-knob: #ffffff;
        --toggle-outline: rgba(31,90,255,0.85);
        --toggle-bg: rgba(2, 6, 23, 0.10);
      }
    """

    dark_vars = """
      :root{
        --max: 900px;
        --space-1: 6px;
        --space-2: 10px;
        --space-3: 14px;
        --space-4: 18px;
        --space-5: 22px;
        --radius-1: 10px;
        --radius-2: 14px;

        --blue: #7AA2FF;
        --blue-border: rgba(122,162,255,0.22);

        --text: rgba(241,245,249,0.94);
        --muted: rgba(226,232,240,0.72);

        --card-bg: rgba(255,255,255,0.05);

        --chip-bg: rgba(122,162,255,0.12);
        --chip-border: rgba(122,162,255,0.30);

        --chip-muted-bg: rgba(148,163,184,0.10);
        --chip-muted-border: rgba(148,163,184,0.26);
        --chip-muted-text: rgba(241,245,249,0.86);

        --chip-ok-bg: rgba(16,185,129,0.18);
        --chip-ok-border: rgba(16,185,129,0.36);
        --chip-ok-text: rgba(167,243,208,0.96);

        --header-grad-a: rgba(122,162,255,0.18);
        --header-grad-b: rgba(122,162,255,0.04);
        --header-splash: rgba(122,162,255,0.40);
        --header-caption: rgba(226,232,240,0.76);

        /* >>> TOGGLE VISUAL (ESCURO) */
        --toggle-track-off: rgba(148,163,184,0.30);
        --toggle-track-on: rgba(122,162,255,0.92);
        --toggle-knob: rgba(255,255,255,0.95);
        --toggle-outline: rgba(122,162,255,0.45);
        --toggle-bg: rgba(122,162,255,0.08);
      }
    """

    if modo == "Escuro":
        vars_css = dark_vars
        force_page = """
          body, .stApp{
            background: #0b1220 !important;
            color: var(--text) !important;
          }
        """
    else:  # "Claro"
        vars_css = light_vars
        force_page = """
          body, .stApp{
            background: #ffffff !important;
            color: var(--text) !important;
          }
        """

    st.markdown(
        f"""
        <style>
          {vars_css}

          .block-container{{
            padding-top: 1rem;
            padding-bottom: 1.5rem;
            max-width: var(--max);
          }}

          {force_page}

          /* Texto */
          .stMarkdown, .stMarkdown p, .stMarkdown span, .stText, label, div, p {{
            color: var(--text);
          }}
          .stCaption, .stCaption p {{
            color: var(--muted) !important;
          }}

          /* >>> TOGGLE VISUAL */
          div[data-testid="stToggle"] {{
            padding: 10px 12px;
            border-radius: var(--radius-1);
            border: 2px solid var(--toggle-outline);
            background: var(--toggle-bg);
            box-shadow: 0 2px 8px rgba(0,0,0,0.10);
            transition: all 0.2s ease;
          }}
          div[data-testid="stToggle"]:hover {{
            box-shadow: 0 4px 12px rgba(0,0,0,0.20);
            border-color: var(--blue);
          }}
          div[data-testid="stToggle"] label {{
            font-weight: 700;
            font-size: 13px;
            color: var(--text);
          }}
          div[data-testid="stToggle"] label span {{
            background-color: var(--toggle-track-off) !important;
            border-radius: 12px;
          }}
          div[data-testid="stToggle"] label input:checked + span {{
            background-color: var(--toggle-track-on) !important;
          }}
          div[data-testid="stToggle"] label span::before {{
            background-color: var(--toggle-knob) !important;
            box-shadow: 0 2px 8px rgba(0,0,0,0.25) !important;
            width: 18px;
            height: 18px;
          }}
          div[data-testid="stToggle"] label:focus-within {{
            outline: 3px solid var(--toggle-outline);
            outline-offset: 2px;
            border-radius: var(--radius-1);
          }}

          /* HEADER */
          #lf-header{{
            position: relative;
            overflow: hidden;
            padding: var(--space-3) var(--space-3);
            border-radius: var(--radius-1);
            background: linear-gradient(135deg, var(--header-grad-a), var(--header-grad-b));
            border: 1px solid var(--blue-border);
            margin-bottom: var(--space-2);
          }}
          #lf-header::before{{
            content:"";
            position:absolute;
            top:-85px;
            right:-85px;
            width: 200px;
            height: 200px;
            background: radial-gradient(circle at 35% 35%, var(--header-splash), rgba(0,0,0,0) 70%);
            transform: rotate(12deg);
          }}
          #lf-header .title{{
            font-size: 1.5rem;
            font-weight: 800;
            margin: 0;
            letter-spacing: -0.6px;
            color: var(--text);
          }}
          #lf-header .subtitle{{
            margin: 4px 0 0 0;
            font-size: 0.9rem;
            color: var(--blue);
            font-weight: 600;
          }}
          #lf-header .caption{{
            margin-top: 4px;
            color: var(--header-caption);
            font-size: 0.85rem;
          }}

          /* Botões */
          div.stButton > button{{
            border-radius: var(--radius-1);
            padding: 0.5rem 0.9rem;
            font-weight: 600;
          }}

          /* Chips */
          .chip-wrap{{ display:flex; flex-wrap:wrap; gap:6px; margin:6px 0 2px 0; }}
          .chip{{
            width:36px; height:36px;
            border-radius:999px;
            display:inline-flex;
            align-items:center;
            justify-content:center;
            font-weight:700;
            font-size:13px;
            user-select:none;
            border:1px solid var(--chip-border);
            background: var(--chip-bg);
            color: var(--blue);
          }}
          .chip--ok{{
            border:1px solid var(--chip-ok-border);
            background: var(--chip-ok-bg);
            color: var(--chip-ok-text);
          }}
          .chip--muted{{
            border:1px solid var(--chip-muted-border);
            background: var(--chip-muted-bg);
            color: var(--chip-muted-text);
          }}

          /* Métricas */
          [data-testid="stMetric"]{{
            background: var(--card-bg);
            padding: var(--space-2);
            border-radius: var(--radius-1);
          }}
          [data-testid="stMetricLabel"] p{{ color: var(--muted) !important; font-size: 0.85rem !important; }}

          .small-muted{{
            font-size: 0.85rem;
            color: var(--muted);
            margin-top: 0.1rem;
            margin-bottom: 0.3rem;
            line-height: 1.1rem;
            word-break: break-word;
          }}

          hr{{ margin: 0.5rem 0; opacity: 0.55; }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_chips(nums: List[int], variant: str = "default"):
    cls = "chip"
    if variant == "ok":
        cls += " chip--ok"
    elif variant == "muted":
        cls += " chip--muted"

    html = '<div class="chip-wrap">' + "".join(
        f'<span class="{cls}">{n:02d}</span>' for n in nums
    ) + "</div>"
    st.markdown(html, unsafe_allow_html=True)


def render_chips_com_acertos(nums: List[int], acertos_set: set):
    html_parts = ['<div class="chip-wrap">']
    for n in nums:
        cls = "chip chip--ok" if n in acertos_set else "chip chip--muted"
        html_parts.append(f'<span class="{cls}">{n:02d}</span>')
    html_parts.append("</div>")
    st.markdown("".join(html_parts), unsafe_allow_html=True)


# --- Utilitários ---
def formatar_moeda_br(valor: float) -> str:
    cent = int(round(float(valor) * 100))
    sinal = "-" if cent < 0 else ""
    cent_abs = abs(cent)

    reais = cent_abs // 100
    centavos = cent_abs % 100

    reais_str = f"{reais:,}".replace(",", ".")
    return f"{sinal}R$ {reais_str},{centavos:02d}"


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
    st.subheader(titulo_bloco)

    sorteadas_set = set(sorteadas)

    for idx, jogo in enumerate(jogos, start=1):
        acertos_set = set(jogo) & sorteadas_set
        qtd = len(acertos_set)
        premio = calcular_premio_por_acertos(data, qtd)
        total_bloco += premio

        with st.container(border=True):
            st.markdown(f"### {prefixo_nome} {idx}")

            c1, c2, c3 = st.columns(3)
            with c1:
                st.metric("Acertos", f"{qtd}")
            with c2:
                st.markdown("<p style='font-size: 0.85rem; color: var(--muted); margin-bottom: 5px;'>Resultado</p>",
                            unsafe_allow_html=True)
                if qtd >= 11:
                    img_file = "certo.png"
                else:
                    img_file = "errado.png"

                if os.path.exists(img_file):
                    st.image(img_file, width=45)
                else:
                    st.warning(f"Falta: {img_file}")
            with c3:
                st.metric("Prêmio", formatar_moeda_br(premio))

            st.write("**Números do jogo:**")
            render_chips_com_acertos(sorted(jogo), acertos_set)

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


def calcular_frequencia_no_periodo(dt_ini: date, dt_fim: date) -> Tuple[Dict[int, int], int]:
    if dt_ini > dt_fim:
        raise RuntimeError("Data inicial maior que a data final.")

    freq: Dict[int, int] = {i: 0 for i in range(1, 26)}
    concursos_encontrados = 0

    data_ultimo = buscar_resultado(None)
    ultimo_num = int(data_ultimo.get("numero") or data_ultimo.get("numeroConcurso"))

    limite_concursos = 900
    verificados = 0

    for num in range(ultimo_num, 0, -1):
        if verificados >= limite_concursos:
            break
        verificados += 1

        try:
            data = buscar_resultado(num)
            dt_concurso = parse_data_concurso(data)

            if dt_concurso < dt_ini:
                break

            if dt_ini <= dt_concurso <= dt_fim:
                dezenas = extrair_dezenas_sorteadas(data)
                for d in dezenas:
                    freq[d] += 1
                concursos_encontrados += 1

        except Exception:
            continue

    return freq, concursos_encontrados


def montar_jogo_por_frequencia(freq: Dict[int, int], qtd_dezenas: int, modo: str) -> List[int]:
    if qtd_dezenas not in (15, 16):
        raise RuntimeError("Quantidade de dezenas inválida (use 15 ou 16).")

    itens = list(freq.items())

    if modo == "mais":
        itens.sort(key=lambda x: (-x[1], x[0]))
    elif modo == "menos":
        itens.sort(key=lambda x: (x[1], x[0]))
    else:
        raise RuntimeError("Modo inválido (use 'mais' ou 'menos').")

    jogo = [dez for dez, _cnt in itens[:qtd_dezenas]]
    return sorted(jogo)


# --- TELA INICIAL DE SELEÇÃO DE TEMA ---
if "tema_selecionado" not in st.session_state:
    st.session_state["tema_selecionado"] = None

if st.session_state["tema_selecionado"] is None:
    st.markdown(
        """
        <div style="text-align: center; padding: 2rem;">
          <h1>🎯 Lotofácil 2026</h1>
          <p style="font-size: 1.2rem; margin: 1rem 0;">Qual aparência você deseja usar?</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns(2)
    with col1:
        if st.button("☀️ Claro", type="primary", use_container_width=True):
            st.session_state["tema_selecionado"] = "Claro"
            st.rerun()
    with col2:
        if st.button("🌙 Escuro", type="primary", use_container_width=True):
            st.session_state["tema_selecionado"] = "Escuro"
            st.rerun()

    st.stop()

# --- Aplicar tema selecionado ---
modo_visual = st.session_state["tema_selecionado"]
aplicar_tema_visual(modo_visual)

# --- Toggle no topo ---
top_left, top_right = st.columns([3, 1])
with top_right:
    modo_escuro_toggle = st.toggle("Escuro", value=(modo_visual == "Escuro"),
                                   help="Desligado = Claro | Ligado = Escuro")
    if modo_escuro_toggle != (modo_visual == "Escuro"):
        st.session_state["tema_selecionado"] = "Escuro" if modo_escuro_toggle else "Claro"
        st.rerun()

# --- Header ---
st.markdown(
    """
    <div id="lf-header">
      <div class="title">Lotofácil 2026</div>
      <div class="subtitle">Conferência, histórico e sugestões de jogos</div>
      <div class="caption">Lucas - Henrique - Bruno - Sergio</div>
    </div>
    """,
    unsafe_allow_html=True,
)

# --- Conferência ---
with st.container(border=True):
    st.subheader("Conferência do concurso")

    col1, col2 = st.columns(2)
    with col1:
        use_ultimo = st.checkbox("Último concurso", value=True)
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

                numero_concurso = data.get("numero") or data.get("numeroConcurso") or (
                    concurso_num if concurso_num else "N/A"
                )
                data_apuracao = data.get("dataApuracao") or data.get("data") or "N/A"

                with st.container(border=True):
                    st.subheader(f"Concurso {numero_concurso}")
                    st.caption(f"Data: {data_apuracao}")
                    st.write("**Dezenas sorteadas:**")
                    render_chips(sorteadas, variant="default")

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

                with st.container(border=True):
                    st.subheader("Total")
                    st.metric("Total ganho (somando os jogos selecionados)", formatar_moeda_br(total))

            except Exception as e:
                st.error(f"Erro: {e}")

# --- Histórico ---
with st.expander("📅 Histórico", expanded=False):
    c1, c2 = st.columns(2)
    with c1:
        dt_ini = st.date_input("Data inicial", key="hist_ini")
    with c2:
        dt_fim = st.date_input("Data final", key="hist_fim")

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
                        key=lambda x: datetime.strptime(x, "%d/%m/%Y"),
                    )

                    st.session_state["hist_dias"] = dias_disponiveis
                    st.session_state["hist_fixos"] = totais_fixos_por_dia
                    st.session_state["hist_extras"] = totais_extras_por_dia

                    st.session_state["hist_extras_multiselect"] = []
                    st.session_state["hist_action"] = None

                    st.rerun()

                except Exception as e:
                    st.error(f"Erro ao pesquisar histórico: {e}")

    if st.session_state.get("hist_dias"):
        dias = st.session_state["hist_dias"]
        fixos = st.session_state["hist_fixos"]
        extras = st.session_state["hist_extras"]

        action = st.session_state.get("hist_action")
        if action == "select_all":
            st.session_state["hist_extras_multiselect"] = list(dias)
            st.session_state["hist_action"] = None
            st.rerun()
        elif action == "clear":
            st.session_state["hist_extras_multiselect"] = []
            st.session_state["hist_action"] = None
            st.rerun()

        st.subheader("Selecionar dias com Jogos Extras")

        sel_actions = st.columns(2)
        with sel_actions[0]:
            if st.button("Marcar todos"):
                st.session_state["hist_action"] = "select_all"
                st.rerun()
        with sel_actions[1]:
            if st.button("Limpar seleção"):
                st.session_state["hist_action"] = "clear"
                st.rerun()

        selecionados = st.multiselect(
            "Marque os dias dos Jogos Extras:",
            options=dias,
            key="hist_extras_multiselect",
        )
        dias_extras_set = set(selecionados)

        st.subheader("Resultado no período")

        total_periodo = 0.0

        cols_per_row = 3
        cols = st.columns(cols_per_row)

        for i, dia in enumerate(dias):
            total_fixos = fixos.get(dia, 0.0)
            total_extras = extras.get(dia, 0.0) if dia in dias_extras_set else 0.0

            custo_extras = (VALOR_JOGO_EXTRA * QTD_JOGOS_EXTRAS_DIA) if dia in dias_extras_set else 0.0

            total_dia_bruto = total_fixos + total_extras
            total_dia_liquido = total_dia_bruto - custo_extras
            total_periodo += total_dia_liquido

            col = cols[i % cols_per_row]
            with col:
                with st.container(border=True):
                    left, right = st.columns([1.2, 1])
                    with left:
                        st.markdown(f"### {dia}")
                        st.caption("Extras: ✅" if dia in dias_extras_set else "Extras: —")
                    with right:
                        st.metric("Total do dia (líquido)", formatar_moeda_br(total_dia_liquido))

                    det1, det2 = st.columns(2)
                    with det1:
                        st.caption(f"Fixos: {formatar_moeda_br(total_fixos)}")
                        st.caption(f"Custo extras: {formatar_moeda_br(custo_extras)}")
                    with det2:
                        st.caption(f"Extras (prêmios): {formatar_moeda_br(total_extras)}")
                        st.caption(f"Bruto: {formatar_moeda_br(total_dia_bruto)}")

            # --- CORREÇÃO AQUI (já aplicada para você) ---
            if (i + 1) % cols_per_row == 0 and (i + 1) < len(dias):
                cols = st.columns(cols_per_row)

        st.subheader("Total no período")
        st.metric("Total (líquido)", formatar_moeda_br(total_periodo))

# --- Sugestão de jogos ---
with st.expander("📊 Sugestão de jogos", expanded=False):
    a1, a2 = st.columns(2)
    with a1:
        analise_ini = st.date_input("Data inicial", key="analise_ini")
    with a2:
        analise_fim = st.date_input("Data final", key="analise_fim")

    qtd_dezenas = st.radio("Quantidade de dezenas", options=[15, 16], horizontal=True)

    if st.button("Gerar jogos sugeridos"):
        if analise_ini > analise_fim:
            st.error("A **Data inicial** não pode ser maior que a **Data final**.")
        else:
            with st.spinner("Lendo concursos do período e calculando frequências..."):
                try:
                    freq, concursos_encontrados = calcular_frequencia_no_periodo(analise_ini, analise_fim)

                    if concursos_encontrados == 0:
                        st.warning("Não encontrei concursos dentro do período selecionado.")
                    else:
                        with st.container(border=True):
                            st.subheader("Resumo da análise")
                            periodo_txt = f"{analise_ini.strftime('%d/%m/%Y')} a {analise_fim.strftime('%d/%m/%Y')}"
                            st.markdown(
                                f'<div class="small-muted"><b>Período:</b> {periodo_txt}</div>',
                                unsafe_allow_html=True,
                            )

                            c1, c2 = st.columns(2)
                            with c1:
                                st.metric("Quantidade de Concursos", f"{concursos_encontrados}")
                            with c2:
                                st.metric("Jogos", f"{qtd_dezenas} dezenas")

                        jogo_mais = montar_jogo_por_frequencia(freq, qtd_dezenas=qtd_dezenas, modo="mais")
                        jogo_menos = montar_jogo_por_frequencia(freq, qtd_dezenas=qtd_dezenas, modo="menos")

                        c_left, c_right = st.columns(2)
                        with c_left:
                            with st.container(border=True):
                                st.subheader("Mais sorteados")
                                render_chips(jogo_mais, variant="default")
                        with c_right:
                            with st.container(border=True):
                                st.subheader("Menos sorteados")
                                render_chips(jogo_menos, variant="muted")

                except Exception as e:
                    st.error(f"Erro na análise: {e}")
