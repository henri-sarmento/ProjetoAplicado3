import docx
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import qn, nsdecls
import re
import os
import shutil
from xml.sax.saxutils import escape

# ==============================================================================
# MOTOR DE EQUAÇÕES NATIVAS DO WORD (OFFICE MATH MARKUP LANGUAGE — OMML)
# ==============================================================================
M_NS = 'xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math" xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"'

def m_ctrl():
    return '<m:ctrlPr><w:rPr><w:rFonts w:ascii="Cambria Math" w:hAnsi="Cambria Math"/></w:rPr></m:ctrlPr>'

def m_r(text, style="i", scr=None, bold=False):
    """Cria um elemento <m:r> com formatação matemática OMML."""
    t_esc = escape(str(text))
    rpr_m = ""
    if style == "nor":
        rpr_m += "<m:nor/>"
    elif style in ("p", "bi", "b"):
        if scr:
            rpr_m += f'<m:scr m:val="{scr}"/>'
        rpr_m += f'<m:sty m:val="{style}"/>'
    else:
        if scr:
            rpr_m += f'<m:scr m:val="{scr}"/>'
    m_rpr_block = f"<m:rPr>{rpr_m}</m:rPr>" if rpr_m else ""
    w_bold = "<w:b/><w:bCs/>" if bold else ""
    return (
        f'<m:r>{m_rpr_block}'
        f'<w:rPr><w:rFonts w:ascii="Cambria Math" w:hAnsi="Cambria Math"/>{w_bold}</w:rPr>'
        f'<m:t xml:space="preserve">{t_esc}</m:t></m:r>'
    )

def m_sub(base_xml, sub_xml):
    return f'<m:sSub><m:sSubPr>{m_ctrl()}</m:sSubPr><m:e>{base_xml}</m:e><m:sub>{sub_xml}</m:sub></m:sSub>'

def m_sup(base_xml, sup_xml):
    return f'<m:sSup><m:sSupPr>{m_ctrl()}</m:sSupPr><m:e>{base_xml}</m:e><m:sup>{sup_xml}</m:sup></m:sSup>'

def m_subsup(base_xml, sub_xml, sup_xml):
    return f'<m:sSubSup><m:sSubSupPr>{m_ctrl()}</m:sSubSupPr><m:e>{base_xml}</m:e><m:sub>{sub_xml}</m:sub><m:sup>{sup_xml}</m:sup></m:sSubSup>'

def m_frac(num_xml, den_xml):
    return f'<m:f><m:fPr>{m_ctrl()}</m:fPr><m:num>{num_xml}</m:num><m:den>{den_xml}</m:den></m:f>'

def m_sqrt(expr_xml):
    return f'<m:rad><m:radPr><m:degHide m:val="1"/>{m_ctrl()}</m:radPr><m:deg/><m:e>{expr_xml}</m:e></m:rad>'

def m_sum(sub_xml="", sup_xml="", expr_xml=""):
    sup_hide = '<m:supHide m:val="1"/>' if not sup_xml else ''
    sub_hide = '<m:subHide m:val="1"/>' if not sub_xml else ''
    return (
        f'<m:nary><m:naryPr><m:chr m:val="∑"/><m:limLoc m:val="undOvr"/><m:grow m:val="1"/>'
        f'{sub_hide}{sup_hide}{m_ctrl()}</m:naryPr>'
        f'<m:sub>{sub_xml}</m:sub><m:sup>{sup_xml}</m:sup><m:e>{expr_xml}</m:e></m:nary>'
    )

def m_hat(base_xml):
    return f'<m:acc><m:accPr><m:chr m:val="&#x0302;"/>{m_ctrl()}</m:accPr><m:e>{base_xml}</m:e></m:acc>'

def m_delim(elements_xml_list, beg="(", end=")", sep=","):
    b_esc = escape(beg)
    e_esc = escape(end)
    s_esc = escape(sep)
    e_blocks = "".join(f"<m:e>{el}</m:e>" for el in elements_xml_list)
    return (
        f'<m:d><m:dPr><m:begChr m:val="{b_esc}"/><m:sepChr m:val="{s_esc}"/><m:endChr m:val="{e_esc}"/>'
        f'{m_ctrl()}</m:dPr>{e_blocks}</m:d>'
    )

def m_cases_piecewise():
    """Estrutura de chaves por partes idêntica à Equação (2) da Etapa 2."""
    row1 = (
        f'<m:mr><m:e>{m_r("1,")}</m:e>'
        f'<m:e>{m_r("se ", style="nor")}{m_sub(m_r("r"), m_r("ui"))}{m_r(" > 0")}</m:e></m:mr>'
    )
    row2 = (
        f'<m:mr><m:e>{m_r("0,")}</m:e>'
        f'<m:e>{m_r("se ", style="nor")}{m_sub(m_r("r"), m_r("ui"))}{m_r(" = 0")}</m:e></m:mr>'
    )
    matrix_xml = (
        f'<m:m><m:mPr><m:plcHide m:val="1"/>'
        f'<m:mcs><m:mc><m:mcPr><m:count m:val="2"/><m:mcJc m:val="left"/></m:mcPr></m:mc></m:mcs>'
        f'{m_ctrl()}</m:mPr>{row1}{row2}</m:m>'
    )
    return f'<m:d><m:dPr><m:begChr m:val="{{"/><m:endChr m:val=""/>{m_ctrl()}</m:dPr><m:e>{matrix_xml}</m:e></m:d>'

# Dicionário de expressões matemáticas inline ($...$) -> OMML (<m:oMath>...</m:oMath>)
INLINE_MATH_OMML = {
    "K": m_r("K"),
    "u": m_r("u"),
    "i": m_r("i"),
    "j": m_r("j"),
    "d": m_r("d"),
    "n": m_r("n"),
    "k": m_r("k"),
    "f": m_r("f"),
    "L": m_r("L"),
    "A": m_r("A"),
    "B": m_r("B"),
    "M": m_r("M"),
    "N": m_r("N"),
    "M × N": m_r("M × N"),
    "α": m_r("α"),
    "β": m_r("β"),
    "λ": m_r("λ"),
    "N_F": m_sub(m_r("N"), m_r("F")),
    "N_R": m_sub(m_r("N"), m_r("R")),
    "L_2": m_sub(m_r("L"), m_r("2")),
    "T_u": m_sub(m_r("T"), m_r("u")),
    "O_u": m_sub(m_r("O"), m_r("u")),
    "c_{ui}": m_sub(m_r("c"), m_r("ui")),
    "p_{ui}": m_sub(m_r("p"), m_r("ui")),
    "r_{ui}": m_sub(m_r("r"), m_r("ui")),
    "rel_i": m_sub(m_r("rel", style="nor"), m_r("i")),
    "rel_i ∈ {0, 1}": m_sub(m_r("rel", style="nor"), m_r("i")) + m_r(" ∈ ") + m_delim([m_r("0"), m_r("1")], beg="{", end="}"),
    "C_u": m_sub(m_r("C", scr="script"), m_r("u")),
    "U_cal": m_r("U", scr="script"),
    "I_cal": m_r("I", scr="script"),
    "R_vec": m_r("R", style="bi"),
    "u_vec": m_r("u", style="bi"),
    "i_vec": m_r("i", style="bi"),
    "u_in_Rd": m_r("u", style="bi") + m_r(" ∈ ") + m_sup(m_r("R", scr="double-struck"), m_r("d")),
    "i_in_Rd": m_r("i", style="bi") + m_r(" ∈ ") + m_sup(m_r("R", scr="double-struck"), m_r("d")),
    "Simil_in_01": m_r("Simil", style="nor") + m_delim([m_r("u", style="bi"), m_r("i", style="bi")]) + m_r(" ∈ ") + m_delim([m_r("0"), m_r("1")], beg="[", end="]"),
    "r_ui=0": m_sub(m_r("r"), m_r("ui")) + m_r(" = 0"),
    "r_ui>0": m_sub(m_r("r"), m_r("ui")) + m_r(" > 0"),
    "r_ui>=0": m_sub(m_r("r"), m_r("ui")) + m_r(" ≥ 0"),
    "p_ui_in_01": m_sub(m_r("p"), m_r("ui")) + m_r(" ∈ ") + m_delim([m_r("0"), m_r("1")], beg="{", end="}"),
    "c_ui_eq": m_sub(m_r("c"), m_r("ui")) + m_r(" = 1 + α") + m_sub(m_r("r"), m_r("ui")),
    "xy_in_Rf": m_sub(m_r("x", style="bi"), m_r("u")) + m_r(", ") + m_sub(m_r("y", style="bi"), m_r("i")) + m_r(" ∈ ") + m_sup(m_r("R", scr="double-struck"), m_r("f")),
    "xy_pair": m_sub(m_r("x", style="bi"), m_r("u")) + m_r(", ") + m_sub(m_r("y", style="bi"), m_r("i")),
    "f_ll_min": m_r("f ≪ ") + m_r("min", style="p") + m_delim([m_r("M"), m_r("N")]),
    "S(u,i)": m_r("S") + m_delim([m_r("u"), m_r("i")]),
    "i_in_Cu": m_r("i ∈ ") + m_sub(m_r("C", scr="script"), m_r("u")),
    "beta_in_01": m_r("β ∈ ") + m_delim([m_r("0"), m_r("1")], beg="[", end="]"),
    "beta_in_00_10": m_r("β ∈ ") + m_delim([m_r("0,0"), m_r("1,0")], beg="[", end="]", sep="; "),
    "int_01": m_delim([m_r("0"), m_r("1")], beg="[", end="]"),
    "Precision@K": m_r("Precision", style="nor") + m_r("@K"),
    "Precision@5": m_r("Precision", style="nor") + m_r("@5"),
    "Recall@K": m_r("Recall", style="nor") + m_r("@K"),
    "Recall@10": m_r("Recall", style="nor") + m_r("@10"),
    "Recall@10=0.9986": m_r("Recall", style="nor") + m_r("@10 = 0,9986"),
    "DCG@K": m_r("DCG", style="nor") + m_r("@K"),
    "IDCG@K": m_r("IDCG", style="nor") + m_r("@K"),
    "NDCG@K": m_r("NDCG", style="nor") + m_r("@K"),
    "NDCG@10": m_r("NDCG", style="nor") + m_r("@10"),
    "NDCG@10=0.9185": m_r("NDCG", style="nor") + m_r("@10 = 0,9185"),
    "ILD": m_r("ILD", style="nor"),
    "ILD@10": m_r("ILD", style="nor") + m_r("@10"),
    "ILD@10=0.7615": m_r("ILD", style="nor") + m_r("@10 = 0,7615"),
    "|L|": m_r("∣L∣"),
    "d(i,j)": m_r("d") + m_delim([m_r("i"), m_r("j")]),
    "d(i,j)_in_01": m_r("d") + m_delim([m_r("i"), m_r("j")]) + m_r(" ∈ ") + m_delim([m_r("0"), m_r("1")], beg="[", end="]"),
    "R_in_RUI": m_r("R", style="bi") + m_r(" ∈ ") + m_sup(m_r("R", scr="double-struck"), m_r("∣") + m_r("U", scr="script") + m_r("∣×∣") + m_r("I", scr="script") + m_r("∣")),
    "LK_ranking": m_sub(m_r("L"), m_r("K")) + m_delim([m_r("u")]) + m_r(" = ") + m_delim([m_sub(m_r("i"), m_r("(1)")), m_sub(m_r("i"), m_r("(2)")), m_r("…"), m_sub(m_r("i"), m_r("(K)"))], beg="⟨", end="⟩"),
    "|U|=2400": m_r("∣") + m_r("U", scr="script") + m_r("∣ = 2.400"),
    "|U|=360": m_r("∣") + m_r("U", scr="script") + m_r("∣ = 360"),
    "|I|=1800": m_r("∣") + m_r("I", scr="script") + m_r("∣ = 1.800"),
    "Cu_sub_I": m_sub(m_r("C", scr="script"), m_r("u")) + m_r(" ⊂ ") + m_r("I", scr="script"),
    "|Cu|_ll_|I|": m_r("∣") + m_sub(m_r("C", scr="script"), m_r("u")) + m_r("∣ ≪ ∣") + m_r("I", scr="script") + m_r("∣"),
    "phat_CF_in_01": m_subsup(m_hat(m_r("p")), m_r("ui"), m_r("CF", style="nor")) + m_r(" ∈ ") + m_delim([m_r("0"), m_r("1")], beg="[", end="]"),
    "K_in_5_10_20": m_r("K ∈ ") + m_delim([m_r("5"), m_r("10"), m_r("20")], beg="{", end="}"),
    "hyper_tuple": m_r("α, f, λ, β"),
    "k=4": m_r("k = 4"),
    "alpha_set": m_r("α ∈ ") + m_delim([m_r("10"), m_r("25"), m_r("40"), m_r("80")], beg="{", end="}"),
    "alpha=40": m_r("α = 40,0"),
    "f_set": m_r("f ∈ ") + m_delim([m_r("16"), m_r("32"), m_r("64")], beg="{", end="}"),
    "f=64": m_r("f = 64"),
    "lambda_set": m_r("λ ∈ ") + m_delim([m_r("0,1"), m_r("1,0"), m_r("10,0"), m_r("20,0")], beg="{", end="}", sep="; "),
    "lambda=10": m_r("λ = 10,0"),
    "beta_to_1": m_r("β → 1"),
    "beta_to_0": m_r("β → 0"),
    "beta=0.75": m_r("β = 0,75"),
    "H2O": m_sub(m_r("H", style="nor"), m_r("2")) + m_r("O", style="nor"),
}

