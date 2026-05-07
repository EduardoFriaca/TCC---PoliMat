# Eduaro Honorio Friaca    RA: 10408959

from __future__ import annotations

import argparse
import re
import sys
from typing import Dict, List, Tuple

try:
    import sympy as sp
    from sympy.parsing.sympy_parser import (
        parse_expr,
        standard_transformations,
        implicit_multiplication_application,
        convert_xor,
    )
except Exception:
    print("Erro: É necessário instalar o pacote 'sympy'. Use: pip install sympy")
    sys.exit(1)


# -------------------------------
# Utilidades de parsing e validação
# -------------------------------

MAPA_SUPER = {
    "0": "⁰", "1": "¹", "2": "²", "3": "³", "4": "⁴",
    "5": "⁵", "6": "⁶", "7": "⁷", "8": "⁸", "9": "⁹"
}

MAPA_SUPER_INVERSO = {
    "⁰": "^0", "¹": "^1", "²": "^2", "³": "^3", "⁴": "^4",
    "⁵": "^5", "⁶": "^6", "⁷": "^7", "⁸": "^8", "⁹": "^9"
}


def normalizar_expressao(texto: str) -> str:
    if texto is None:
        raise ValueError("Expressão vazia.")

    t = texto.strip()

    # Converte números pequenos para potência.
    # Exemplo: x² vira x^2
    for super_num, potencia in MAPA_SUPER_INVERSO.items():
        t = t.replace(super_num, potencia)

    return t


def criar_variaveis(lista_variaveis: List[str]) -> Tuple[List[sp.Symbol], Dict[str, sp.Symbol]]:
    simbolos = [sp.Symbol(v) for v in lista_variaveis]
    mapa = {v: s for v, s in zip(lista_variaveis, simbolos)}
    return simbolos, mapa


def interpretar_atribuicoes(texto: str, mapa_simbolos: Dict[str, sp.Symbol]) -> Dict[sp.Symbol, float]:
    if not texto:
        return {}

    pares = [p.strip() for p in texto.replace(";", ",").split(",") if p.strip()]
    result: Dict[sp.Symbol, float] = {}

    for par in pares:
        if "=" not in par:
            raise ValueError(f"Atribuição inválida: '{par}'. Use o formato nome=valor.")

        nome, valor = [t.strip() for t in par.split("=", 1)]

        if nome not in mapa_simbolos:
            raise ValueError(f"Variável '{nome}' não reconhecida.")

        try:
            result[mapa_simbolos[nome]] = float(valor)
        except ValueError:
            raise ValueError(f"Valor inválido para '{nome}': '{valor}'. Use números reais.")

    return result


def ler_expressao(expr_txt: str, variaveis: List[str]) -> sp.Expr:
    """
    Parser amigável para Ensino Médio:
    - aceita 2x, xy, 2xy, (x+1)(x-1)
    - aceita ^ como potência
    - aceita números pequenos: x², x³, x⁴...
    - aceita múltiplas variáveis, se declaradas no campo variáveis
    """
    expr_txt = normalizar_expressao(expr_txt)
    _, mapa = criar_variaveis(variaveis)

    transformations = standard_transformations + (
        implicit_multiplication_application,
        convert_xor,
    )

    try:
        expr = parse_expr(
            expr_txt,
            local_dict=mapa,
            transformations=transformations,
            evaluate=True
        )
    except Exception as e:
        raise ValueError(f"Não foi possível interpretar a expressão: {e}")

    return expr


# -------------------------------
# Formatação para linguagem escolar
# -------------------------------

def formatar_expressao_aluno(expr) -> str:
    """
    Converte saída do SymPy para uma forma mais próxima do caderno.
    Exemplo:
    x**2 + 2*x + 1 -> x² + 2x + 1
    """
    try:
        texto = sp.sstr(expr)
    except Exception:
        texto = str(expr)

    def trocar_potencia(match):
        expoente = match.group(1)
        return "".join(MAPA_SUPER.get(c, c) for c in expoente)

    # x**2 -> x²
    texto = re.sub(r"\*\*(\d+)", trocar_potencia, texto)

    # 2*x -> 2x
    # x*y -> xy
    # (x+1)*(x-1) -> (x+1)(x-1)
    texto = re.sub(r"(?<=[0-9a-zA-Z\)])\*(?=[a-zA-Z\(])", "", texto)

    # I -> i
    texto = texto.replace("I", "i")

    return texto


