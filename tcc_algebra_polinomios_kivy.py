# tcc_algebra_polinomios_kivy.py
# Frontend Kivy para o sistema de polinômios com passo a passo

from __future__ import annotations

import traceback

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Color, RoundedRectangle
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.spinner import Spinner
from kivy.uix.textinput import TextInput

import tcc_algebra_polinomios as be


# -------------------------------
# Aparência geral
# -------------------------------

Window.size = (1280, 820)
Window.clearcolor = (0.95, 0.96, 0.98, 1)


MAPA_SUPER = {
    "0": "⁰", "1": "¹", "2": "²", "3": "³", "4": "⁴",
    "5": "⁵", "6": "⁶", "7": "⁷", "8": "⁸", "9": "⁹"
}


def para_superescrito(numero: str) -> str:
    saida = ""
    for c in numero:
        if c in MAPA_SUPER:
            saida += MAPA_SUPER[c]
        else:
            return ""
    return saida


class Painel(BoxLayout):
    def __init__(self, cor=(1, 1, 1, 1), raio=12, **kwargs):
        super().__init__(**kwargs)
        self.cor = cor
        self.raio = raio

        with self.canvas.before:
            Color(*self.cor)
            self._bg = RoundedRectangle(pos=self.pos, size=self.size, radius=[self.raio])

        self.bind(pos=self._atualizar_bg, size=self._atualizar_bg)

    def _atualizar_bg(self, *args):
        self._bg.pos = self.pos
        self._bg.size = self.size


class BotaoPadrao(Button):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ""
        self.background_down = ""
        self.background_color = (0.20, 0.45, 0.85, 1)
        self.color = (1, 1, 1, 1)
        self.font_size = 16


class BotaoSecundario(Button):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ""
        self.background_down = ""
        self.background_color = (0.85, 0.89, 0.96, 1)
        self.color = (0.10, 0.10, 0.10, 1)
        self.font_size = 15


class CampoTexto(TextInput):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.multiline = False
        self.background_normal = ""
        self.background_active = ""
        self.background_color = (1, 1, 1, 1)
        self.foreground_color = (0.1, 0.1, 0.1, 1)
        self.cursor_color = (0.1, 0.1, 0.1, 1)
        self.font_size = 20
        self.padding = [10, 10, 10, 10]


# -------------------------------
# Tela principal
# -------------------------------

