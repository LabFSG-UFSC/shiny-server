import math
import pandas as pd

# =========================================================
# CONFIGURAÇÕES BÁSICAS
# =========================================================
ARQUIVO_EXCEL = "Planilhao_Excel_COND_VERT_CORRIGIDO.xlsx"
ABA_ENTRADA = 0
ARQUIVO_SAIDA = "Calculo_com_Medianas_VVT_70_IPTU.xlsx"

# =========================================================
# TABELAS – TERRENO (PVG)
# =========================================================
MAP_FSQ = {1: 1.00, 2: 1.03, 3: 1.09, 4: 0.90, 5: 0.80}
MAP_FTOP = {1: 1.00, 2: 0.95, 3: 0.90, 4: 0.90}
MAP_FPD = {1: 0.90, 2: 1.00, 3: 0.85}
MAP_FPAV = {1: 1.00, 2: 1.00, 4: 1.00, 5: 0.85}
MAP_FMP_STR = {"SIM": 1.00, "NAO": 0.93, "NÃO": 0.93}
MAP_FTO = {1: 1.00, 2: 1.40}

# =========================================================
# CONSTRUÇÃO – CONSTANTE (Cr)
# =========================================================
CR_CONSTRUCAO = 1218.52

# =========================================================
# TABELA PVG IX – FPC (PADRÃO CONSTRUTIVO) – COMPLETA (Lei)
# =========================================================
MAP_FPC = {
    # Casa
    "1A": 1.3596, "1B": 0.8969, "1C": 0.6766, "1D": 0.3854,
    # Barraco
    "2A": 0.4090, "2B": 0.3135, "2C": 0.1910, "2D": 0.1840,
    # (Algumas versões da tabela trazem 3A..3D também; mantido por segurança)
    "3A": 0.4090, "3B": 0.3135, "3C": 0.1910, "3D": 0.1840,
    # Apartamento
    "4A": 1.3596, "4B": 0.8969, "4C": 0.6766, "4D": 0.3854,
    # Sala
    "5A": 1.3596, "5B": 0.8969, "5C": 0.6766, "5D": 0.3854,
    # Loja
    "6A": 1.3596, "6B": 0.8969, "6C": 0.6766, "6D": 0.3854,
    # Galpão
    "7A": 0.8179, "7B": 0.6270, "7C": 0.4217, "7D": 0.2340,
    # Telheiro
    "8A": 0.7160, "8B": 0.5679, "8C": 0.3870, "8D": 0.2017,
    # Fábrica
    "9A": 0.9160, "9B": 0.8179, "9C": 0.6270, "9D": 0.3817,
    # Especial
    "10A": 0.9160, "10B": 0.8179, "10C": 0.6270, "10D": 0.3817,
    # Outros
    "11A": 0.9160, "11B": 0.8179, "11C": 0.6270, "11D": 0.3817,
}

# =========================================================
# TABELA PVG X – FEC (ELEMENTO CONSTRUTIVO) – PAREDES
# =========================================================
MAP_FEC = {1: 0.90, 2: 0.60, 3: 1.00, 4: 0.80, 5: 0.95, 6: 1.00}

# =========================================================
# TABELA PVG XI – FCV (UNIDADES EM CONDOMÍNIOS VERTICAIS)
# (aplica SOMENTE quando COND_VERT == 1)
# =========================================================
MAP_FCV = {
    # 1x Apartamento
    "1A": 2.5, "1B": 1.8, "1C": 1.5, "1D": 1.2,
    # 2x Loja
    "2A": 2.2, "2B": 1.6, "2C": 1.3, "2D": 1.1,
    # 3x Sala
    "3A": 2.2, "3B": 1.6, "3C": 1.3, "3D": 1.1,
    # 4x Garagem (se existir no cadastro)
    "4A": 1.5, "4B": 1.3, "4C": 1.1, "4D": 1.0,
}

# =========================================================
# FUNÇÕES AUXILIARES – VVT (SEU SCRIPT VALIDADO)
# =========================================================
def _to_float_or_none(x):
    try:
        if pd.isna(x):
            return None
        return float(str(x).replace(",", ".").strip())
    except:
        return None

def fator_testada_ft(testada):
    t = _to_float_or_none(testada)
    if t is None or t <= 0:
        return 1.0
    if t <= 100:
        return 0.89 + 0.045 * math.log(t)
    return 1.10

def fator_area_fa(area):
    a = _to_float_or_none(area)
    if a is None or a <= 0:
        return 1.0
    if a <= 1800:
        return 1.434 - 0.076 * math.log(a)
    if a <= 100000:
        return 2.046 - 0.157 * math.log(a)
    return 0.238