def formatar_valor(valor) -> str:
    try:
        valor_float = float(valor)
        if valor_float.is_integer():
            return str(int(valor_float))
        return str(valor_float)
    except Exception:
        return str(valor)


def formatar_aproximacao(valor) -> str:
    try:
        z = complex(sp.N(valor, 6))
        real = z.real
        imag = z.imag

        def fmt(n: float) -> str:
            s = f"{n:.4f}".rstrip("0").rstrip(".")
            if s == "-0":
                s = "0"
            return s

        if abs(imag) < 1e-10:
            return fmt(real)

        if abs(real) < 1e-10:
            return f"{fmt(imag)}i"

        sinal = "+" if imag >= 0 else "-"
        return f"{fmt(real)} {sinal} {fmt(abs(imag))}i"

    except Exception:
        return str(valor)


def mesma_forma_visual(a, b) -> bool:
    """
    Verifica se a forma escrita é igual.
    Importante: isso é diferente de verificar equivalência matemática.
    Exemplo: (x+1)(x+1) e x²+2x+1 são equivalentes,
    mas não têm a mesma forma visual.
    """
    try:
        return sp.sstr(a) == sp.sstr(b)
    except Exception:
        return str(a) == str(b)


def mesma_expressao(a, b) -> bool:
    try:
        return sp.simplify(a - b) == 0
    except Exception:
        return sp.sstr(a) == sp.sstr(b)


def formatar_fator_linear(variavel: sp.Symbol, raiz) -> str:
    """
    Monta fatores do tipo:
    raiz = -1 -> (x + 1)
    raiz = 3  -> (x - 3)
    raiz = 0  -> x
    """
    raiz = sp.simplify(raiz)

    if raiz == 0:
        return f"{variavel}"

    try:
        if raiz.is_number and raiz < 0:
            return f"({variavel} + {formatar_expressao_aluno(abs(raiz))})"
    except Exception:
        pass

    return f"({variavel} - {formatar_expressao_aluno(raiz)})"


def formatar_expr_com_substituicoes(expr: sp.Expr, atribuicoes: Dict[sp.Symbol, float]) -> str:
    """
    Monta uma forma didática da expressão com os valores substituídos.
    Exemplo:
    x² + 2xy + y², com x=2 e y=2
    vira:
    (2)² + 2(2)(2) + (2)²
    """
    texto = formatar_expressao_aluno(expr)

    # troca variáveis maiores primeiro, para evitar conflitos
    itens = sorted(atribuicoes.items(), key=lambda item: len(str(item[0])), reverse=True)

    for var, valor in itens:
        nome = str(var)
        valor_txt = f"({formatar_valor(valor)})"
        texto = texto.replace(nome, valor_txt)

    return texto


def montar_distributiva(expr: sp.Expr) -> str:
    """
    Tenta montar uma etapa intermediária de distributiva para produtos de parênteses.
    Exemplo:
    (x + 2)(x² - 9)
    vira:
    (x)(x²) + (x)(-9) + (2)(x²) + (2)(-9)
    """
    try:
        fatores = list(sp.Mul.make_args(expr))
        fatores_com_soma = [f for f in fatores if isinstance(f, sp.Add)]

        if len(fatores_com_soma) < 2:
            return ""

        a = fatores_com_soma[0]
        b = fatores_com_soma[1]

        outros = [f for f in fatores if f not in [a, b]]

        termos = []
        for termo_a in a.as_ordered_terms():
            for termo_b in b.as_ordered_terms():
                if outros:
                    prefixo = "".join(f"({formatar_expressao_aluno(o)})" for o in outros)
                else:
                    prefixo = ""
                termos.append(
                    f"{prefixo}({formatar_expressao_aluno(termo_a)})({formatar_expressao_aluno(termo_b)})"
                )

        return " + ".join(termos)

    except Exception:
        return ""


# -------------------------------
# Operações principais
# -------------------------------

def simplificar(expr: sp.Expr) -> sp.Expr:
    return sp.simplify(expr)


def fatorar(expr: sp.Expr) -> sp.Expr:
    try:
        return sp.factor(expr)
    except Exception:
        return expr


def expandir(expr: sp.Expr) -> sp.Expr:
    return sp.expand(expr)


def coletar_termos(expr: sp.Expr, variavel: sp.Symbol) -> sp.Expr:
    return sp.collect(sp.expand(expr), variavel)