class TelaPrincipal(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(
            orientation="vertical",
            spacing=dp(10),
            padding=dp(10),
            **kwargs
        )

        self._criar_topo()
        self._criar_corpo()

    def _criar_topo(self):
        topo = Painel(
            cor=(0.16, 0.23, 0.36, 1),
            orientation="vertical",
            padding=dp(12),
            spacing=dp(4),
            size_hint_y=None,
            height=dp(90)
        )

        titulo = Label(
            text="Protótipo: Polinômios (Kivy + SymPy)",
            font_size=28,
            bold=True,
            color=(1, 1, 1, 1)
        )

        subtitulo = Label(
            text="Ferramenta para simplificar, fatorar, expandir, coletar termos, avaliar e encontrar raízes.",
            font_size=15,
            color=(0.92, 0.95, 1, 1)
        )

        topo.add_widget(titulo)
        topo.add_widget(subtitulo)

        self.add_widget(topo)

    def _criar_corpo(self):
        corpo = BoxLayout(
            orientation="horizontal",
            spacing=dp(10)
        )

        self.sidebar = self._criar_sidebar()
        self.main = self._criar_area_principal()

        corpo.add_widget(self.sidebar)
        corpo.add_widget(self.main)

        self.add_widget(corpo)

    def _criar_sidebar(self):
        sidebar = Painel(
            cor=(1, 1, 1, 1),
            orientation="vertical",
            padding=dp(12),
            spacing=dp(10),
            size_hint_x=None,
            width=dp(300)
        )

        titulo = Label(
            text="Como usar",
            font_size=20,
            bold=True,
            color=(0.12, 0.12, 0.12, 1),
            size_hint_y=None,
            height=dp(28)
        )
        sidebar.add_widget(titulo)

        instrucoes = Label(
            text=(
                "1) Digite ou monte a expressão\n"
                "2) Você pode usar 2x, xy, x², x³\n"
                "3) Se usar y, escreva x,y\n"
                "4) Escolha a operação\n"
                "5) Clique em Executar"
            ),
            font_size=15,
            color=(0.2, 0.2, 0.2, 1),
            halign="left",
            valign="top"
        )
        instrucoes.bind(size=lambda inst, val: setattr(inst, "text_size", val))
        sidebar.add_widget(instrucoes)

        subtitulo_ex = Label(
            text="Exemplos",
            font_size=18,
            bold=True,
            color=(0.12, 0.12, 0.12, 1),
            size_hint_y=None,
            height=dp(26)
        )
        sidebar.add_widget(subtitulo_ex)

        exemplos = [
            ("2x² + 2x + 1", "2x² + 2x + 1", "x"),
            ("(x² - 9)(x + 2)", "(x² - 9)(x + 2)", "x"),
            ("x² + 2xy + y²", "x² + 2xy + y²", "x,y"),
        ]

        for texto, expr, vars_ in exemplos:
            b = BotaoSecundario(
                text=texto,
                size_hint_y=None,
                height=dp(42)
            )
            b.bind(on_press=lambda instance, e=expr, v=vars_: self.carregar_exemplo(e, v))
            sidebar.add_widget(b)

        subtitulo_at = Label(
            text="Atalhos",
            font_size=18,
            bold=True,
            color=(0.12, 0.12, 0.12, 1),
            size_hint_y=None,
            height=dp(26)
        )
        sidebar.add_widget(subtitulo_at)

        grade = GridLayout(
            cols=4,
            spacing=dp(6),
            size_hint_y=None,
            height=dp(190)
        )

        atalhos = [
            ("x", "x"), ("y", "y"), ("+", "+"), ("-", "-"),
            ("(", "("), (")", ")"), ("×", "*"), ("⌫", "APAGAR"),
            ("x²", "x²"), ("x³", "x³"), ("x⁴", "x⁴"), ("Limpar", "LIMPAR"),
        ]

        for txt, valor in atalhos:
            b = BotaoSecundario(text=txt)
            b.bind(on_press=lambda instance, v=valor: self.inserir_atalho(v))
            grade.add_widget(b)

        sidebar.add_widget(grade)

        dica = Label(
            text="Dica: o sistema entende multiplicação implícita, como 2x e xy.",
            font_size=14,
            color=(0.30, 0.30, 0.30, 1),
            halign="left",
            valign="top"
        )
        dica.bind(size=lambda inst, val: setattr(inst, "text_size", val))
        sidebar.add_widget(dica)

        return sidebar

    def _criar_area_principal(self):
        main = Painel(
            cor=(1, 1, 1, 1),
            orientation="vertical",
            padding=dp(14),
            spacing=dp(10)
        )

        self.entrada_expr = CampoTexto(
            text="x² + 2x + 1",
            size_hint_y=None,
            height=dp(48)
        )

        self.entrada_vars = CampoTexto(
            text="x",
            size_hint_y=None,
            height=dp(44)
        )

        self.entrada_valores = CampoTexto(
            text="",
            size_hint_y=None,
            height=dp(44)
        )

        main.add_widget(self._linha_campo("Expressão", self.entrada_expr))
        main.add_widget(self._linha_campo("Variáveis (ex.: x ou x,y)", self.entrada_vars))
        main.add_widget(self._linha_campo("Valores para avaliar (ex.: x=2, y=3)", self.entrada_valores))

        bloco_pot = Painel(
            cor=(0.95, 0.97, 1, 1),
            orientation="vertical",
            padding=dp(10),
            spacing=dp(8),
            size_hint_y=None,
            height=dp(120)
        )

        bloco_pot.add_widget(Label(
            text="Criar potência com número pequeno",
            font_size=18,
            bold=True,
            color=(0.12, 0.12, 0.12, 1),
            size_hint_y=None,
            height=dp(24)
        ))

        linha_pot = BoxLayout(
            orientation="horizontal",
            spacing=dp(8),
            size_hint_y=None,
            height=dp(42)
        )

        self.base_pot = CampoTexto(
            text="",
            hint_text="Base (ex.: x+2)"
        )

        self.expoente_pot = CampoTexto(
            text="",
            hint_text="Expoente",
            size_hint_x=None,
            width=dp(140)
        )

        botao_pot = BotaoPadrao(
            text="Inserir potência",
            size_hint_x=None,
            width=dp(180)
        )
        botao_pot.bind(on_press=self.inserir_potencia)

        linha_pot.add_widget(self.base_pot)
        linha_pot.add_widget(self.expoente_pot)
        linha_pot.add_widget(botao_pot)

        bloco_pot.add_widget(linha_pot)
        main.add_widget(bloco_pot)

        linha_operacao = BoxLayout(
            orientation="horizontal",
            spacing=dp(8),
            size_hint_y=None,
            height=dp(50)
        )

        self.spinner_operacao = Spinner(
            text="Fatorar",
            values=(
                "Simplificar",
                "Fatorar",
                "Expandir",
                "Coletar termos",
                "Avaliar numericamente",
                "Raízes (resolver expr=0)",
                "Etapas (sequência didática)",
                "Resumo do projeto (todas as operações)"
            ),
            background_normal="",
            background_color=(0.85, 0.89, 0.96, 1),
            color=(0.1, 0.1, 0.1, 1),
            font_size=16
        )

        botao_executar = BotaoPadrao(
            text="Executar",
            size_hint_x=None,
            width=dp(180)
        )
        botao_executar.bind(on_press=self.executar_operacao)

        linha_operacao.add_widget(self.spinner_operacao)
        linha_operacao.add_widget(botao_executar)

        main.add_widget(linha_operacao)

        main.add_widget(Label(
            text="Resultado",
            font_size=20,
            bold=True,
            color=(0.12, 0.12, 0.12, 1),
            size_hint_y=None,
            height=dp(28)
        ))

        self.area_resultado = Painel(
            cor=(0.98, 0.98, 0.99, 1),
            orientation="vertical",
            padding=dp(12),
            spacing=dp(0)
        )

        self.scroll_resultado = ScrollView(
            do_scroll_x=False,
            do_scroll_y=True,
            bar_width=dp(10),
            scroll_type=["bars", "content"]
        )

        self.label_resultado = Label(
            text="",
            font_size=18,
            color=(0.08, 0.08, 0.08, 1),
            halign="left",
            valign="top",
            size_hint_y=None,
            markup=False
        )

        self.label_resultado.bind(texture_size=self._ajustar_altura_resultado)
        self.scroll_resultado.bind(width=self._ajustar_largura_resultado)

        self.scroll_resultado.add_widget(self.label_resultado)
        self.area_resultado.add_widget(self.scroll_resultado)

        main.add_widget(self.area_resultado)

        return main

    def _ajustar_largura_resultado(self, instance, largura):
        self.label_resultado.text_size = (largura - dp(30), None)

    def _ajustar_altura_resultado(self, instance, tamanho):
        altura_minima = self.scroll_resultado.height
        self.label_resultado.height = max(tamanho[1] + dp(20), altura_minima)

    def _linha_campo(self, titulo: str, campo: TextInput) -> BoxLayout:
        bloco = BoxLayout(
            orientation="vertical",
            spacing=dp(4),
            size_hint_y=None,
            height=dp(72)
        )

        rot = Label(
            text=titulo,
            font_size=17,
            bold=True,
            color=(0.12, 0.12, 0.12, 1),
            halign="left",
            valign="middle",
            size_hint_y=None,
            height=dp(22)
        )
        rot.bind(size=lambda inst, val: setattr(inst, "text_size", val))

        bloco.add_widget(rot)
        bloco.add_widget(campo)

        return bloco

    # -------------------------------
    # Resultado visual
    # -------------------------------

    def mostrar_resultado(self, texto: str):
        self.label_resultado.text = texto

        def voltar_para_topo(dt):
            self.scroll_resultado.scroll_y = 1

        Clock.schedule_once(voltar_para_topo, 0.05)
        Clock.schedule_once(voltar_para_topo, 0.20)

    # -------------------------------
    # Ações da interface
    # -------------------------------

    def carregar_exemplo(self, expr: str, vars_: str):
        self.entrada_expr.text = expr
        self.entrada_vars.text = vars_
        self.mostrar_resultado("")

    def inserir_atalho(self, valor: str):
        if valor == "LIMPAR":
            self.entrada_expr.text = ""
        elif valor == "APAGAR":
            self.entrada_expr.text = self.entrada_expr.text[:-1]
        else:
            self.entrada_expr.text += valor

    def inserir_potencia(self, instance):
        base = self.base_pot.text.strip()
        expoente = self.expoente_pot.text.strip()

        if not base or not expoente:
            self.mostrar_resultado("Informe base e expoente.")
            return

        expo_super = para_superescrito(expoente)

        if not expo_super:
            self.mostrar_resultado("O expoente deve conter apenas números.")
            return

        self.entrada_expr.text += f"({base}){expo_super}"

    def obter_dados(self):
        expr_txt = self.entrada_expr.text.strip()
        variaveis = [v.strip() for v in self.entrada_vars.text.strip().split(",") if v.strip()]

        if not expr_txt:
            raise ValueError("Digite uma expressão.")

        if not variaveis:
            raise ValueError("Informe pelo menos uma variável.")

        expr = be.ler_expressao(expr_txt, variaveis)
        simbolos, mapa = be.criar_variaveis(variaveis)
        var_principal = simbolos[0]

        return expr, variaveis, simbolos, mapa, var_principal

    def executar_operacao(self, instance):
        try:
            operacao = self.spinner_operacao.text
            expr, variaveis, simbolos, mapa, var_principal = self.obter_dados()

            atribuicoes = None

            if operacao == "Avaliar numericamente":
                atribuicoes = be.interpretar_atribuicoes(
                    self.entrada_valores.text.strip(),
                    mapa
                )

            texto_resultado = be.executar_operacao_com_passos(
                operacao,
                expr,
                var_principal,
                atribuicoes
            )

            self.mostrar_resultado(texto_resultado)

        except Exception as e:
            self.mostrar_resultado(f"Erro:\n{e}\n\n{traceback.format_exc()}")


class PolinomiosKivyApp(App):
    def build(self):
        self.title = "Polinômios - Ensino Médio"
        return TelaPrincipal()


if __name__ == "__main__":
    PolinomiosKivyApp().run()