def map_factor(value, mapping, default=1.0):
    v = _to_float_or_none(value)
    if v is not None:
        if int(v) == v and int(v) in mapping:
            return mapping[int(v)]
        return v
    s = str(value).strip().upper() if value is not None else ""
    return mapping.get(s, default)

def fator_iluminacao_fmp(x):
    v = _to_float_or_none(x)
    if v is not None:
        if abs(v - 1.00) < 1e-9 or abs(v - 0.93) < 1e-9:
            return v
        if v == 1:
            return 1.00
        if v == 0:
            return 0.93
        return v
    s = str(x).strip().upper() if x is not None else ""
    return MAP_FMP_STR.get(s, 1.0)

def fator_fec_paredes(v):
    v = _to_float_or_none(v)
    if v is not None and int(v) == v:
        return MAP_FEC.get(int(v), 1.0)
    return 1.0

# =========================================================
# FPC – derivado de M_TIPO e M_PADRAO (Lei)
# =========================================================
TIPO_TO_GRUPO_FPC = {
    1: 1,   # 001-Casa -> 1x
    2: 2,   # 002-Barraco -> 2x
    3: 4,   # 003-Apartamento -> 4x
    4: 5,   # 004-Sala -> 5x
    5: 6,   # 005-Loja -> 6x
    6: 7,   # 006-Galpao -> 7x
    7: 8,   # 007-Telheiro -> 8x
    8: 9,   # 008-Fabrica -> 9x
    9: 10,  # 009-Especial -> 10x
    10: 11, # 010-Outros -> 11x
}

PADRAO_TO_LETRA = {
    "001-LUXO": "A",
    "002-NORMAL": "B",
    "003-BAIXO": "C",
    "004-POPULAR": "D",
}

def calcula_fpc(m_tipo, m_padrao):
    # m_tipo exemplo: "003-Apartamento"
    # m_padrao exemplo: "002-Normal"
    try:
        tipo_str = str(m_tipo).strip()
        tipo_cod = int(tipo_str.split("-")[0])
    except:
        return None

    grupo = TIPO_TO_GRUPO_FPC.get(tipo_cod)
    if grupo is None:
        return None

    padrao_key = str(m_padrao).strip().upper()
    letra = PADRAO_TO_LETRA.get(padrao_key)
    if letra is None:
        # fallback: tenta ler código numérico
        try:
            padrao_cod = int(padrao_key.split("-")[0])
            letra = {1: "A", 2: "B", 3: "C", 4: "D"}.get(padrao_cod)
        except:
            return None

    return f"{grupo}{letra}"

# =========================================================
# FCV – só para condomínio vertical (COND_VERT == 1)
# =========================================================
def converte_fpc_para_fcv(fpc):
    """
    PVG XI usa tipologias:
      1x Apartamento, 2x Loja, 3x Sala, 4x Garagem
    O FPC é PVG IX (ex.: 4B Apartamento Normal, 6B Loja Normal, 5B Sala Normal)
    """
    if not fpc or len(str(fpc)) < 2:
        return None

    fpc = str(fpc).strip().upper()
    letra = fpc[-1]
    grupo = fpc[:-1]  # "4", "6", "5", "11", etc.

    # Só convertemos os tipos que existem na tabela PVG XI
    if grupo == "4":   # Apartamento
        return f"1{letra}"
    if grupo == "6":   # Loja
        return f"2{letra}"
    if grupo == "5":   # Sala
        return f"3{letra}"
    # Garagem não está vindo pelo seu M_TIPO (geralmente), mas deixamos se necessário
    return None

def calcula_fcv(cond_vert, fpc_id):
    cv = _to_float_or_none(cond_vert)

    # FCV só se aplica quando COND_VERT == 1 (condomínio vertical)
    if cv != 1:
        return 1.0

    fcv_id = converte_fpc_para_fcv(fpc_id)
    if fcv_id and fcv_id in MAP_FCV:
        return MAP_FCV[fcv_id]

    return 1.0


# =========================================================
# ALÍQUOTAS IPTU
# =========================================================
ALIQUOTAS_PREDIAL = [
    (0, 100000, 0.0045),
    (100000, 200000, 0.0050),
    (200000, 350000, 0.0055),
    (350000, 550000, 0.0060),
    (550000, 1000000, 0.0065),
    (1000000, 1500000, 0.0080),
    (1500000, float("inf"), 0.0090),
]

ALIQUOTAS_TERRITORIAL = [
    (0, 80000, 0.0065),
    (80000, 160000, 0.0070),
    (160000, 500000, 0.0075),
    (500000, 1000000, 0.0090),
    (1000000, 2000000, 0.0100),
    (2000000, float("inf"), 0.0110),
]