def avaliar(expr: sp.Expr, atribuicoes: Dict[sp.Symbol, float]) -> float:
    if not atribuicoes:
        raise ValueError("É necessário fornecer pelo menos uma atribuição.")
    return float(expr.evalf(subs=atribuicoes))


def raizes(expr: sp.Expr, variavel: sp.Symbol) -> List:
    """
    Retorna raízes:
    - para polinômios tenta solução simbólica;
    - se necessário, tenta solução numérica.
    """
    try:
        if expr.is_polynomial(variavel):
            sols = sp.solve(sp.Eq(expr, 0), variavel)
            if not sols:
                try:
                    nr = sp.nroots(expr)
                    return [complex(r) for r in nr]
                except Exception:
                    return []
            return sols
        else:
            sols = sp.solveset(sp.Eq(expr, 0), variavel, domain=sp.S.Complexes)
            try:
                return list(sols)
            except Exception:
                return [sols]
    except Exception:
        try:
            return [complex(r) for r in sp.nroots(sp.expand(expr))]
        except Exception:
            raise


# -------------------------------
# Passo a passo por operação
# -------------------------------

def passos_simplificar(expr: sp.Expr) -> str:
    resultado = simplificar(expr)

    linhas = []
    linhas.append("PASSO A PASSO — SIMPLIFICAÇÃO\n")
    linhas.append(f"Expressão inicial:\n{formatar_expressao_aluno(expr)}\n")

    linhas.append("1º passo: verificar se há parênteses, produtos ou termos semelhantes.")
    linhas.append("2º passo: aplicar as propriedades algébricas para deixar a expressão em uma forma mais simples.")

    if mesma_forma_visual(expr, resultado):
        linhas.append("\nNeste caso, o sistema não encontrou uma redução algébrica mais simples.")
        linhas.append("A expressão já está organizada para a operação escolhida.")
    else:
        linhas.append(f"\nForma simplificada encontrada:\n{formatar_expressao_aluno(resultado)}")

    linhas.append(f"\nResultado final:\n{formatar_expressao_aluno(resultado)}")
    return "\n".join(linhas)


def passos_expandir(expr: sp.Expr) -> str:
    resultado = expandir(expr)
    intermediaria = montar_distributiva(expr)

    linhas = []
    linhas.append("PASSO A PASSO — EXPANSÃO\n")
    linhas.append(f"Expressão inicial:\n{formatar_expressao_aluno(expr)}\n")

    linhas.append("1º passo: identificar se existem parênteses, produtos ou potências.")
    linhas.append("2º passo: aplicar a propriedade distributiva.")

    if intermediaria:
        linhas.append("\nDistribuindo os termos:")
        linhas.append(intermediaria)

    if mesma_forma_visual(expr, resultado):
        linhas.append("\n3º passo: a expressão já estava expandida, ou seja, não havia parênteses para distribuir.")
    else:
        linhas.append("\n3º passo: multiplicar os termos e juntar os termos semelhantes.")
        linhas.append(f"Após a expansão:\n{formatar_expressao_aluno(resultado)}")

    linhas.append(f"\nResultado final:\n{formatar_expressao_aluno(resultado)}")
    return "\n".join(linhas)


def passos_coletar_termos(expr: sp.Expr, variavel: sp.Symbol) -> str:
    expandida = expandir(expr)
    resultado = coletar_termos(expr, variavel)

    linhas = []
    linhas.append("PASSO A PASSO — COLETA DE TERMOS\n")
    linhas.append(f"Expressão inicial:\n{formatar_expressao_aluno(expr)}\n")

    linhas.append("1º passo: expandir a expressão, caso existam parênteses ou produtos.")
    linhas.append(f"Forma expandida:\n{formatar_expressao_aluno(expandida)}\n")

    linhas.append(f"2º passo: agrupar os termos que possuem a variável {variavel}.")
    linhas.append("3º passo: organizar a expressão por potências da variável principal.")

    linhas.append(f"\nResultado final:\n{formatar_expressao_aluno(resultado)}")
    return "\n".join(linhas)