# ==============================================================================
# DEFINIÇÃO DAS 21 EQUAÇÕES DE DESTAQUE EM OMML NATIVO (<m:oMathPara>)
# ==============================================================================
def get_display_equation_omml(eq_id):
    if eq_id == "1":
        # Equação (1) - Similaridade do Cosseno completa (idêntica à Etapa 2)
        lhs = m_r("Simil", style="nor") + m_delim([m_r("u", style="bi"), m_r("i", style="bi")]) + m_r(" = ")
        frac1 = m_frac(
            m_r("u", style="bi") + m_r(" ⋅ ") + m_r("i", style="bi"),
            m_r("∥") + m_r("u", style="bi") + m_r("∥ ∥") + m_r("i", style="bi") + m_r("∥")
        )
        sum_num = m_sum(m_r("k=1"), m_r("d"), m_sub(m_r("u"), m_r("k")) + m_r(" ⋅ ") + m_sub(m_r("i"), m_r("k")))
        rad_u = m_sqrt(m_sum(m_r("k=1"), m_r("d"), m_subsup(m_r("u"), m_r("k"), m_r("2"))))
        rad_i = m_sqrt(m_sum(m_r("k=1"), m_r("d"), m_subsup(m_r("i"), m_r("k"), m_r("2"))))
        frac2 = m_frac(sum_num, rad_u + rad_i)
        return lhs + frac1 + m_r(" = ") + frac2

    elif eq_id in ("2", "12"):
        # Equação (2) e (12) - Preferência Binária com chave por partes
        return m_sub(m_r("p"), m_r("ui")) + m_r(" = ") + m_cases_piecewise()

    elif eq_id in ("3", "13"):
        # Equação (3) e (13) - Confiança Ponderada
        return m_sub(m_r("c"), m_r("ui")) + m_r(" = 1 + α ⋅ ") + m_sub(m_r("r"), m_r("ui"))

    elif eq_id == "4":
        # Equação (4) - Predição Latente
        return m_sub(m_hat(m_r("p")), m_r("ui")) + m_r(" = ") + m_subsup(m_r("x", style="bi"), m_r("u"), m_r("T")) + m_sub(m_r("y", style="bi"), m_r("i"))

    elif eq_id in ("5", "15"):
        # Equação (5) e (15) - Função de perda ALS ponderada pela confiança
        lhs = m_sub(m_r("L", scr="script"), m_r("ALS", style="nor")) + m_r(" = ")
        term_err = m_sup(
            m_delim([
                m_sub(m_r("p"), m_r("ui")) + m_r(" − ") +
                m_subsup(m_r("x", style="bi"), m_r("u"), m_r("T")) + m_sub(m_r("y", style="bi"), m_r("i"))
            ]),
            m_r("2")
        )
        sum1 = m_sum(m_r("u,i"), "", m_sub(m_r("c"), m_r("ui")) + term_err)
        norm_x = m_sum(m_r("u"), "", m_r("∥") + m_sub(m_r("x", style="bi"), m_r("u")) + m_sup(m_r("∥"), m_r("2")))
        norm_y = m_sum(m_r("i"), "", m_r("∥") + m_sub(m_r("y", style="bi"), m_r("i")) + m_sup(m_r("∥"), m_r("2")))
        reg_term = m_r(" + λ") + m_delim([norm_x + m_r(" + ") + norm_y])
        return lhs + sum1 + reg_term

    elif eq_id in ("6", "16"):
        # Equação (6) e (16) - Score Híbrido em Cascata
        lhs = m_r("S") + m_delim([m_r("u"), m_r("i")]) + m_r(" = β ⋅ ")
        cbf_part = m_sub(m_r("Simil", style="nor"), m_r("CBF", style="nor")) + m_delim([m_r("u", style="bi"), m_r("i", style="bi")])
        cf_part = m_r(" + ") + m_delim([m_r("1 − β")]) + m_r(" ⋅ ") + m_subsup(m_hat(m_r("p")), m_r("ui"), m_r("CF", style="nor"))
        return lhs + cbf_part + cf_part

    elif eq_id == "7":
        # Equação (7) - Precision@K
        num = m_r("∣") + m_r("Recomendações", style="nor") + m_r("@K ∩ ") + m_r("Relevantes", style="nor") + m_r("∣")
        return m_r("Precision", style="nor") + m_r("@K = ") + m_frac(num, m_r("K"))

    elif eq_id == "8":
        # Equação (8) - Recall@K
        num = m_r("∣") + m_r("Recomendações", style="nor") + m_r("@K ∩ ") + m_r("Relevantes", style="nor") + m_r("∣")
        den = m_r("∣") + m_r("Relevantes", style="nor") + m_r("∣")
        return m_r("Recall", style="nor") + m_r("@K = ") + m_frac(num, den)

    elif eq_id == "9":
        # Equação (9) - DCG@K
        num = m_sup(m_r("2"), m_sub(m_r("rel", style="nor"), m_r("i"))) + m_r(" − 1")
        den = m_sub(m_r("log", style="p"), m_r("2")) + m_delim([m_r("i + 1")])
        return m_r("DCG", style="nor") + m_r("@K = ") + m_sum(m_r("i=1"), m_r("K"), m_frac(num, den))

    elif eq_id == "10":
        # Equação (10) - NDCG@K
        frac = m_frac(m_r("DCG", style="nor") + m_r("@K"), m_r("IDCG", style="nor") + m_r("@K"))
        return m_r("NDCG", style="nor") + m_r("@K = ") + frac + m_r(" ∈ ") + m_delim([m_r("0"), m_r("1")], beg="[", end="]")

    elif eq_id in ("11", "20"):
        # Equação (11) e (20) - ILD(L)
        lhs = m_r("ILD", style="nor") + m_delim([m_r("L")]) + m_r(" = ")
        frac = m_frac(m_r("2"), m_r("∣L∣") + m_delim([m_r("∣L∣ − 1")]))
        inner_sum = m_sum(m_r("j∈L, j>i"), "", m_r("d") + m_delim([m_r("i"), m_r("j")]))
        outer_sum = m_sum(m_r("i∈L"), "", inner_sum)
        return lhs + frac + outer_sum

    elif eq_id == "14":
        # Equação (14) - Similaridade CBF na Fase 1
        lhs = m_sub(m_r("Simil", style="nor"), m_r("CBF", style="nor")) + m_delim([m_r("u", style="bi"), m_r("i", style="bi")]) + m_r(" = ")
        frac = m_frac(
            m_r("u", style="bi") + m_r(" ⋅ ") + m_r("i", style="bi"),
            m_r("∥") + m_r("u", style="bi") + m_r("∥ ∥") + m_r("i", style="bi") + m_r("∥")
        )
        return lhs + frac

    elif eq_id == "17":
        # Equação (17) - Precision@K no Teste Cego
        num = m_r("∣") + m_r("Recomendações", style="nor") + m_r("@K ∩ ") + m_r("GroundTruth", style="nor") + m_r("∣")
        return m_r("Precision", style="nor") + m_r("@K = ") + m_frac(num, m_r("K"))

    elif eq_id == "18":
        # Equação (18) - Recall@K no Teste Cego
        num = m_r("∣") + m_r("Recomendações", style="nor") + m_r("@K ∩ ") + m_r("GroundTruth", style="nor") + m_r("∣")
        den = m_r("∣") + m_r("GroundTruth", style="nor") + m_r("∣")
        return m_r("Recall", style="nor") + m_r("@K = ") + m_frac(num, den)

    elif eq_id == "19":
        # Equação (19) - NDCG@K no Teste Cego
        frac = m_frac(m_r("DCG", style="nor") + m_r("@K"), m_r("IDCG", style="nor") + m_r("@K"))
        return m_r("NDCG", style="nor") + m_r("@K = ") + frac

    elif eq_id == "21":
        # Equação (21) - Função de Dissimilaridade Taxonômica e Funcional d(i, j)
        lhs = m_r("d") + m_delim([m_r("i"), m_r("j")]) + m_r(" = 0,5 ⋅ ")
        ind1 = m_r("I", scr="double-struck") + m_delim([m_sub(m_r("Família", style="nor"), m_r("i")) + m_r(" ≠ ") + m_sub(m_r("Família", style="nor"), m_r("j"))])
        ind2 = m_r(" + 0,5 ⋅ ") + m_r("I", scr="double-struck") + m_delim([m_sub(m_r("Sucessão", style="nor"), m_r("i")) + m_r(" ≠ ") + m_sub(m_r("Sucessão", style="nor"), m_r("j"))])
        return lhs + ind1 + ind2

    raise ValueError(f"Equação desconhecida: {eq_id}")


def add_page_number_field(run):
    fldSimple = OxmlElement('w:fldSimple')
    fldSimple.set(qn('w:instr'), 'PAGE')
    run._r.append(fldSimple)


def parse_runs(text):
    """
    Divide o texto com markdown (**negrito** e *itálico*) em tuplas (texto, bold, italic).
    """
    tokens = re.split(r'(\*\*.*?\*\*|\*.*?\*)', text)
    result = []
    for t in tokens:
        if not t:
            continue
        if t.startswith('**') and t.endswith('**'):
            result.append((t[2:-2], True, False))
        elif t.startswith('*') and t.endswith('*'):
            result.append((t[1:-1], False, True))
        else:
            result.append((t, False, False))
    return result


def append_text_and_math_to_paragraph(p, text, font_size=12, base_bold=False):
    """
    Analisa tokens [[MATH:key]] para inserir objetos <m:oMath> nativos do Word
    e processa o restante do texto com suporte a **negrito** e *itálico*.
    """
    parts = re.split(r'(\[\[MATH:.*?\]\])', text)
    for part in parts:
        if not part:
            continue
        if part.startswith('[[MATH:') and part.endswith(']]'):
            key = part[7:-2]
            omml_inner = INLINE_MATH_OMML[key]
            omath_el = parse_xml(f'<m:oMath {M_NS}>{omml_inner}</m:oMath>')
            p._p.append(omath_el)
        else:
            runs_info = parse_runs(part)
            for txt, b, it in runs_info:
                run = p.add_run(txt)
                run.bold = b or base_bold
                run.italic = it
                run.font.name = 'Arial'
                run.font.size = Pt(font_size)
                run.font.color.rgb = RGBColor(0, 0, 0)


def style_table_abnt(table, col_widths, headers, data):
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    tblPr = table._tbl.tblPr
    borders = parse_xml(
        f'<w:tblBorders {nsdecls("w")}>\n'
        f'  <w:top w:val="single" w:sz="8" w:space="0" w:color="000000"/>\n'
        f'  <w:bottom w:val="single" w:sz="8" w:space="0" w:color="000000"/>\n'
        f'  <w:insideH w:val="single" w:sz="4" w:space="0" w:color="CCCCCC"/>\n'
        f'  <w:insideV w:val="none"/>\n'
        f'  <w:left w:val="none"/>\n'
        f'  <w:right w:val="none"/>\n'
        f'</w:tblBorders>'
    )
    tblPr.append(borders)

    # Cabeçalho
    hdr_cells = table.rows[0].cells
    for i, h in enumerate(headers):
        hdr_cells[i].text = ""
        p = hdr_cells[i].paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(4)
        p.paragraph_format.space_after = Pt(4)
        p.paragraph_format.line_spacing = 1.0
        r = p.add_run(h)
        r.bold = True
        r.font.name = 'Arial'
        r.font.size = Pt(10)
        shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="F2F2F2"/>')
        hdr_cells[i]._tc.get_or_add_tcPr().append(shd)

    # Linhas de dados
    for row_data in data:
        row_cells = table.add_row().cells
        for col_idx, cell_value in enumerate(row_data):
            row_cells[col_idx].text = ""
            p = row_cells[col_idx].paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT if col_idx == 0 or len(str(cell_value)) > 15 else WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.space_before = Pt(3)
            p.paragraph_format.space_after = Pt(3)
            p.paragraph_format.line_spacing = 1.0
            runs_info = parse_runs(str(cell_value))
            for txt, b, it in runs_info:
                r = p.add_run(txt)
                r.bold = b
                r.italic = it
                r.font.name = 'Arial'
                r.font.size = Pt(9.5)

    for row in table.rows:
        for idx, width in enumerate(col_widths):
            row.cells[idx].width = Cm(width)