def iptu_progressivo(vvi, tabela):
    imposto = 0.0
    for vmin, vmax, aliq in tabela:
        if vvi > vmin:
            imposto += (min(vvi, vmax) - vmin) * aliq
        else:
            break
    return imposto

# =========================================================
# MAIN
# =========================================================
def main():
    df = pd.read_excel(ARQUIVO_EXCEL, sheet_name=ABA_ENTRADA)

    # -------------------------
    # VVT – EXATAMENTE O SEU (VALIDADO)
    # -------------------------
    At = df["M_AREA_LOT"]
    Vmq = df["PVG_VU_PVG"]

    Ft = df["M_TESTADAP"].apply(fator_testada_ft)
    Fa = df["M_AREA_LOT"].apply(fator_area_fa)

    Fsq  = df["SQ"].apply(lambda x: map_factor(x, MAP_FSQ, 1.0))
    Ftop = df["M_TOPOGRAF"].apply(lambda x: map_factor(x, MAP_FTOP, 1.0))
    Fpd  = df["M_PEDOLOGI"].apply(lambda x: map_factor(x, MAP_FPD, 1.0))
    Fpav = df["PAVIM"].apply(lambda x: map_factor(x, MAP_FPAV, 1.0))

    Fmp = df["PVG_Ilumin"].apply(fator_iluminacao_fmp)
    Fto = df["TIPO_OCUOP"].apply(lambda x: map_factor(x, MAP_FTO, 1.0))

    # =========================
    # >>> ÚNICA ADIÇÃO: salvar os fatores em colunas (sem mudar cálculo)
    # =========================
    df["Ft"] = Ft
    df["Fa"] = Fa
    df["Fsq"] = Fsq
    df["Ftop"] = Ftop
    df["Fpd"] = Fpd
    df["Fpav"] = Fpav
    df["Fmp"] = Fmp
    df["Fto"] = Fto
    # =========================

    df["VVT_Calc"] = At * (Vmq) * Ft * Fa * Fsq * Ftop * Fpd * Fpav * Fmp * Fto

    # -------------------------
    # TIPO DO IMÓVEL
    # -------------------------
    df["TIPO_IMOVEL"] = df["M_OCUPACAO"].apply(
        lambda x: "PREDIAL" if str(x).startswith("007") else "TERRITORIAL"
    )

    # -------------------------
    # Vc – CONSTRUÇÃO (CORRIGIDO)
    # -------------------------
    # FPC vem da lei: M_TIPO + M_PADRAO
    df["FPC_ID"] = df.apply(lambda r: calcula_fpc(r.get("M_TIPO"), r.get("M_PADRAO")), axis=1)
    df["FPC"] = df["FPC_ID"].map(MAP_FPC).fillna(1.0)

    # FEC pelas paredes (tabela PVG X)
    df["FEC"] = df["M_PAREDES"].apply(fator_fec_paredes)

    # FCV somente se COND_VERT == 1 (tabela PVG XI)
    df["FCV"] = df.apply(lambda r: calcula_fcv(r.get("COND_VERT", 0), r.get("FPC_ID")), axis=1)

    # Vc = Ac * Cr * FPC * FEC * FCV
    df["Vc_Calc"] = (
        df["M_AREA_CON"].fillna(0) *
        CR_CONSTRUCAO *
        df["FPC"] *
        df["FEC"] *
        df["FCV"]
    )

    # Territorial não tem construção
    df.loc[df["TIPO_IMOVEL"] == "TERRITORIAL", "Vc_Calc"] = 0.0

    # -------------------------
    # VVI – REGRA FINAL
    # -------------------------
    def calcula_vvi(row):
        if row["TIPO_IMOVEL"] == "TERRITORIAL":
            return row["VVT_Calc"] * 0.70
        fi = _to_float_or_none(row.get("FI_LOTE"))
        if fi is None or fi <= 0:
            fi = 1.0
        return row["VVT_Calc"] * fi * 0.70 + row["Vc_Calc"] * 1

    df["Vvi_Calc"] = df.apply(calcula_vvi, axis=1)

    # -------------------------
    # IPTU
    # -------------------------
    df["IPTU_Calc"] = df.apply(
        lambda r: iptu_progressivo(
            r["Vvi_Calc"],
            ALIQUOTAS_PREDIAL if r["TIPO_IMOVEL"] == "PREDIAL"
            else ALIQUOTAS_TERRITORIAL
        ),
        axis=1
    )

    df.to_excel(ARQUIVO_SAIDA, index=False)
    print(f"OK! Arquivo gerado: {ARQUIVO_SAIDA}")

if __name__ == "__main__":
    main()