def passos_avaliar(expr: sp.Expr, atribuicoes: Dict[sp.Symbol, float]) -> str:
    if not atribuicoes:
        raise ValueError("É necessário fornecer pelo menos uma atribuição.")

    resultado = avaliar(expr, atribuicoes)
    expr_substituida_texto = formatar_expr_com_substituicoes(expr, atribuicoes)

    valores_txt = []
    for var, val in atribuicoes.items():
        valores_txt.append(f"{var} = {formatar_valor(val)}")

    linhas = []
    linhas.append("PASSO A PASSO — AVALIAÇÃO NUMÉRICA\n")
    linhas.append(f"Expressão inicial:\n{formatar_expressao_aluno(expr)}\n")

    linhas.append("1º passo: identificar os valores informados para cada variável.")
    linhas.append("Valores usados:")
    linhas.append(", ".join(valores_txt))

    linhas.append("\n2º passo: substituir as variáveis na expressão.")
    linhas.append(f"{formatar_expressao_aluno(expr)}")
    linhas.append(f"→ {expr_substituida_texto}")

    linhas.append("\n3º passo: calcular o valor numérico da expressão.")
    linhas.append(f"Resultado do cálculo: {formatar_valor(resultado)}")

    linhas.append(f"\nResultado final:\n{formatar_valor(resultado)}")
    return "\n".join(linhas)


def passos_raizes(expr: sp.Expr, variavel: sp.Symbol) -> str:
    linhas = []
    linhas.append("PASSO A PASSO — RAÍZES\n")
    linhas.append(f"Expressão inicial:\n{formatar_expressao_aluno(expr)}")
    linhas.append("Queremos resolver:")
    linhas.append(f"{formatar_expressao_aluno(expr)} = 0\n")

    try:
        pol = sp.Poly(expr, variavel)
        grau = pol.degree()

        if grau == 1:
            a, b = pol.all_coeffs()
            raiz = sp.simplify(-b / a)

            linhas.append("1º passo: identificar uma equação do 1º grau.")
            linhas.append("Forma geral: ax + b = 0")
            linhas.append(f"a = {formatar_expressao_aluno(a)}")
            linhas.append(f"b = {formatar_expressao_aluno(b)}\n")
            linhas.append("2º passo: usar x = -b/a.")
            linhas.append(f"x = -({formatar_expressao_aluno(b)}) / {formatar_expressao_aluno(a)}")
            linhas.append(f"\nResultado final:\nx = {formatar_expressao_aluno(raiz)}")
            return "\n".join(linhas)

        if grau == 2:
            a, b, c = pol.all_coeffs()
            delta = sp.simplify(b**2 - 4*a*c)

            x1 = sp.simplify((-b + sp.sqrt(delta)) / (2*a))
            x2 = sp.simplify((-b - sp.sqrt(delta)) / (2*a))

            linhas.append("1º passo: identificar os coeficientes da equação ax² + bx + c = 0.")
            linhas.append(f"a = {formatar_expressao_aluno(a)}")
            linhas.append(f"b = {formatar_expressao_aluno(b)}")
            linhas.append(f"c = {formatar_expressao_aluno(c)}\n")

            linhas.append("2º passo: calcular o discriminante Δ.")
            linhas.append("Δ = b² - 4ac")
            linhas.append(
                f"Δ = ({formatar_expressao_aluno(b)})² - 4·({formatar_expressao_aluno(a)})·({formatar_expressao_aluno(c)})"
            )
            linhas.append(f"Δ = {formatar_expressao_aluno(delta)}\n")

            linhas.append("3º passo: aplicar a fórmula de Bhaskara.")
            linhas.append("x = (-b ± √Δ) / 2a")
            linhas.append(f"x1 = {formatar_expressao_aluno(x1)}")
            linhas.append(f"x2 = {formatar_expressao_aluno(x2)}")

            try:
                if delta.is_number and delta < 0:
                    linhas.append("\nComo Δ é negativo, as raízes não são reais.")
                    linhas.append("O sistema apresenta as raízes complexas.")
            except Exception:
                pass

            linhas.append(f"\nAproximação de x1: {formatar_aproximacao(x1)}")
            linhas.append(f"Aproximação de x2: {formatar_aproximacao(x2)}")

            return "\n".join(linhas)

        solucoes = raizes(expr, variavel)

        linhas.append(f"1º passo: identificar que o polinômio tem grau {grau}.")
        linhas.append("2º passo: calcular as raízes com apoio do sistema.")

        if isinstance(solucoes, (list, tuple)):
            for i, r in enumerate(solucoes, start=1):
                linhas.append(f"Raiz {i}: {formatar_expressao_aluno(r)}")
                linhas.append(f"Aproximação: {formatar_aproximacao(r)}")
        else:
            linhas.append(formatar_expressao_aluno(solucoes))

        return "\n".join(linhas)

    except Exception:
        solucoes = raizes(expr, variavel)
        linhas.append("O sistema calculou as raízes pelo método algébrico/computacional.")

        if isinstance(solucoes, (list, tuple)):
            for i, r in enumerate(solucoes, start=1):
                linhas.append(f"Raiz {i}: {formatar_expressao_aluno(r)}")
        else:
            linhas.append(formatar_expressao_aluno(solucoes))

        return "\n".join(linhas)