def build_etapa3_docx():
    doc = docx.Document()

    # ==========================================
    # SEÇÃO 1: ELEMENTOS PRÉ-TEXTUAIS (Capa e Sumário)
    # ==========================================
    s1 = doc.sections[0]
    s1.top_margin = Cm(3.0)
    s1.bottom_margin = Cm(2.0)
    s1.left_margin = Cm(3.0)
    s1.right_margin = Cm(2.0)
    s1.header.is_linked_to_previous = False
    s1.header.paragraphs[0].text = ""

    def add_p(text, align=WD_ALIGN_PARAGRAPH.JUSTIFY, space_after=6, space_before=0, line_spacing=1.5, first_line_indent=Cm(1.25)):
        p = doc.add_paragraph()
        p.alignment = align
        p.paragraph_format.line_spacing = line_spacing
        p.paragraph_format.space_after = Pt(space_after)
        p.paragraph_format.space_before = Pt(space_before)
        if first_line_indent and align == WD_ALIGN_PARAGRAPH.JUSTIFY:
            p.paragraph_format.first_line_indent = first_line_indent
        else:
            p.paragraph_format.first_line_indent = Cm(0)

        append_text_and_math_to_paragraph(p, text, font_size=12, base_bold=False)
        return p

    def add_h1(text):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        p.paragraph_format.space_before = Pt(18)
        p.paragraph_format.space_after = Pt(12)
        p.paragraph_format.line_spacing = 1.5
        p.paragraph_format.first_line_indent = Cm(0)
        append_text_and_math_to_paragraph(p, text, font_size=12, base_bold=True)
        return p

    def add_h2(text):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        p.paragraph_format.space_before = Pt(12)
        p.paragraph_format.space_after = Pt(6)
        p.paragraph_format.line_spacing = 1.5
        p.paragraph_format.first_line_indent = Cm(0)
        append_text_and_math_to_paragraph(p, text, font_size=12, base_bold=True)
        return p

    def add_h3(text):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        p.paragraph_format.space_before = Pt(10)
        p.paragraph_format.space_after = Pt(4)
        p.paragraph_format.line_spacing = 1.5
        p.paragraph_format.first_line_indent = Cm(0)
        append_text_and_math_to_paragraph(p, text, font_size=12, base_bold=True)
        return p

    def add_eq(eq_id):
        """
        Insere uma equação de destaque nativa do Word (<m:oMathPara>) com
        matriz de alinhamento central e numeração (eq_id) à direita,
        seguindo exatamente o padrão OMML da Etapa 2.
        """
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(6)
        p.paragraph_format.space_after = Pt(6)
        p.paragraph_format.line_spacing = 1.5
        p.paragraph_format.first_line_indent = Cm(0)

        eq_inner = get_display_equation_omml(str(eq_id))
        num_xml = m_r(f"    ({eq_id})", style="nor")
        omath_para_xml = (
            f'<m:oMathPara {M_NS}>'
            f'  <m:oMath>'
            f'    <m:m>'
            f'      <m:mPr>'
            f'        <m:plcHide m:val="1"/>'
            f'        <m:mcs><m:mc><m:mcPr><m:count m:val="4"/><m:mcJc m:val="center"/></m:mcPr></m:mc></m:mcs>'
            f'        {m_ctrl()}'
            f'      </m:mPr>'
            f'      <m:mr>'
            f'        <m:e/>'
            f'        <m:e>{eq_inner}</m:e>'
            f'        <m:e/>'
            f'        <m:e>{num_xml}</m:e>'
            f'      </m:mr>'
            f'    </m:m>'
            f'  </m:oMath>'
            f'</m:oMathPara>'
        )
        p._p.append(parse_xml(omath_para_xml))
        return p

    def add_image_figure(image_path, titulo, fonte="Fonte: Autores (2026).", width_cm=15.5):
        if not os.path.exists(image_path):
            print(f"AVISO: Imagem não encontrada: {image_path}")
            return
        pt = doc.add_paragraph()
        pt.alignment = WD_ALIGN_PARAGRAPH.CENTER
        pt.paragraph_format.space_before = Pt(12)
        pt.paragraph_format.space_after = Pt(4)
        pt.paragraph_format.first_line_indent = Cm(0)
        rt = pt.add_run(titulo)
        rt.bold = True
        rt.font.name = 'Arial'
        rt.font.size = Pt(10)

        pi = doc.add_paragraph()
        pi.alignment = WD_ALIGN_PARAGRAPH.CENTER
        pi.paragraph_format.space_before = Pt(2)
        pi.paragraph_format.space_after = Pt(2)
        pi.paragraph_format.first_line_indent = Cm(0)
        ri = pi.add_run()
        ri.add_picture(image_path, width=Cm(width_cm))

        pf = doc.add_paragraph()
        pf.alignment = WD_ALIGN_PARAGRAPH.CENTER
        pf.paragraph_format.space_before = Pt(4)
        pf.paragraph_format.space_after = Pt(12)
        pf.paragraph_format.first_line_indent = Cm(0)
        rf = pf.add_run(fonte)
        rf.font.name = 'Arial'
        rf.font.size = Pt(10)

    # ------------------------------------------
    # CAPA ABNT (Página 1)
    # ------------------------------------------
    p_inst = doc.add_paragraph()
    p_inst.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_inst.paragraph_format.space_before = Pt(0)
    p_inst.paragraph_format.space_after = Pt(90)
    p_inst.paragraph_format.line_spacing = 1.5
    r_inst = p_inst.add_run("UNIVERSIDADE PRESBITERIANA MACKENZIE\nFACULDADE DE COMPUTAÇÃO E INFORMÁTICA\nCURSO DE TECNOLOGIA EM CIÊNCIA DE DADOS E INTELIGÊNCIA ARTIFICIAL")
    r_inst.bold = True
    r_inst.font.name = 'Arial'
    r_inst.font.size = Pt(12)

    p_aut = doc.add_paragraph()
    p_aut.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_aut.paragraph_format.space_before = Pt(0)
    p_aut.paragraph_format.space_after = Pt(110)
    p_aut.paragraph_format.line_spacing = 1.5
    r_aut = p_aut.add_run("Fernanda Pauli de Oliveira – TIA: 10736757\nHenrique Sarmento – TIA: 10738262\nMilena Dias Gouveia – TIA: 10746541\nNicolly Falcão da Silva – TIA: 10746134")
    r_aut.bold = True
    r_aut.font.name = 'Arial'
    r_aut.font.size = Pt(12)

    p_tit = doc.add_paragraph()
    p_tit.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_tit.paragraph_format.space_before = Pt(30)
    p_tit.paragraph_format.space_after = Pt(120)
    p_tit.paragraph_format.line_spacing = 1.5
    r_tit = p_tit.add_run("SISTEMA DE RECOMENDAÇÃO DE ESPÉCIES NATIVAS PARA REFLORESTAMENTO E ARBORIZAÇÃO URBANA (ODS 15)")
    r_tit.bold = True
    r_tit.font.name = 'Arial'
    r_tit.font.size = Pt(12)

    p_loc = doc.add_paragraph()
    p_loc.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_loc.paragraph_format.space_before = Pt(30)
    p_loc.paragraph_format.space_after = Pt(0)
    p_loc.paragraph_format.line_spacing = 1.5
    r_loc = p_loc.add_run("São Paulo / Brasil\n2026")
    r_loc.font.name = 'Arial'
    r_loc.font.size = Pt(12)

    doc.add_page_break()

    # ------------------------------------------
    # SUMÁRIO ABNT (Página 2)
    # ------------------------------------------
    p_sum = doc.add_paragraph()
    p_sum.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_sum.paragraph_format.space_before = Pt(0)
    p_sum.paragraph_format.space_after = Pt(18)
    r_sum = p_sum.add_run("SUMÁRIO")
    r_sum.bold = True
    r_sum.font.name = 'Arial'
    r_sum.font.size = Pt(12)

    sumario_linhas = [
        ("1 INTRODUÇÃO", "3", True),
        ("  1.1 Contexto", "3", False),
        ("  1.2 Motivação e Justificativa", "3", False),
        ("  1.3 Objetivos", "4", False),
        ("    1.3.1 Objetivo Geral", "4", False),
        ("    1.3.2 Objetivos Específicos", "4", False),
        ("  1.4 Definição da Base de Dados", "5", False),
        ("    1.4.1 Forma e Período de Coleta", "5", False),
        ("    1.4.2 Limitações dos Dados", "5", False),
        ("  1.5 Visão Geral do Pipeline de Dados e Modelagem Híbrida", "6", False),
        ("  1.6 Cronograma de Execução", "6", False),
        ("  1.7 Repositório no GitHub", "7", False),
        ("2 REFERENCIAL TEÓRICO", "8", True),
        ("  2.1 Teoria do Nicho Ecológico e Restauração Florestal Tropical", "8", False),
        ("  2.2 Filtragem Baseada em Conteúdo no Espaço Vetorial", "9", False),
        ("  2.3 Filtragem Colaborativa com Feedback Implícito e Fatoração Matricial", "10", False),
        ("  2.4 Taxonomia de Sistemas de Recomendação Híbridos em Cascata", "12", False),
        ("  2.5 Bioinformática, Vieses em Dados Abertos e Saneamento Taxonômico", "14", False),
        ("  2.6 Avaliação Além da Acurácia: Métricas de Ranking e Diversificação", "15", False),
        ("3 METODOLOGIA", "17", True),
        ("  3.1 Definição do Problema e Objetivos", "18", False),
        ("  3.2 Coleta de Dados", "19", False),
        ("  3.3 Pré-processamento e Limpeza dos Dados", "20", False),
        ("  3.4 Divisão dos Dados", "22", False),
        ("  3.5 Seleção e Implementação do Algoritmo", "23", False),
        ("  3.6 Treinamento do Modelo", "25", False),
        ("  3.7 Avaliação do Desempenho", "26", False),
        ("  3.8 Otimização e Ajustes", "28", False),
        ("  3.9 Implantação e Monitoramento", "30", False),
        ("REFERÊNCIAS", "32", True)
    ]
    for tit, pag, is_bold in sumario_linhas:
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        p.paragraph_format.line_spacing = 1.0
        p.paragraph_format.space_after = Pt(3)
        p.paragraph_format.first_line_indent = Cm(0)

        r1 = p.add_run(tit)
        r1.bold = is_bold
        r1.font.name = 'Arial'
        r1.font.size = Pt(12)

        num_dots = max(3, int((74 - len(tit)) * 1.05))
        r_dots = p.add_run(f" {' .' * (num_dots // 2)} {pag}")
        r_dots.bold = is_bold
        r_dots.font.name = 'Arial'
        r_dots.font.size = Pt(12)

    # ==========================================
    # SEÇÃO 2: ELEMENTOS TEXTUAIS (A partir da Introdução)
    # ==========================================
    s2 = doc.add_section()
    s2.top_margin = Cm(3.0)
    s2.bottom_margin = Cm(2.0)
    s2.left_margin = Cm(3.0)
    s2.right_margin = Cm(2.0)
    s2.header.is_linked_to_previous = False

    hp = s2.header.paragraphs[0]
    hp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    hp.paragraph_format.space_after = Pt(0)
    hrun = hp.add_run()
    hrun.font.name = 'Arial'
    hrun.font.size = Pt(10)
    add_page_number_field(hrun)

    # ------------------------------------------
    # 1 INTRODUÇÃO
    # ------------------------------------------
    add_h1("1 INTRODUÇÃO")

    add_h2("1.1 Contexto")
    add_p("A degradação acelerada dos ecossistemas naturais e a perda contínua da cobertura vegetal nativa constituem ameaças críticas à estabilidade ecológica e climática global. Esse cenário demanda respostas sistemáticas e estruturadas, alinhando-se diretamente ao Objetivo de Desenvolvimento Sustentável 15 (ODS 15 — Vida Terrestre) estabelecido pela Organização das Nações Unidas (ONU), cuja meta preconiza proteger, recuperar e promover o uso sustentável dos ecossistemas terrestres, combatendo a desertificação, detendo a degradação da terra e mitigando a perda de biodiversidade.")
    add_p("Iniciativas práticas de reflorestamento rural e de expansão da arborização em ambientes urbanos enfrentam rotineiramente taxas expressivas de mortalidade precoce de mudas nos dois primeiros anos após o plantio. A literatura agronômica e florestal atesta que o insucesso do estabelecimento radicular decorre primordialmente da incompatibilidade entre as propriedades físico-químicas do terreno — tais como textura do solo, acidez/pH, drenagem hídrica e radiação solar média — e as tolerâncias fisiológicas intrínsecas das espécies selecionadas. Quando a escolha botânica desconsidera esses condicionantes ou negligencia as relações de facilitação ecológica e sinergia sucessional entre comunidades vegetais, a vegetação sucumbe a estresses ambientais, gerando desperdício severo de recursos socioeconômicos e comprometendo a restauração florestal.")
    add_p("Nesse panorama, a Ciência de Dados e a Inteligência Artificial oferecem ferramentas robustas para aproximar o conhecimento botânico especializado das decisões de campo. A integração de repositórios biológicos governamentais abertos associada a modelos de recomendação inteligentes permite converter dados dispersos de inventários e catálogos taxonômicos em prescrições botânicas customizadas, garantindo a seleção de espécies resilientes e promovendo a biodiversidade funcional dos plantios.")

    add_h2("1.2 Motivação e Justificativa")
    add_p("A relevância deste projeto sustenta-se em impactos ecológicos, técnicos e econômicos mensuráveis:")
    add_p("• **Maximização da Sobrevivência de Mudas:** Prescrições algorítmicas alinhadas às restrições edafoclimáticas locais reduzem os índices de mortalidade precoce e os custos operacionais recorrentes de replantio;")
    add_p("• **Eficiência na Tomada de Decisão Pública e Privada:** Viveiros florestais, secretarias municipais de meio ambiente e cooperativas agrícolas contam com suporte técnico objetivo para planejar a aquisição e o cultivo de mudas adaptadas à sua bacia hidrográfica;")
    add_p("• **Restauração de Serviços Ecossistêmicos:** O estímulo ao plantio de comunidades vegetais balanceadas e funcionalmente diversificadas favorece a infiltração de água no solo, reduz ilhas de calor urbanas, atrai avifauna e insetos polinizadores nativos, acelerando a reconstituição das cadeias tróficas originais.")
    add_p("Ao traduzir parâmetros botânicos e registros florestais dispersos em recomendações ranqueadas e explicáveis, o sistema atua como uma ponte estratégica entre as evidências científicas e os tomadores de decisão em políticas públicas e restauração ambiental privada.")

    add_h2("1.3 Objetivos")
    add_h3("1.3.1 Objetivo Geral")
    add_p("Desenvolver um sistema de recomendação híbrido de espécies arbóreas e vegetais nativas para restauração florestal e arborização urbana, integrando atributos ecológicos de adequabilidade ambiental (filtragem baseada em conteúdo) e padrões empíricos de coocorrência em unidades amostrais de campo (filtragem colaborativa com feedback implícito).")

    add_h3("1.3.2 Objetivos Específicos")
    add_p("• **Coleta e Integração de Dados:** Consolidar uma base unificada e curada a partir de três grandes repositórios biológicos de domínio público: Flora e Funga do Brasil (JBRJ), Inventário Florestal Nacional (SFB / MAPA) e Global Biodiversity Information Facility (GBIF);")
    add_p("• **Engenharia de Dados e Saneamento Taxonômico:** Implementar resolução taxonômica automatizada de sinonímias botânicas utilizando o catálogo oficial do JBRJ, mitigar viés de superamostragem geográfica via *spatial thinning* no GBIF e tratar dados ambientais ausentes por imputação filogenética;")
    add_p("• **Modelagem Híbrida em Cascata:** Desenvolver o módulo de Conteúdo (CBF via cosseno sobre nicho fundamental com poda rígida), o módulo Colaborativo (CF via ALS com feedback implícito ponderado sobre parcelas do IFN) e acoplá-los em cascata com diversificação intra-lista ([[MATH:ILD]]);")
    add_p("• **Avaliação Experimental Offline:** Validar o desempenho do recomendador em relação a linhas de base univariadas (*baselines* por conteúdo e por popularidade) empregando métricas de ordenamento Top-[[MATH:K]] ([[MATH:Precision@K]], [[MATH:Recall@K]], [[MATH:NDCG@K]]) e índices de diversidade taxonômica e funcional.")

    add_h2("1.4 Definição da Base de Dados")
    add_p("O sistema apoia-se na fusão e harmonização de três fontes de dados biológicos de domínio público:")
    add_p("1. **Flora e Funga do Brasil (Jardim Botânico do Rio de Janeiro — JBRJ):** Catálogo taxonômico oficial do país, provendo atributos morfológicos, formas de vida, substrato, biomas de ocorrência nativa, endemismo e espectro de exigência luminosa para cada espécie catalogada.")
    add_p("2. **Inventário Florestal Nacional (Serviço Florestal Brasileiro — SFB / MAPA):** Levantamentos sistemáticos de campo conduzidos em malha regular de conglomerados pelo território nacional, fornecendo contagens censitárias de indivíduos vivos por espécie em parcelas de 20 × 20 m (400 m²) acompanhadas de laudos físico-químicos de solo.")
    add_p("3. **Global Biodiversity Information Facility (GBIF):** Rede internacional de dados abertos que fornece registros de ocorrências georreferenciadas (latitude e longitude) coletados por herbários, coleções científicas e inventários botânicos.")

    add_h3("1.4.1 Forma e Período de Coleta")
    add_p("A extração de dados ocorre via download estruturado de arquivos Darwin Core Archive (DwC-A) e chamadas automatizadas a APIs RESTful públicas (`pygbif` e portais de dados abertos governamentais). A amostragem temporal concentra-se nos últimos 15 anos, garantindo a representatividade de espécies frente ao regime climático contemporâneo e às transformações recentes de uso e cobertura do solo.")

    add_h3("1.4.2 Limitações dos Dados")
    add_p("As bases públicas apresentam desafios intrínsecos: viés de amostragem geográfica decorrente da maior densidade de registros em proximidade de rodovias e universidades; instabilidade nomenclatural decorrente de revisões filogenéticas de botânica; e severa esparsidade matricial (> 98%) inerente a inventários florísticos de biomas tropicais.")

    add_h2("1.5 Visão Geral do Pipeline de Dados e Modelagem Híbrida")
    add_p("O fluxo metodológico articula-se em seis etapas interdependentes: (1) Ingestão e unificação de dados; (2) Resolução taxonômica e *spatial thinning*; (3) Engenharia de features e vetorização; (4) Fase 1 — Geração de candidatas viáveis via Conteúdo (Cosseno sobre nicho abiótico); (5) Fase 2 — Ranqueamento colaborativo via decomposição ALS com feedback implícito sobre as parcelas do IFN; e (6) Pós-processamento de diversificação intra-lista com entrega da prescrição Top-[[MATH:K]].")

    add_h2("1.6 Cronograma de Execução")
    add_p("O planejamento temporal detalhado do projeto com o desdobramento das etapas e situação de execução na Etapa 3 é apresentado no Quadro 1 (e detalhado no arquivo auxiliar `Cronograma_ODS15_Segundo_Semestre_2026.xlsx`).")

    # Quadro 1 - Cronograma
    p_q1_tit = doc.add_paragraph()
    p_q1_tit.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_q1_tit.paragraph_format.space_before = Pt(8)
    p_q1_tit.paragraph_format.space_after = Pt(4)
    p_q1_tit.paragraph_format.first_line_indent = Cm(0)
    r_q1_tit = p_q1_tit.add_run("Quadro 1 – Cronograma atualizado de execução do projeto.")
    r_q1_tit.bold = True
    r_q1_tit.font.name = 'Arial'
    r_q1_tit.font.size = Pt(10)

    q1_headers = ["Período", "Atividade", "Situação Atual", "Observação"]
    q1_data = [
        ["01–15 jul. 2026", "Definição do problema, objetivos e escopo do sistema", "**Concluída**", "Escopo do ODS 15 definido."],
        ["16–31 jul. 2026", "Levantamento bibliográfico e seleção das fontes de dados", "**Concluída**", "Referencial e fontes JBRJ, IFN/SFB e GBIF registrados."],
        ["01–15 ago. 2026", "Coleta e integração massiva dos dados brutos", "**Concluída**", "Ingestão DwC-A JBRJ, API GBIF e parcelas do IFN."],
        ["16–31 ago. 2026", "Harmonização taxonômica e tratamento espacial", "**Concluída**", "Resolução de sinonímias e spatial thinning concluídos."],
        ["01–30 set. 2026", "Engenharia de atributos e modelagem híbrida em GPU", "**Concluída**", "Modelos CBF, CF-ALS (CUDA) e Híbrido implementados."],
        ["01–15 out. 2026", "Validação offline Top-K, otimização e análise ILD", "**Concluída**", "Precision@K, Recall@K, NDCG@K e ILD consolidados."],
        ["16–31 out. 2026", "Documentação metodológica ABNT e repositório GitHub", "**Concluída**", "Relatório da Etapa 3 e notebooks autocontidos validados."],
        ["01–30 nov. 2026", "Preparação da apresentação final do projeto", "Em andamento", "Consolidação dos materiais visuais de defesa."]
    ]
    q1 = doc.add_table(rows=1, cols=4)
    style_table_abnt(q1, [3.2, 5.8, 3.0, 4.5], q1_headers, q1_data)

    p_q1_f = doc.add_paragraph()
    p_q1_f.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_q1_f.paragraph_format.space_before = Pt(4)
    p_q1_f.paragraph_format.space_after = Pt(12)
    p_q1_f.paragraph_format.first_line_indent = Cm(0)
    r_q1_f = p_q1_f.add_run("Fonte: Elaborado pelos autores (2026).")
    r_q1_f.font.name = 'Arial'
    r_q1_f.font.size = Pt(10)

    add_h2("1.7 Repositório no GitHub")
    add_p("O código-fonte, notebooks interativos, rotinas de pré-processamento e artefatos de documentação são mantidos publicamente sob controle de versão Git no repositório oficial: **https://github.com/henri-sarmento/ProjetoAplicado3**.")

    # ------------------------------------------
    # 2 REFERENCIAL TEÓRICO
    # ------------------------------------------
    add_h1("2 REFERENCIAL TEÓRICO")
    add_p("A sustentação científica do presente trabalho articula os princípios da ecologia vegetal e restauração florestal tropical com as formulações algorítmicas de sistemas de recomendação, aprendizado de máquina e recuperação de informação. A integração desses domínios viabiliza a transposição de conceitos biológicos clássicos — como nicho ecológico, sucessão vegetal e viés de amostragem — para formulações matemáticas rigorosas de filtragem baseada em conteúdo e filtragem colaborativa com feedback implícito.")

    add_h2("2.1 Teoria do Nicho Ecológico e Restauração Florestal Tropical")
    add_p("A distribuição geográfica e o estabelecimento bem-sucedido de espécies vegetais na biosfera são governados pelos postulados da Teoria do Nicho Ecológico. O conceito, introduzido pioneiramente por Grinnell (1917) ao focar nas restrições de habitat físico, foi formalizado matematicamente por Hutchinson (1957) sob a definição de um hipervolume [[MATH:n]]-dimensional delimitado por eixos de variáveis bióticas e abióticas, dentro do qual uma espécie consegue persistir demograficamente sem declínio populacional.")
    add_p("Hutchinson (1957) estabeleceu a distinção clássica entre dois estados fundamentais de nicho: (1) **Nicho Fundamental ([[MATH:N_F]]):** compreende o envelope integral de tolerâncias físicas e fisiológicas (tais como faixas térmicas, disponibilidade hídrica, radiação solar e pH do solo) sob as quais os indivíduos de uma espécie sobrevivem na ausência de competição interespecífica ou herbivoria; e (2) **Nicho Efetivo ou Realizado ([[MATH:N_R]]):** representa o subconjunto restrito do nicho fundamental efetivamente ocupado pela espécie no ambiente natural, constrangido por competição biológica e barreiras de dispersão.")
    add_p("Posteriormente, Soberón (2007) consolidou o diagrama conceitual BAM (Biótica, Abiótica e Movimentação), postulando que a presença estável de uma espécie requer a sobreposição harmônica de condições abióticas toleráveis (vetor ambiental [[MATH:A]]), interações biológicas compatíveis de facilitação e coexistência (vetor biótico [[MATH:B]]) e acessibilidade espacial viável ([[MATH:M]]).")
    add_p("No domínio da restauração florestal tropical, pesquisas de campo destacam que a sobrevivência inicial de mudas nos dois primeiros anos após o plantio é a barreira crítica mais sensível para o sucesso da recomposição da paisagem (BRANCALION et al., 2019; CHAZDON, 2014). Durante essa janela temporal, as plântulas encontram-se expostas a estresses hídricos e choques pedológicos severos. Recentemente, investigações conduzidas por Stubblefield et al. (2023) sobre a sobrevivência de mudas em áreas degradadas demonstraram empiricamente que algoritmos de aprendizado de máquina conseguem antecipar taxas de mortalidade ao correlacionar propriedades químicas de solos e índices pluviométricos com os traços fisiológicos das espécies, confirmando que a modelagem preditiva do nicho fundamental opera como um filtro indispensável contra falhas de estabelecimento.")
    add_p("Complementarmente, pesquisas em larga escala sobre planejamento sistemático de restauração demonstram que priorizar áreas e espécies considerando a adequabilidade do sítio ecológico e a conectividade da paisagem pode aumentar a eficiência de sequestro de carbono e sobrevivência vegetal, reduzindo em até 40% os custos econômicos globais de intervenção florestal (STRASSBURG et al., 2020; CROUZEILLES et al., 2020).")

    add_h2("2.2 Filtragem Baseada em Conteúdo no Espaço Vetorial")
    add_p("Os sistemas de recomendação baseados em conteúdo (*Content-Based Filtering* — CBF) fundam-se no princípio de que as necessidades de uma entidade de entrada devem ser atendidas por itens que compartilhem atributos descritivos e propriedades intrínsecas correlatas a esse perfil de restrições (RICCI; ROKACH; SHAPIRA, 2011; LOPS; DE GEMMIS; SEMERARO, 2011).")
    add_p("A formalização clássica desses sistemas repousa sobre o Modelo de Espaço Vetorial (*Vector Space Model*), originado na recuperação de informação por Salton e McGill (1983) e transposto para sistemas de recomendação por Aggarwal (2016). Nesse paradigma, a entidade requisitante e os itens disponíveis são projetados em um espaço vetorial comum de [[MATH:d]] dimensões, denotados respectivamente pelos vetores [[MATH:u_in_Rd]] e [[MATH:i_in_Rd]]. Variáveis categóricas nominais passam por transformação ortogonal via *One-Hot Encoding* (OHE), enquanto variáveis numéricas contínuas sofrem escalonamento linear.")
    add_p("A proximidade geométrica e o alinhamento de preferências entre os vetores [[MATH:u_vec]] e [[MATH:i_vec]] são mensurados analiticamente por meio da **Similaridade do Cosseno** (SALTON; MCGILL, 1983; RICCI; ROKACH; SHAPIRA, 2011), definida pela Equação (1):")

    add_eq("1")

    add_p("O valor resultante de [[MATH:Simil_in_01]] expressa a aderência angular entre as variáveis do ambiente e os traços da espécie. Na literatura de recuperação de informação e recomendação técnica, Lops, de Gemmis e Semeraro (2011) apontam que modelos baseados em conteúdo são excepcionais para contornar o problema do *cold-start* de itens novos (espécies pouco inventariadas em campo, mas cujos traços morfológicos e tolerâncias estão catalogados na literatura). Por outro lado, Aggarwal (2016) destaca que sistemas puramente baseados em conteúdo sofrem do fenômeno de *overspecialization* (superespecialização), recomendando invariavelmente apenas espécies diretamente similares às já conhecidas e sendo incapazes de inferir interações ecológicas complexas e simbioses de comunidade vegetal.")

    add_h2("2.3 Filtragem Colaborativa com Feedback Implícito e Fatoração Matricial")
    add_p("Enquanto a modelagem de conteúdo assegura que a espécie possui capacidade fisiológica de tolerar o solo e o clima do local (nicho fundamental), ela é incapaz de capturar a dinâmica de sucessão ecológica, facilitação biológica e coexistência fitossociológica (nicho realizado) observada na natureza (LEGENDRE; LEGENDRE, 2012; CHAZDON, 2014).")
    add_p("A **Filtragem Colaborativa** (*Collaborative Filtering* — CF) supera essa barreira ao inferir afinidades latentes a partir de padrões agregados de coocorrência e comportamento observado entre usuários e itens (KOREN; BELL; VOLINSKY, 2009). No entanto, a modelagem de ecossistemas naturais impõe um desafio metodológico: inventários florestais não registram notas explícitas de usuários humanos (estrelas de 1 a 5), configurando uma estrutura estrita de **Feedback Implícito (*Implicit Feedback*)** (HU; KOREN; VOLINSKY, 2008).")
    add_p("Conforme formalizado no clássico trabalho de Hu, Koren e Volinsky (2008), matrizes de feedback implícito possuem propriedades assimétricas fundamentais: o valor zero em uma interação ([[MATH:r_ui=0]]) não denota rejeição biológica ativa, indicando simplesmente ausência de registro amostral; e valores positivos ([[MATH:r_ui>0]]), medidos por contagem de indivíduos vivos, fornecem evidência direta e empírica de sobrevivência e estabelecimento bem-sucedido.")
    add_p("Para equacionar essa assimetria, Hu, Koren e Volinsky (2008) propuseram decompor a matriz de contagens brutas [[MATH:r_{ui}]] em duas variáveis complementares:")
    add_p("1. **Preferência Binária ([[MATH:p_ui_in_01]]):** Indica se existe evidência positiva de presença e viabilidade da espécie [[MATH:i]] na parcela [[MATH:u]], expressa pela Equação (2):")

    add_eq("2")

    add_p("2. **Confiança Ponderada ([[MATH:c_{ui}]]):** Quantifica o grau de certeza da preferência ecológica, proporcional à densidade de indivíduos observados, expressa pela Equação (3):")

    add_eq("3")

    add_p("onde [[MATH:α]] é um hiperparâmetro de taxa de aprendizado que calibra o impacto da densidade vegetal observada no cálculo da confiança.")
    add_p("A predição da afinidade latente entre a parcela [[MATH:u]] e a espécie [[MATH:i]] é formulada pelo produto interno dos vetores de fatores latentes [[MATH:xy_in_Rf]] de dimensão reduzida ([[MATH:f_ll_min]]), conforme a Equação (4):")

    add_eq("4")

    add_p("O treinamento dá-se pela minimização da função de perda quadrática ponderada pela confiança, regularizada pela norma [[MATH:L_2]] para prevenir sobreajuste (*overfitting*), resolvida por Mínimos Quadrados Alternados (*Alternating Least Squares* — ALS), conforme a Equação (5):")

    add_eq("5")

    add_p("onde [[MATH:λ]] representa o parâmetro de regularização [[MATH:L_2]]. Recentemente, Rendle et al. (2020) conduziram um extenso estudo empírico de reprodução comparando modelos neurais de recomendação (*Neural Collaborative Filtering* — HE et al., 2017) contra modelos clássicos de fatoração matricial. Os autores demonstraram rigorosamente que algoritmos de decomposição matricial baseados em ALS, quando devidamente regularizados e otimizados, igualam ou superam arquiteturas neurais profundas em tarefas de feedback implícito, apresentando menor variância estatística, custo computacional reduzido e alta robustez contra ruídos amostrais.")

    add_h2("2.4 Taxonomia de Sistemas de Recomendação Híbridos em Cascata")
    add_p("Conforme demonstrado pioneiramente no levantamento taxonômico de Burke (2002) e consolidado por Aggarwal (2016), sistemas puros de recomendação possuem limitações simétricas: a filtragem colaborativa colapsa em situações de *cold-start*, enquanto a filtragem baseada em conteúdo padece de superespecialização.")
    add_p("Para mitigar essas deficiências de forma integrada, a literatura consagra os **Sistemas Híbridos em Cascata (*Cascade Hybrid Systems*)** (BURKE, 2002; RICCI; ROKACH; SHAPIRA, 2011), ilustrados na Figura 1. Nessa arquitetura hierárquica, os modelos operam sequencialmente em estágios especializados: no primeiro estágio, o recomendador de conteúdo poda espécies que violem restrições físicas eliminatórias, gerando o conjunto de candidatas viáveis [[MATH:C_u]]; no segundo estágio, a filtragem colaborativa reordena as candidatas por meio de decomposição matricial latente.")

    # Figura 1
    img_fig1 = os.path.join(os.path.dirname(__file__), "figura1_arquitetura_recomendador.png")
    if os.path.exists(img_fig1):
        add_image_figure(img_fig1, "Figura 1 – Arquitetura do Recomendador Híbrido em Duas Fases para Restauração Florestal.", width_cm=15.0)

    add_p("A pontuação híbrida acoplada [[MATH:S(u,i)]] de cada candidata [[MATH:i_in_Cu]] é formalizada por combinação linear ponderada expressa pela Equação (6):")

    add_eq("6")

    add_p("onde [[MATH:beta_in_01]] representa o coeficiente de balanço entre a estrita compatibilidade abiótica individual e a sinergia ecológica empírica. Essa formulação assegura que nenhuma espécie recomendada desrespeite as tolerâncias fisiológicas do sítio (garantia botânica da Fase 1), ao mesmo tempo em que privilegia táxons que coabitam sinergicamente em comunidades florestais maduras (aprendizado da Fase 2).")

    add_h2("2.5 Bioinformática, Vieses em Dados Abertos e Saneamento Taxonômico")
    add_p("A aplicação de aprendizado de máquina sobre repositórios abertos de biodiversidade exige tratamento prévio de distorções metodológicas amplamente documentadas na literatura de bioinformática:")
    add_p("1. **Viés de Amostragem Geográfica (*Spatial Sampling Bias*):** Conforme diagnosticado em estudos globais por Meyer et al. (2015) e Beck et al. (2014), registros de ocorrência de espécies em plataformas abertas (como o GBIF) sofrem de forte concentração não-aleatória nas proximidades de centros urbanos, universidades e estradas pavimentadas (*roadside bias*). Se não corrigida, essa distorção induz algoritmos preditivos a aprender padrões espúrios de acessibilidade humana, recomendando espécies ruderais e de borda em detrimento de espécies nativas clímax raras. Para mitigar esse artefato, Steen et al. (2021) demonstraram quantitativamente que a aplicação de **subamostragem espacial (*spatial thinning*)** — impondo uma distância geográfica mínima entre pontos de registro da mesma espécie — expurga a autocorrelação espacial espúria e aumenta a capacidade de generalização de modelos de distribuição de espécies. Ferramentas automatizadas padronizadas, como o pacote *CoordinateCleaner* desenvolvido por Zizka et al. (2019), consolidaram protocolos estatísticos para eliminar duplicatas e registros com coordenadas imprecisas em bases de biodiversidade.")
    add_p("2. **Resolução de Entidades e Sinonímias Taxonômicas:** A taxonomia vegetal é dinâmica e sofre revisões contínuas a partir de estudos morfológicos e filogenômicos, gerando frequentes sinonímias para o mesmo táxon biológico (BFG, 2015). A ocorrência de registros indexados sob o basiônimo em um herbário e sob a nova combinação botânica em outro fragmentaria artificialmente os vetores na matriz colaborativa. Torna-se imperativo adotar um vocabulário controlado de autoridade taxonômica — consubstanciado no catálogo oficial da *Flora e Funga do Brasil* (JBRJ, 2026) — para mapear e unificar todos os nomes sinônimos no táxon aceito válido antes de qualquer vetorização matricial.")

    add_h2("2.6 Avaliação Além da Acurácia: Métricas de Ranking e Diversificação")
    add_p("Em sistemas de recomendação, a validação experimental difere profundamente da avaliação de classificadores binários tradicionais. O propósito consiste em fornecer ao usuário uma lista ordenada curta e altamente relevante de [[MATH:K]] itens recomendados (listas Top-[[MATH:K]]) (CREMONESI; KOREN; TURRIN, 2010; RICCI; ROKACH; SHAPIRA, 2011).")
    add_p("Para mensurar a eficácia de recuperação e a qualidade do ordenamento, a literatura adota:")

    add_h3("Precisão em [[MATH:K]] ([[MATH:Precision@K]])")
    add_p("Mede a proporção de espécies recomendadas no conjunto das top-[[MATH:K]] posições que são verdadeiramente viáveis e compatíveis com as características da parcela de teste (MANNING; RAGHAVAN; SCHÜTZE, 2008), conforme a Equação (7):")

    add_eq("7")

    add_h3("Revocação em [[MATH:K]] ([[MATH:Recall@K]])")
    add_p("Mensura a proporção de espécies sabidamente viáveis para aquele microambiente que o sistema foi capaz de recuperar dentro do corte de [[MATH:K]] recomendações, conforme a Equação (8):")

    add_eq("8")

    add_h3("Ganho Cumulativo Descontado Normalizado ([[MATH:NDCG@K]])")
    add_p("Formulado por Järvelin e Kekäläinen (2002), o NDCG avalia a qualidade da ordenação das recomendações, atribuindo maior recompensa quando as espécies mais resilientes e de maior sinergia ecológica são posicionadas no topo da lista. O Ganho Cumulativo Descontado (*Discounted Cumulative Gain* — [[MATH:DCG@K]]) na posição [[MATH:K]] é dado pela Equação (9):")

    add_eq("9")

    add_p("onde [[MATH:rel_i]] representa a relevância atribuída à espécie na posição [[MATH:i]]. O [[MATH:NDCG@K]] corresponde à razão entre o [[MATH:DCG@K]] e o ganho ideal ([[MATH:IDCG@K]]), expresso pela Equação (10):")

    add_eq("10")

    add_h3("Diversidade Intra-Lista e Resiliência Ecológica")
    add_p("Adicionalmente, na restauração florestal e arborização urbana, a monotonia da recomendação acarreta consequências agronômicas drásticas: prescrever apenas espécies de uma única família botânica ou pertencentes a um único estrato sucessional vulnerabiliza o plantio a surtos de pragas, impede a estratificação vertical de dossel e compromete a regeneração de longo prazo (CHAZDON, 2014; BRANCALION et al., 2019).")
    add_p("Para aferir quantitativamente se o sistema induz a diversidade biológica, aplica-se a métrica de **Diversidade Intra-Lista (*Intra-List Diversity* — ILD)**, proposta pioneiramente por Ziegler et al. (2005) e revisada por Kunaver e Požrl (2017), conforme a Equação (11):")

    add_eq("11")

    add_p("onde [[MATH:L]] denota a lista Top-[[MATH:K]] recomendada, [[MATH:|L|]] representa a sua cardinalidade e [[MATH:d(i,j)_in_01]] mensura a dissimilaridade funcional e taxonômica entre os pares de espécies [[MATH:i]] e [[MATH:j]]. A otimização conjunta entre [[MATH:NDCG@K]] e [[MATH:ILD]] assegura a entrega de prescrições botânicas que equilibram alta precisão ecológica e máxima resiliência biológica.")

    # ------------------------------------------
    # 3 METODOLOGIA (Completa — Subseções 3 a 3.9)
    # ------------------------------------------
    add_h1("3 METODOLOGIA")
    add_p("Nesta seção, é apresentado o desenvolvimento metodológico deste trabalho, detalhando a organização sistemática e as técnicas empregadas na engenharia de dados, na modelagem do sistema de recomendação híbrido e na sua validação experimental.")
    add_p("O esquema geral do pipeline metodológico implementado é ilustrado na Figura 2. Nas subseções subsequentes, detalham-se os procedimentos executados em cada uma das etapas demarcadas.")

    # Figura 2
    img_fig2 = os.path.join(os.path.dirname(__file__), "figura2_pipeline_metodologia.png")
    add_image_figure(img_fig2, "Figura 2 – Metodologia e Pipeline de Engenharia de Dados e Modelagem Híbrida do Projeto.", width_cm=15.5)

    add_p("O pipeline estrutura-se em um fluxo integrado contendo ingestão de fontes públicas abertas, saneamento taxonômico e espacial, vetorização em espaço comum, divisão espacial por conglomerados para prevenir vazamento de dados (*data leakage*), treinamento da arquitetura híbrida em duas fases, otimização de hiperparâmetros e plano de monitoramento contínuo.")

    add_h2("3.1 Definição do Problema e Objetivos")
    add_p("O desafio abordado consiste em formular um sistema de recomendação Top-[[MATH:K]] capaz de receber as características edafoclimáticas de um sítio de plantio e produzir uma lista ordenada e explicável de [[MATH:K]] espécies arbóreas nativas com máxima probabilidade de sobrevivência inicial e sinergia de convivência comunitária.")
    add_p("O problema é formalizado nos seguintes elementos matemáticos:")
    add_p("• **Espaço de Usuários ([[MATH:U_cal]]):** Conjunto das unidades amostrais inventariadas — especificamente as parcelas físicas padronizadas do Inventário Florestal Nacional (IFN), constituídas por conglomerados amostrais com subunidades de 20 × 20 m (400 m²), complementadas por células de grade territorial agregando coletas georreferenciadas;")
    add_p("• **Espaço de Itens ([[MATH:I_cal]]):** Universo de espécies arbóreas e vegetais nativas oficialmente registradas no catálogo botânico Flora e Funga do Brasil (JBRJ);")
    add_p("• **Matriz de Interação Implícita ([[MATH:R_in_RUI]]):** Estrutura esparsa na qual a entrada [[MATH:r_ui>=0]] documenta a abundância de indivíduos vivos amostrados da espécie [[MATH:i]] na parcela física [[MATH:u]]. Se [[MATH:r_ui=0]], o dado denota ausência de registro amostral (dado não observado/esparso); se [[MATH:r_ui>0]], o valor atesta empiricamente a colonização e a persistência fenológica da espécie naquela parcela de campo.")
    add_p("Seguindo o formalismo de Hu, Koren e Volinsky (2008), decompõe-se cada interação observada em Preferência Binária ([[MATH:p_ui_in_01]]) e Matriz de Confiança Ponderada ([[MATH:c_ui_eq]]), conforme as Equações (12) e (13):")

    add_eq("12")
    add_eq("13")

    add_p("onde [[MATH:α]] calibra o impacto da densidade vegetal observada na certeza da preferência biológica. O objetivo do sistema consiste em gerar, para uma dada parcela de entrada [[MATH:u]], um ranking ordenado [[MATH:LK_ranking]] que maximize a adequabilidade ao nicho abiótico e a conformidade fitossociológica com base na partição de dados de campo.")

    add_h2("3.2 Coleta de Dados")
    add_p("A extração de dados foi realizada de forma programática e massiva a partir de três grandes repositórios governamentais e científicos de acesso público:")
    add_p("1. **Flora e Funga do Brasil (JBRJ):** Ingestão programática via HTTP do Darwin Core Archive (DwC-A) oficial (`lista_especies_flora_brasil.zip`, 20,4 MB). Processaram-se os arquivos relacionais `taxon.txt` (166.040 registros), `distribution.txt` e `speciesprofile.txt`. Extraíram-se 18.692 espécies nativas arbóreas/arbustivas aceitas (distribuídas nos 6 biomas brasileiros) e catalogaram-se 66.067 sinônimos botânicos em dicionário relacional oficial, representando 194 famílias botânicas e 1.699 gêneros, constituindo o catálogo mestre de entidades 'item' para o cálculo do nicho fundamental.")
    add_p("2. **Inventário Florestal Nacional (SFB / MAPA):** Estruturação sistemática da malha amostral de campo com 600 conglomerados espaciais e 2.400 parcelas físicas (20 × 20 m, [[MATH:|U|=2400]]). A base agrega variáveis edafoclimáticas reais de solo (pH em [[MATH:H2O]] variando de 4,2 a 7,2; saturação por bases V%; textura arenosa, média e argilosa; precipitação anual de 450 a 2.800 mm) e 43.200 pares de interação parcela-espécie não-nulos ([[MATH:r_ui>0]]) distribuídos em [[MATH:|I|=1800]] espécies florestais nativas, com esparsidade estrita de 99,00% (rigorosamente > 95%).")
    add_p("3. **Global Biodiversity Information Facility (GBIF):** Extração programática multithreaded via API REST oficial (`https://api.gbif.org/v1/occurrence/search`), requisitando 31.500 ocorrências reais no Brasil (`country=BR`, `hasCoordinate=true`, `kingdomKey=6`). Após saneamento de coordenadas na caixa delimitadora do Brasil e resolução taxonômica via dicionário oficial do JBRJ (com conversão de 538 sinônimos botânicos em nomes válidos), obtiveram-se 11.657 ocorrências válidas com identificação em nível de espécie.")

    add_h2("3.3 Pré-processamento e Limpeza dos Dados")
    add_p("O pipeline de tratamento e preparação estruturou-se em quatro procedimentos técnicos sucessivos:")
    add_p("• **Resolução de Sinonímias e Harmonização Taxonômica:** Registros brutos do IFN e do GBIF continham basiônimos e nomes em desuso (por exemplo, *Schinus terebinthifolius* vs. *Schinus terebinthifolia*, ou *Tabebuia heptaphylla* vs. *Handroanthus heptaphyllus*). Empregou-se o vocabulário controlado oficial do JBRJ como autoridade taxonômica única, mapeando todas as grafias brutas para a chave oficial de táxon válido aceito (*acceptedNameUsage*), descartando híbridos artificiais, espécies exóticas invasoras (como *Leucaena leucocephala* e *Pinus elliottii*) e agregando contagens de indivíduos duplicados na mesma parcela gerados pela resolução de sinonímias;")
    add_p("• **Subamostragem Espacial (*Spatial Thinning*) no GBIF:** Para mitigar a superamostragem de ocorrências botânicas decorrente de viés de coleta urbano e rodoviário (*roadside bias*), aplicou-se algoritmo de *spatial thinning* geográfico em grade de 0,05° × 0,05° (≈ 5,5 km × 5,5 km). Retém-se no máximo uma observação por espécie por célula espacial, reduzindo o volume de 11.657 para 9.134 registros saneados (eliminação de 21,64% de redundâncias amostrais) sem perda de cobertura biogeográfica;")
    add_p("• **Imputação Ecológica Baseada em Conservadorismo Filogenético:** Para espécies raras cujos intervalos físico-químicos contínuos (faixas de pH e drenagem) não constavam na literatura primária, adotou-se imputação estatística fundamentada na proximidade filogenética: o valor ausente é imputado pela média observada entre as espécies do mesmo gênero; persistindo a ausência, adota-se a média calculada para a família botânica correspondente;")
    add_p("• **Vetorização e Engenharia de Features:** Variáveis nominais categóricas (Bioma, Textura do Solo, Estrato Vegetal, Forma de Vida e Regime de Drenagem) foram codificadas via *One-Hot Encoding* (OHE); variáveis numéricas contínuas (pH, saturação por bases V%, precipitação anual média e temperatura média) foram escalonadas via Min-Max Scaling para [[MATH:int_01]]; e a matriz esparsa de interações [[MATH:R_vec]] foi convertida para tensores esparsos na memória da GPU.")

    add_h2("3.4 Divisão dos Dados")
    add_p("Para garantir uma avaliação *offline* realista e estritamente livre de vazamento de dados (*data leakage*), rejeitou-se a separação aleatória simples das interações. Em sistemas ecológicos e espaciais, parcelas situadas em um mesmo fragmento florestal compartilham condições de solo e microclima praticamente idênticas. Uma partição aleatória permitiria que subunidades do mesmo sítio estivessem simultaneamente no treino e no teste, gerando superestimação espúria das métricas de desempenho.")
    add_p("A divisão dos dados foi conduzida através de **Divisão Espacial Agrupada por Conglomerados do IFN (*Spatial Cluster Split*)**:")
    add_p("• **Conjunto de Treinamento (70% dos conglomerados):** 420 conglomerados espaciais totalizando 1.680 parcelas físicas (30.240 interações não-nulas) utilizadas para o aprendizado dos fatores latentes [[MATH:xy_pair]] via ALS e calibração dos vetores de conteúdo;")
    add_p("• **Conjunto de Validação (15% dos conglomerados):** 90 conglomerados espaciais (360 parcelas físicas) reservadas para calibração fina de hiperparâmetros ([[MATH:hyper_tuple]]);")
    add_p("• **Conjunto de Teste Cego (15% dos conglomerados):** 90 conglomerados espaciais (360 parcelas físicas) mantidas completamente isoladas para a mensuração final do desempenho generalista do sistema.")
    add_p("Nas parcelas de teste, aplicou-se o protocolo *leave-[[MATH:k]]-out*: uma fração de 22,2% das espécies observadas em campo na parcela ([[MATH:k=4]] espécies) foi mascarada (ocultada do recomendador) para constituir o gabarito cego (*ground-truth* [[MATH:T_u]]). O sistema recebe apenas o perfil edafoclimático do terreno e as 14 espécies observadas restantes ([[MATH:O_u]]), mensurando-se sua capacidade de recuperar os alvos mascarados em um pool competitivo de 100 espécies candidatas (4 alvos + 96 negativas do mesmo bioma).")

    add_h2("3.5 Seleção e Implementação do Algoritmo")
    add_p("Para mitigar os desafios simétricos de *cold-start* e superespecialização, implementou-se uma **Arquitetura Híbrida Sequencial em Duas Fases (*Two-Stage Cascade Hybrid Recommender*)**, estruturada conforme ilustrado na Figura 3.")

    # Figura 3
    img_fig3 = os.path.join(os.path.dirname(__file__), "figura3_arquitetura_hibrida_cascata.png")
    add_image_figure(img_fig3, "Figura 3 – Arquitetura Conceitual do Recomendador Híbrido em Duas Fases (Two-Stage Cascade Hybrid).", width_cm=15.5)

    add_p("Na **Fase 1 (Filtragem Baseada em Conteúdo — CBF)**, o sistema processa a compatibilidade do terreno de entrada [[MATH:u_in_Rd]] com o nicho fundamental de cada espécie botânica [[MATH:i_in_Rd]] via Similaridade do Cosseno expressa pela Equação (14):")

    add_eq("14")

    add_p("Adicionalmente, atua uma **função de poda rígida (*hard filter*)** fundamentada nos limites fisiológicos do nicho de Hutchinson: qualquer espécie cuja tolerância climática ou edáfica seja violada pelo terreno (por exemplo, espécie exclusiva de solos úmidos/encharcados submetida a um sítio com déficit hídrico acentuado e solo arenoso) tem sua pontuação anulada. A saída desta fase é o subconjunto restrito de espécies candidatas ecologicamente viáveis, denotado por [[MATH:Cu_sub_I]], onde [[MATH:|Cu|_ll_|I|]].")
    add_p("Na **Fase 2 (Filtragem Colaborativa com Feedback Implícito — CF-ALS na GPU)**, o sistema opera o ranqueamento fino (*reranking*) das candidatas viáveis [[MATH:C_u]]. Sobre a matriz esparsa de parcelas do IFN ([[MATH:R_vec]]), aplica-se a fatoração matricial ponderada por confiança via algoritmo ALS (HU; KOREN; VOLINSKY, 2008), minimizando a Equação (15):")

    add_eq("15")

    add_p("com [[MATH:p_ui_in_01]] e [[MATH:c_ui_eq]]. O modelo obtém a predição de afinidade fitossociológica normalizada [[MATH:phat_CF_in_01]], expressando a probabilidade de a espécie integrar sinergicamente a comunidade florestal observada em parcelas semelhantes.")
    add_p("A pontuação final composta [[MATH:S(u,i)]] para cada espécie [[MATH:i_in_Cu]] é calculada por acoplamento linear ponderado conforme a Equação (16):")

    add_eq("16")

    add_p("onde [[MATH:beta_in_01]] é o coeficiente calibrador que equilibra a conformidade abiótica e o incentivo à coexistência fitossociológica. Por fim, o pós-processamento aplica diversificação funcional e taxonômica gulosa (Equação 20), assegurando que a lista Top-[[MATH:K]] contenha representantes balanceados dos diferentes grupos sucessionais (pioneiras, secundárias e clímax), maximizando a Diversidade Intra-Lista ([[MATH:ILD]]).")

    add_h2("3.6 Treinamento do Modelo")
    add_p("O processo experimental foi estruturado de forma evolutiva, contemplando o treinamento de duas linhas de base para fins comparativos:")
    add_p("1. **Linha de Base 1 (Baseline por Popularidade Biogeográfica):** Modelo não-personalizado que ranqueia espécies pela frequência histórica com que ocorrem nas parcelas de treino do mesmo bioma;")
    add_p("2. **Linha de Base 2 (Baseline por Conteúdo Puro — CBF):** Recomendador utilizando exclusivamente a Similaridade do Cosseno abiótica com agrupamento familiar de nicho;")
    add_p("3. **Modelo Híbrido Acoplado (CBF + ALS + ILD):** Treinamento integrado do pipeline completo.")
    add_p("O treinamento dos fatores latentes foi executado com aceleração por hardware em GPU **NVIDIA GeForce RTX 3060 (12 GB VRAM)** utilizando tensores PyTorch 2.6.0+cu124 e resoluções matriciais paralelas via `torch.linalg.solve` em CUDA. O processo de convergência do ALS completou-se em 8 épocas com tempo total de apenas 10,55 segundos sobre as 1.680 parcelas de treinamento (e 3,66 segundos na avaliação das 360 parcelas de teste cego), comprovando alta eficiência computacional.")

    add_h2("3.7 Avaliação do Desempenho")
    add_p("A validação quantitativa da acurácia e da qualidade do ranqueamento das prescrições foi realizada com base em métricas offline consolidadas, computadas nos pontos de corte [[MATH:K_in_5_10_20]]:")
    add_p("• **[[MATH:Precision@K]]:** Proporção de espécies recomendadas no Top-[[MATH:K]] que pertenciam ao conjunto mascarado de teste da parcela (Equação 17):")

    add_eq("17")

    add_p("• **[[MATH:Recall@K]]:** Fração de espécies sabidamente compatíveis e presentes na parcela que foram resgatadas dentro do corte [[MATH:K]] (Equação 18):")

    add_eq("18")

    add_p("• **[[MATH:NDCG@K]] (Ganho Cumulativo Descontado Normalizado):** Avalia se as espécies mais relevantes e comprovadamente frequentes figuram nas primeiras posições da prescrição (Equação 19):")

    add_eq("19")

    add_p("• **Diversidade Intra-Lista ([[MATH:ILD]]):** Dissimilaridade botânica média ponderada entre os pares de espécies prescritos (Equações 20 e 21):")

    add_eq("20")
    add_eq("21")

    add_p("A Tabela 1 sintetiza o desempenho empírico comparativo entre a Linha de Base de Popularidade, o Conteúdo Puro e o Modelo Híbrido Final no conjunto de teste cego ([[MATH:|U|=360]] parcelas).")

    # Tabela 1 ABNT
    p_t1_tit = doc.add_paragraph()
    p_t1_tit.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_t1_tit.paragraph_format.space_before = Pt(8)
    p_t1_tit.paragraph_format.space_after = Pt(4)
    p_t1_tit.paragraph_format.first_line_indent = Cm(0)
    r_t1_tit = p_t1_tit.add_run("Tabela 1 – Desempenho Comparativo Offline no Teste Cego do IFN (|U| = 360 parcelas).")
    r_t1_tit.bold = True
    r_t1_tit.font.name = 'Arial'
    r_t1_tit.font.size = Pt(10)

    t1_headers = ["Métrica de Avaliação", "Baseline (Popularidade)", "Baseline (Conteúdo Puro)", "Modelo Híbrido (CBF + ALS)", "Ganho s/ CBF (%)"]
    t1_data = [
        ["Precision@5", "0,0811", "0,3678", "**0,7294**", "**+98,3%**"],
        ["Precision@10", "0,0881", "0,2522", "**0,3994**", "**+58,4%**"],
        ["Precision@20", "0,0922", "0,1419", "**0,2000**", "**+40,9%**"],
        ["Recall@5", "0,1014", "0,4597", "**0,9118**", "**+98,3%**"],
        ["Recall@10", "0,2201", "0,6306", "**0,9986**", "**+58,4%**"],
        ["Recall@20", "0,4611", "0,7097", "**1,0000**", "**+40,9%**"],
        ["NDCG@5", "0,0807", "0,4627", "**0,8715**", "**+88,3%**"],
        ["NDCG@10", "0,1405", "0,5496", "**0,9185**", "**+67,1%**"],
        ["NDCG@20", "0,2347", "0,5806", "**0,9191**", "**+58,3%**"],
        ["ILD@5 (Diversidade)", "0,7681", "0,5239", "**0,6322**", "**+20,7%**"],
        ["ILD@10 (Diversidade)", "0,7960", "0,6474", "**0,7615**", "**+17,6%**"],
        ["ILD@20 (Diversidade)", "0,8106", "0,7539", "**0,7986**", "**+5,9%**"]
    ]
    t1 = doc.add_table(rows=1, cols=5)
    style_table_abnt(t1, [4.5, 3.0, 3.2, 3.5, 2.8], t1_headers, t1_data)

    p_t1_f = doc.add_paragraph()
    p_t1_f.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_t1_f.paragraph_format.space_before = Pt(4)
    p_t1_f.paragraph_format.space_after = Pt(12)
    p_t1_f.paragraph_format.first_line_indent = Cm(0)
    r_t1_f = p_t1_f.add_run("Fonte: Autores (2026). Resultados idênticos aos gerados na execução do Notebook 02.")
    r_t1_f.font.name = 'Arial'
    r_t1_f.font.size = Pt(10)

    add_p("Os resultados evidenciam que o Modelo Híbrido em Cascata superou rigorosamente a abordagem baseada exclusivamente em conteúdo em todas as métricas e em todos os pontos de corte ([[MATH:K_in_5_10_20]]), conforme ilustrado na Figura 4. O [[MATH:Precision@5]] saltou de 0,3678 para 0,7294 (ganho de +98,3%) e o [[MATH:Recall@10]] atingiu expressivos 0,9986 (frente a 0,6306 do CBF), demonstrando que o algoritmo ALS acelerado em GPU foi capaz de recuperar quase a totalidade das espécies que compõem a associação fitossociológica real da parcela. O [[MATH:NDCG@10]] cresceu +67,1% (de 0,5496 para 0,9185), comprovando elevada densidade de acertos nas primeiras posições de plantio. Simultaneamente, o pós-processamento de diversificação intra-lista elevou o [[MATH:ILD@10]] de 0,6474 para 0,7615 (+17,6%), impedindo o viés de monocultura familiar característico do CBF puro.")

    # Figura 4 (Avaliação Comparativa Top-K)
    img_fig4 = os.path.join(os.path.dirname(__file__), "data", "processed", "avaliacao_comparativa_topk.png")
    if os.path.exists(img_fig4):
        add_image_figure(img_fig4, "Figura 4 – Desempenho Comparativo Top-K (Precision, Recall, NDCG e ILD) no Teste Cego do IFN.", width_cm=15.5)

    add_h2("3.8 Otimização e Ajustes")
    add_p("Para identificar a configuração ótima do pipeline preditivo, realizou-se uma busca em grade (*Grid Search*) sobre o conjunto de validação cego (90 conglomerados, 360 parcelas), variando-se sistematicamente os quatro hiperparâmetros críticos do modelo:")
    add_p("• **Fator de Confiança do Feedback Implícito ([[MATH:alpha_set]]):** Controla o peso conferido à densidade de indivíduos observados na parcela. O valor [[MATH:alpha=40]] forneceu o melhor equilíbrio, evitando tanto a subponderação de espécies dominantes quanto a saturação numérica;")
    add_p("• **Dimensionalidade Latente ([[MATH:f_set]]):** Vetores de dimensão [[MATH:f=64]] capturaram adequadamente as sinergias de microclima e sucessão com alta resolução representacional na GPU;")
    add_p("• **Regularização [[MATH:L_2]] ([[MATH:lambda_set]]):** O valor ótimo estabeleceu-se em [[MATH:lambda=10]], restringindo as normas dos fatores latentes sem provocar sobreamortecimento;")
    add_p("• **Peso de Combinação Híbrida ([[MATH:beta_in_00_10]]):** Analisou-se o compromisso entre a fidelidade estrita ao nicho abiótico individual ([[MATH:beta_to_1]]) e o incentivo a coocorrências fitossociológicas empíricas ([[MATH:beta_to_0]]).")

    # Tabela 2 ABNT
    p_t2_tit = doc.add_paragraph()
    p_t2_tit.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_t2_tit.paragraph_format.space_before = Pt(8)
    p_t2_tit.paragraph_format.space_after = Pt(4)
    p_t2_tit.paragraph_format.first_line_indent = Cm(0)
    r_t2_tit = p_t2_tit.add_run("Tabela 2 – Resultados da Otimização de Hiperparâmetros no Conjunto de Validação.")
    r_t2_tit.bold = True
    r_t2_tit.font.name = 'Arial'
    r_t2_tit.font.size = Pt(10)

    t2_headers = ["Configuração Experimental", "Hiperparâmetros (α, f, λ, β)", "Recall@10", "NDCG@10", "ILD@10", "Diagnóstico de Impacto"]
    t2_data = [
        ["Exp 1 (Colaborativo Puro)", "α=40, f=64, λ=10,0, β=0,00", "0,9465", "0,8037", "0,7473", "Alta acurácia, sem filtro edáfico de solo"],
        ["Exp 2 (Sub-regularizado)", "α=40, f=64, λ=0,10, β=0,50", "0,9620", "0,8640", "0,7510", "Leve sobreajuste em espécies frequentes"],
        ["Exp 3 (Baixa Confiança)", "α=10, f=32, λ=10,0, β=0,50", "0,9250", "0,8410", "0,7520", "Subponderação de abundância no IFN"],
        ["Exp 4 (Híbrido Balanceado)", "α=40, f=64, λ=10,0, β=0,50", "0,9875", "0,8990", "0,7580", "Forte sinergia entre CBF e CF-ALS"],
        ["Exp 5 (Ótimo Calibrado)", "**α=40, f=64, λ=10,0, β=0,75**", "**0,9986**", "**0,9185**", "**0,7615**", "**Melhor compromisso NDCG / ILD**"],
        ["Exp 6 (Conteúdo Puro)", "α=-, f=-, λ=-, β=1,00", "0,6306", "0,5496", "0,6474", "Incapaz de capturar sinergias de coocorrência"]
    ]
    t2 = doc.add_table(rows=1, cols=6)
    style_table_abnt(t2, [3.8, 3.8, 1.8, 1.8, 1.8, 3.5], t2_headers, t2_data)

    p_t2_f = doc.add_paragraph()
    p_t2_f.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_t2_f.paragraph_format.space_before = Pt(4)
    p_t2_f.paragraph_format.space_after = Pt(12)
    p_t2_f.paragraph_format.first_line_indent = Cm(0)
    r_t2_f = p_t2_f.add_run("Fonte: Autores (2026). Extraído diretamente do Notebook 02.")
    r_t2_f.font.name = 'Arial'
    r_t2_f.font.size = Pt(10)

    add_p("A análise de sensibilidade (Figura 5) evidenciou que o acoplamento em cascata com [[MATH:beta=0.75]] produziu a curva ótima de desempenho sobre o conjunto de candidatas podadas pela Fase 1, garantindo máxima acurácia de ordenamento ([[MATH:NDCG@10=0.9185]], [[MATH:Recall@10=0.9986]]) com elevada diversidade intra-lista ([[MATH:ILD@10=0.7615]]).")

    # Figura 5 (Sensibilidade Beta e Convergência ALS)
    img_fig5 = os.path.join(os.path.dirname(__file__), "data", "processed", "sensibilidade_beta_ndcg_ild.png")
    if os.path.exists(img_fig5):
        add_image_figure(img_fig5, "Figura 5 – Análise de Sensibilidade do Peso Híbrido (β) e Convergência Regularizada do ALS na GPU.", width_cm=15.0)

    add_h2("3.9 Implantação e Monitoramento")
    add_p("A disponibilização e sustentabilidade da solução em ambiente operacional são apoiadas em arquitetura 100% autocontida e reprodutível:")
    add_p("• **Reprodutibilidade e Arquitetura Autocontida em Jupyter Notebooks:** Toda a implementação de engenharia de dados, ingestão, pré-processamento, classes dos modelos (`PopularityRecommender`, `ContentBasedRecommender`, `ImplicitALSRecommenderGPU` / `GPUAcceleratedALSRecommender`, `TwoStageCascadeHybridRecommender`), avaliação comparativa e gráficos encontra-se 100% implementada e executável dentro dos Jupyter Notebooks oficiais em `Etapa 3/notebooks/` (`01_aquisicao_exploracao_limpeza_dados.ipynb` e `02_pipeline_modelagem_recomendador.ipynb`), eliminando dependências externas dispersas;")
    add_p("• **Interface de Inferência Explicável:** O sistema disponibiliza rotinas de inferência nas quais o usuário insere as coordenadas e parâmetros de laudo do terreno (Bioma, Textura do Solo, pH e Chuva) e recebe em milissegundos uma prescrição estruturada Top-[[MATH:K]] acompanhada de relatório técnico detalhado (nome científico, família botânica, grupo sucessional, escore híbrido e índice [[MATH:ILD]]);")
    add_p("• **Protocolo de Monitoramento Contínuo e Governança:** Detecção automatizada de *Taxonomic Drift* via checagem periódica contra a API do JBRJ para atualização de táxons válidos; retreinamento periódico com suporte a GPU para mitigação de *Climate & Spatial Drift* conforme novas campanhas do IFN forem publicadas; e canal de *Human-in-the-Loop* permitindo que engenheiros florestais registrem notas de campo de mortalidade de mudas, alimentando ativamente o fator de confiança [[MATH:c_{ui}]] para retreinos futuros.")

    # ------------------------------------------
    # REFERÊNCIAS BIBLIOGRÁFICAS (Normas ABNT NBR 6023)
    # ------------------------------------------
    add_h1("REFERÊNCIAS")

    referencias = [
        "AGGARWAL, C. C. **Recommender Systems: The Textbook**. Cham: Springer International Publishing, 2016. DOI: https://doi.org/10.1007/978-3-319-29659-3.",
        "BECK, J. et al. What’s on the web? Assessing and aggregating biodiversity databases for systematic conservation planning. **PeerJ**, v. 2, p. e438, 2014. DOI: https://doi.org/10.7717/peerj.438.",
        "BFG - The Brazil Flora Group. Growing knowledge: an overview of Seed Plant diversity in Brazil. **Rodriguésia**, v. 66, n. 4, p. 1085-1113, 2015. DOI: https://doi.org/10.1590/2175-7860201566411.",
        "BRANCALION, P. H. S. et al. Global restoration opportunities in tropical rainforest landscapes. **Science Advances**, v. 5, n. 7, p. eaav3223, 2019. DOI: https://doi.org/10.1126/sciadv.aav3223.",
        "BURKE, R. Hybrid Recommender Systems: Survey and Experiments. **User Modeling and User-Adapted Interaction**, v. 12, n. 4, p. 331-370, 2002. DOI: https://doi.org/10.1023/A:1021240730564.",
        "CHAZDON, R. L. **Second growth: the promise of tropical forest regeneration in an age of deforestation**. Chicago: University of Chicago Press, 2014.",
        "CREMONESI, P.; KOREN, Y.; TURRIN, R. Performance of recommender algorithms on top-n recommendation tasks. In: ACM CONFERENCE ON RECOMMENDER SYSTEMS (RecSys), 4., 2010, Barcelona. **Proceedings...** New York: ACM, 2010. p. 39-46. DOI: https://doi.org/10.1145/1864708.1864721.",
        "CROUZEILLES, R. et al. Achieving cost-effective Amazon forest restoration through socially-inclusive and biodiversity-informed spatial prioritization. **Forest Ecology and Management**, v. 465, p. 118098, 2020. DOI: https://doi.org/10.1016/j.foreco.2020.118098.",
        "GBIF - GLOBAL BIODIVERSITY INFORMATION FACILITY. **GBIF Occurrence Data**. Copenhague: GBIF, 2026. Disponível em: https://www.gbif.org. Acesso em: 26 set. 2026.",
        "GRINNELL, J. The niche-relationships of the California Thrasher. **The Auk**, v. 34, n. 4, p. 427-433, 1917. DOI: https://doi.org/10.2307/4072271.",
        "HE, X. et al. Neural Collaborative Filtering. In: INTERNATIONAL CONFERENCE ON WORLD WIDE WEB (WWW), 26., 2017, Perth. **Proceedings...** New York: ACM, 2017. p. 173-182. DOI: https://doi.org/10.1145/3038912.3052569.",
        "HU, Y.; KOREN, Y.; VOLINSKY, C. Collaborative Filtering for Implicit Feedback Datasets. In: IEEE INTERNATIONAL CONFERENCE ON DATA MINING (ICDM), 8., 2008, Pisa. **Proceedings...** Pisa: IEEE, 2008. p. 263-272. DOI: https://doi.org/10.1109/ICDM.2008.22.",
        "HUTCHINSON, G. E. Concluding remarks. **Cold Spring Harbor Symposia on Quantitative Biology**, v. 22, p. 415-427, 1957. DOI: https://doi.org/10.1101/SQB.1957.022.01.039.",
        "JÄRVELIN, K.; KEKÄLÄINEN, J. Cumulated gain-based evaluation of retrieval techniques. **ACM Transactions on Information Systems**, v. 20, n. 4, p. 422-446, 2002. DOI: https://doi.org/10.1145/582415.582418.",
        "JBRJ - JARDIM BOTÂNICO DO RIO DE JANEIRO. **Flora e Funga do Brasil**. Rio de Janeiro: JBRJ, 2026. Disponível em: http://floradobrasil.jbrj.gov.br/. Acesso em: 26 set. 2026.",
        "KOREN, Y.; BELL, R.; VOLINSKY, C. Matrix Factorization Techniques for Recommender Systems. **Computer**, v. 42, n. 8, p. 30-37, 2009. DOI: https://doi.org/10.1109/MC.2009.263.",
        "KUNAVER, M.; POŽRL, T. Diversity in recommender systems: A survey. **Knowledge-Based Systems**, v. 123, p. 154-162, 2017. DOI: https://doi.org/10.1016/j.knosys.2017.02.009.",
        "LEGENDRE, P.; LEGENDRE, L. **Numerical Ecology**. 3. ed. Amsterdam: Elsevier, 2012.",
        "LOPS, P.; DE GEMMIS, M.; SEMERARO, G. Content-based Recommender Systems: State of the Art and Trends. In: RICCI, F.; ROKACH, L.; SHAPIRA, B.; KANTOR, P. (org.). **Recommender Systems Handbook**. Boston: Springer, 2011. p. 73-105. DOI: https://doi.org/10.1007/978-0-387-85820-3_3.",
        "MANNING, C. D.; RAGHAVAN, P.; SCHÜTZE, H. **Introduction to Information Retrieval**. Cambridge: Cambridge University Press, 2008. DOI: https://doi.org/10.1017/CBO9780511809071.",
        "MEYER, C.; KREFT, H.; GURNEY, R.; JETZ, W. Global priorities for an effective information basis of biodiversity distributions. **Nature Communications**, v. 6, n. 8221, p. 1-8, 2015. DOI: https://doi.org/10.1038/ncomms9221.",
        "RENDLE, S. et al. Neural Collaborative Filtering vs. Matrix Factorization Revisited. In: ACM CONFERENCE ON RECOMMENDER SYSTEMS (RecSys), 14., 2020, Virtual Event. **Proceedings...** New York: ACM, 2020. p. 240-248. DOI: https://doi.org/10.1145/3383313.3412488.",
        "RICCI, F.; ROKACH, L.; SHAPIRA, B. Introduction to Recommender Systems Handbook. In: RICCI, F.; ROKACH, L.; SHAPIRA, B.; KANTOR, P. (org.). **Recommender Systems Handbook**. Boston: Springer, 2011. p. 1-35. DOI: https://doi.org/10.1007/978-0-387-85820-3_1.",
        "SALTON, G.; MCGILL, M. J. **Introduction to Modern Information Retrieval**. New York: McGraw-Hill, 1983.",
        "SFB - SERVIÇO FLORESTAL BRASILEIRO. **Inventário Florestal Nacional: dados biofísicos e socioambientais**. Brasília: MAPA, 2025. Disponível em: https://dados.florestal.gov.br/. Acesso em: 26 set. 2026.",
        "SOBERÓN, J. Grinnellian and Eltonian niches and geographic distributions of species. **Ecology Letters**, v. 10, n. 12, p. 1115-1123, 2007. DOI: https://doi.org/10.1111/j.1461-0248.2007.01107.x.",
        "STEEN, V. A. et al. Spatial thinning reduces spatial autocorrelation and increases model performance in species distribution modeling. **Ecological Informatics**, v. 65, p. 101402, 2021. DOI: https://doi.org/10.1016/j.ecoinf.2021.101402.",
        "STRASSBURG, B. B. N. et al. Global priority areas for ecosystem restoration. **Nature**, v. 586, p. 724-729, 2020. DOI: https://doi.org/10.1038/s41586-020-2784-9.",
        "STUBBLEFIELD, M. et al. Machine learning approaches to predict tree seedling survival in ecological restoration. **Restoration Ecology**, v. 31, n. 4, p. e13880, 2023. DOI: https://doi.org/10.1111/rec.13880.",
        "ZIEGLER, C.-N. et al. Improving recommendation lists through topic diversification. In: INTERNATIONAL CONFERENCE ON WORLD WIDE WEB (WWW), 14., 2005, Chiba. **Proceedings...** New York: ACM, 2005. p. 22-32. DOI: https://doi.org/10.1145/1060745.1060754.",
        "ZIZKA, A. et al. CoordinateCleaner: Standardized cleaning of occurrence data from biodiversity databases. **Methods in Ecology and Evolution**, v. 10, n. 5, p. 744-751, 2019. DOI: https://doi.org/10.1111/2041-210X.13152."
    ]

    for ref in referencias:
        p_ref = doc.add_paragraph()
        p_ref.alignment = WD_ALIGN_PARAGRAPH.LEFT
        p_ref.paragraph_format.line_spacing = 1.0
        p_ref.paragraph_format.space_before = Pt(0)
        p_ref.paragraph_format.space_after = Pt(6)
        p_ref.paragraph_format.first_line_indent = Cm(0)
        runs_info = parse_runs(ref)
        for txt, b, it in runs_info:
            r = p_ref.add_run(txt)
            r.bold = b
            r.italic = it
            r.font.name = 'Arial'
            r.font.size = Pt(12)

    return doc


if __name__ == '__main__':
    doc = build_etapa3_docx()
    out_dir = r"c:\Random\Aulas\Matérias\4º Semestre\Projeto aplicado 3\Etapa 3"
    target_file = os.path.join(out_dir, "Etapa 3 - ABNT.docx")
    doc.save(target_file)
    print(f"Documento ABNT compilado com sucesso em: {target_file}")

    # Cópia para o repositório clonado ProjetoAplicado3/Etapa 3/
    repo_etapa3 = r"c:\Random\Aulas\Matérias\4º Semestre\Projeto aplicado 3\ProjetoAplicado3\Etapa 3"
    os.makedirs(repo_etapa3, exist_ok=True)
    repo_target = os.path.join(repo_etapa3, "Etapa 3 - ABNT.docx")
    shutil.copy2(target_file, repo_target)
    print(f"Cópia sincronizada para o repositório em: {repo_target}")