def passos_fatorar(expr: sp.Expr, variavel: sp.Symbol) -> str:
    fatorada = fatorar(expr)

    linhas = []
    linhas.append("PASSO A PASSO — FATORAÇÃO\n")
    linhas.append(f"Expressão inicial:\n{formatar_expressao_aluno(expr)}\n")

    try:
        pol = sp.Poly(expr, variavel)
        grau = pol.degree()

        if grau == 2:
            a, b, c = pol.all_coeffs()
            delta = sp.simplify(b**2 - 4*a*c)

            x1 = sp.simplify((-b + sp.sqrt(delta)) / (2*a))
            x2 = sp.simplify((-b - sp.sqrt(delta)) / (2*a))

            linhas.append("1º passo: encontrar as raízes da equação.")
            linhas.append("Forma geral: ax² + bx + c = 0")
            linhas.append(f"a = {formatar_expressao_aluno(a)}")
            linhas.append(f"b = {formatar_expressao_aluno(b)}")
            linhas.append(f"c = {formatar_expressao_aluno(c)}\n")

            linhas.append("2º passo: calcular Δ = b² - 4ac.")
            linhas.append(
                f"Δ = ({formatar_expressao_aluno(b)})² - 4·({formatar_expressao_aluno(a)})·({formatar_expressao_aluno(c)})"
            )
            linhas.append(f"Δ = {formatar_expressao_aluno(delta)}\n")

            linhas.append("3º passo: aplicar Bhaskara.")
            linhas.append("x = (-b ± √Δ) / 2a")
            linhas.append(f"x1 = {formatar_expressao_aluno(x1)}")
            linhas.append(f"x2 = {formatar_expressao_aluno(x2)}\n")

            try:
                if delta.is_number and delta < 0:
                    linhas.append("Como Δ é negativo, não há fatoração simples usando raízes reais.")
                    linhas.append("\nResultado final:")
                    linhas.append("Não há fatoração simples nos reais.")
                    return "\n".join(linhas)
            except Exception:
                pass

            linhas.append("4º passo: colocar na forma fatorada.")
            linhas.append("Quando conhecemos as raízes, usamos:")
            linhas.append("a(x - x1)(x - x2)\n")

            fator1 = formatar_fator_linear(variavel, x1)
            fator2 = formatar_fator_linear(variavel, x2)

            if a == 1:
                forma_pelas_raizes = f"{fator1}{fator2}"
            else:
                forma_pelas_raizes = f"{formatar_expressao_aluno(a)}{fator1}{fator2}"

            linhas.append(forma_pelas_raizes)
            linhas.append(f"\nResultado final:\n{formatar_expressao_aluno(fatorada)}")

            return "\n".join(linhas)

        linhas.append("1º passo: procurar fator comum, produtos notáveis ou raízes do polinômio.")

        if mesma_forma_visual(expr, fatorada):
            linhas.append("2º passo: não foi encontrada uma fatoração simples nos números racionais.")
            linhas.append(f"\nResultado final:\n{formatar_expressao_aluno(expr)}")
        else:
            linhas.append("2º passo: aplicar a fatoração encontrada.")
            linhas.append(f"\nResultado final:\n{formatar_expressao_aluno(fatorada)}")

        return "\n".join(linhas)

    except Exception:
        linhas.append("1º passo: tentar aplicar uma fatoração algébrica.")

        if mesma_forma_visual(expr, fatorada):
            linhas.append("2º passo: não foi encontrada uma fatoração simples.")
            linhas.append(f"\nResultado final:\n{formatar_expressao_aluno(expr)}")
        else:
            linhas.append(f"2º passo: fatoração encontrada:\n{formatar_expressao_aluno(fatorada)}")

        return "\n".join(linhas)


def mostrar_etapas_texto(expr: sp.Expr, variavel: sp.Symbol) -> str:
    etapa_expandir = expandir(expr)
    etapa_coletar = coletar_termos(etapa_expandir, variavel)
    etapa_fatorar = fatorar(etapa_coletar)
    etapa_simplificar = simplificar(etapa_fatorar)

    linhas = []
    linhas.append("ETAPAS GERAIS DA EXPRESSÃO\n")
    linhas.append(f"Etapa 1 — Expressão inicial:\n{formatar_expressao_aluno(expr)}\n")
    linhas.append(f"Etapa 2 — Expandir:\n{formatar_expressao_aluno(etapa_expandir)}\n")
    linhas.append(f"Etapa 3 — Coletar termos:\n{formatar_expressao_aluno(etapa_coletar)}\n")
    linhas.append(f"Etapa 4 — Fatorar:\n{formatar_expressao_aluno(etapa_fatorar)}\n")
    linhas.append(f"Etapa 5 — Simplificar:\n{formatar_expressao_aluno(etapa_simplificar)}")

    return "\n".join(linhas)


RESUMO_TCC = """
Resumo (versão curta):
Este protótipo é uma aplicação e projeto sobre a modernização do ensino de álgebra no Ensino Médio por meio da
automatização de manipulações algébricas com programação (Python + SymPy).
""".strip()


def passos_resumo(expr: sp.Expr, variavel: sp.Symbol) -> str:
    linhas = []
    linhas.append("RESUMO DAS OPERAÇÕES\n")
    linhas.append(f"Expressão inicial:\n{formatar_expressao_aluno(expr)}\n")

    linhas.append("1) Simplificação:")
    linhas.append(formatar_expressao_aluno(simplificar(expr)))
    linhas.append("")

    f = fatorar(expr)
    linhas.append("2) Fatoração:")
    if mesma_forma_visual(expr, f):
        linhas.append("Não há fatoração simples nos números racionais.")
    else:
        linhas.append(formatar_expressao_aluno(f))
    linhas.append("")

    linhas.append("3) Expansão:")
    linhas.append(formatar_expressao_aluno(expandir(expr)))
    linhas.append("")

    linhas.append("4) Coleta de termos:")
    linhas.append(formatar_expressao_aluno(coletar_termos(expr, variavel)))
    linhas.append("")

    linhas.append("5) Raízes:")
    rr = raizes(expr, variavel)
    if isinstance(rr, (list, tuple)):
        for i, r in enumerate(rr, start=1):
            linhas.append(f"Raiz {i}: {formatar_expressao_aluno(r)}")
            linhas.append(f"Aproximação: {formatar_aproximacao(r)}")
    else:
        linhas.append(formatar_expressao_aluno(rr))

    linhas.append("")
    linhas.append("Resumo do TCC:")
    linhas.append(RESUMO_TCC)

    return "\n".join(linhas)


def executar_operacao_com_passos(
    acao: str,
    expr: sp.Expr,
    variavel: sp.Symbol,
    atribuicoes: Dict[sp.Symbol, float] | None = None
) -> str:
    acao = acao.strip().lower()

    if acao == "simplificar":
        return passos_simplificar(expr)

    if acao == "fatorar":
        return passos_fatorar(expr, variavel)

    if acao == "expandir":
        return passos_expandir(expr)

    if acao == "coletar termos":
        return passos_coletar_termos(expr, variavel)

    if acao == "avaliar numericamente":
        if atribuicoes is None:
            atribuicoes = {}
        return passos_avaliar(expr, atribuicoes)

    if acao in {"raízes (resolver expr=0)", "raizes (resolver expr=0)", "raízes", "raizes"}:
        return passos_raizes(expr, variavel)

    if acao == "etapas (sequência didática)":
        return mostrar_etapas_texto(expr, variavel)

    if acao == "resumo do projeto (todas as operações)":
        return passos_resumo(expr, variavel)

    raise ValueError("Operação não reconhecida.")


def mostrar_etapas(expr: sp.Expr, variavel: sp.Symbol) -> None:
    print(mostrar_etapas_texto(expr, variavel))


def mini_menu() -> None:
    expr = None
    variaveis: List[str] | None = None
    simbolos = None
    mapa = None
    var_principal = None

    while True:
        print("\n=== Protótipo: Manipulação de Polinômios (Python + SymPy) ===")
        print("1) Digitar/Alterar expressão")
        print("2) Simplificar com passo a passo")
        print("3) Fatorar com passo a passo")
        print("4) Expandir com passo a passo")
        print("5) Coletar termos com passo a passo")
        print("6) Avaliar numericamente com passo a passo")
        print("7) Raízes com passo a passo")
        print("8) Etapas gerais")
        print("0) Resumo do projeto")
        print("q) Sair")

        op = input("\nEscolha uma opção: ").strip().lower()

        if op == "q":
            print("Até logo!")
            return

        if op not in {"0", "1", "2", "3", "4", "5", "6", "7", "8"}:
            print("Opção inválida.")
            continue

        if op == "1":
            try:
                expr_txt = input("Digite a expressão (pode usar x², x³, 2x, xy, etc.): ").strip()
                variaveis_txt = input("Variáveis (ex.: x ou x,y) [padrão: x]: ").strip() or "x"
                variaveis = [v.strip() for v in variaveis_txt.split(",") if v.strip()]
                simbolos, mapa = criar_variaveis(variaveis)
                expr = ler_expressao(expr_txt, variaveis)
                var_principal = simbolos[0]
                print("Expressão armazenada com sucesso!")
            except Exception as e:
                print("Erro ao ler expressão:", e)
            continue

        if expr is None:
            print("Primeiro digite/alterar a expressão (opção 1).")
            continue

        try:
            if op == "2":
                print(passos_simplificar(expr))

            elif op == "3":
                print(passos_fatorar(expr, var_principal))

            elif op == "4":
                print(passos_expandir(expr))

            elif op == "5":
                print(passos_coletar_termos(expr, var_principal))

            elif op == "6":
                valores = input("Atribuições (ex.: x=2, y=1.5): ").strip()
                atribuicoes = interpretar_atribuicoes(valores, mapa)
                print(passos_avaliar(expr, atribuicoes))

            elif op == "7":
                print(passos_raizes(expr, var_principal))

            elif op == "8":
                print(mostrar_etapas_texto(expr, var_principal))

            elif op == "0":
                print(passos_resumo(expr, var_principal))

        except Exception as e:
            print("Ocorreu um erro:", e)


def construir_argumentos() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="tcc_algebra_polinomios",
        description="Protótipo educacional de manipulação de polinômios (Python + SymPy)"
    )
    parser.add_argument(
        "--acao",
        choices=["simplificar", "fatorar", "expandir", "coletar", "avaliar", "raizes", "etapas", "resumo", "menu"],
        help="Ação a executar. Sem argumentos, abre o mini-menu interativo."
    )
    parser.add_argument("--expr", help="Expressão algébrica (pode usar x², x³, 2x, xy).")
    parser.add_argument("--variavel", default="x", help="Variável principal (padrão: x). Pode ser x,y")
    parser.add_argument("--valores", default="", help="Atribuições para avaliação, ex.: x=2, y=1.5")
    return parser.parse_args()


def main():
    args = construir_argumentos()

    if not args.acao:
        mini_menu()
        return

    if args.acao == "resumo":
        print(RESUMO_TCC)
        return

    variaveis = [v.strip() for v in (args.variavel or "x").split(",") if v.strip()]
    simbolos, mapa = criar_variaveis(variaveis)
    var_principal = simbolos[0]

    if args.acao not in {"resumo", "menu"}:
        if not args.expr:
            print("Erro: forneça --expr para esta ação.")
            sys.exit(2)
        expr = ler_expressao(args.expr, variaveis)

    try:
        if args.acao == "simplificar":
            print(passos_simplificar(expr))

        elif args.acao == "fatorar":
            print(passos_fatorar(expr, var_principal))

        elif args.acao == "expandir":
            print(passos_expandir(expr))

        elif args.acao == "coletar":
            print(passos_coletar_termos(expr, var_principal))

        elif args.acao == "avaliar":
            atribuicoes = interpretar_atribuicoes(args.valores, mapa)
            print(passos_avaliar(expr, atribuicoes))

        elif args.acao == "raizes":
            print(passos_raizes(expr, var_principal))

        elif args.acao == "etapas":
            print(mostrar_etapas_texto(expr, var_principal))

        elif args.acao == "menu":
            mini_menu()

    except Exception as e:
        print("Erro durante a operação:", e)
        sys.exit(1)


if __name__ == "__main__":
    main()