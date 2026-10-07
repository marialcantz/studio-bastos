import hmac
import json
import os
import re
import secrets
import sqlite3
import time
from datetime import date, datetime, timedelta
from functools import wraps
from pathlib import Path
from zoneinfo import ZoneInfo

from flask import (
    Flask,
    abort,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)


app = Flask(__name__)


# ============================================================
# SEGREDOS / SESSÃO
# ============================================================

try:
    import segredos

    ADMIN_SENHA = getattr(segredos, "ADMIN_SENHA", None)
    SECRET_KEY = getattr(segredos, "SECRET_KEY", None)

except ImportError:
    ADMIN_SENHA = None
    SECRET_KEY = None


ADMIN_SENHA = (
    ADMIN_SENHA
    or os.environ.get("ADMIN_SENHA")
)


SECRET_KEY = (
    SECRET_KEY
    or os.environ.get("SECRET_KEY")
    or secrets.token_hex(32)
)


app.secret_key = SECRET_KEY


app.config.update(
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SECURE=(
        os.environ.get("COOKIE_SECURE") == "1"
    ),
    PERMANENT_SESSION_LIFETIME=timedelta(hours=12),
)


# ============================================================
# CAMINHOS / HORÁRIO
# ============================================================

PASTA = Path(__file__).parent

BANCO = PASTA / "agenda.db"

FUSO = ZoneInfo("America/Sao_Paulo")


def agora():
    return datetime.now(
        FUSO
    ).replace(
        tzinfo=None
    )


# Segunda = 0
# Terça = 1
# Quarta = 2
# Quinta = 3
# Sexta = 4
# Sábado = 5
# Domingo = 6

DIAS_PADRAO = [
    1,
    2,
    3,
    4,
    5,
]


HORARIOS_PADRAO = [
    "09:00",
    "10:00",
    "11:00",
    "12:00",
    "13:00",
    "14:00",
    "15:00",
    "16:00",
    "17:00",
]


NOMES_DIAS = [
    "Segunda",
    "Terça",
    "Quarta",
    "Quinta",
    "Sexta",
    "Sábado",
    "Domingo",
]


ABREV_DIAS = [
    "Seg",
    "Ter",
    "Qua",
    "Qui",
    "Sex",
    "Sáb",
    "Dom",
]


# ============================================================
# DADOS DO STUDIO
# ============================================================

salao = {

    "nome":
        "Studio Bastos",

    "slogan":
        "Beleza e bem-estar",

    "whatsapp":
        "(11) 97219-9804",

    "telefone":
        "+55 (11) 97219-9804",

    "instagram":
        "studiobastos.53",

    "funcionamento":
        " 9h às 18h",

    # Depois troque pelo endereço correto
    "endereco": "R. Itaquaquecetuba, 144 - Grajaú, São Paulo - SP, 04840-190, Brasil",

    "maps": "https://maps.app.goo.gl/FZxC1x5G9EFuv3vr8",

    "pagamentos":
        "Consulte as formas de pagamento pelo WhatsApp.",
}


# ============================================================
# DIFERENCIAIS
# ============================================================

diferenciais = [

    {
        "titulo":
            "Agendamento fácil",

        "texto":
            "Escolha os serviços, o dia e o horário em poucos passos.",
    },

    {
        "titulo":
            "Atendimento personalizado",

        "texto":
            "Cada combinação é pensada de acordo com o estilo da cliente.",
    },

    {
        "titulo":
            "Higiene e cuidado",

        "texto":
            "Organização e atenção aos detalhes durante o atendimento.",
    },

    {
        "titulo":
            "Acabamento de qualidade",

        "texto":
            "Cuidado em cada etapa para um resultado bonito e bem finalizado.",
    },

]


# ============================================================
# SERVIÇOS
# ============================================================

# valor = valor em centavos.
# Exemplo:
# R$ 150,00 = 15000
#
# por_unha = True
# permite escolher quantidade.

servicos = {

    "Alongamento": [

        {
            "nome":
                "Fibra de vidro",

            "preco":
                "R$ 150,00",

            "valor":
                15000,

            "por_unha":
                False,
        },

        {
            "nome":
                "Molde F1",

            "preco":
                "R$ 120,00",

            "valor":
                12000,

            "por_unha":
                False,
        },

        {
            "nome":
                "Banho de gel",

            "preco":
                "R$ 60,00",

            "valor":
                6000,

            "por_unha":
                False,
        },

        {
            "nome":
                "Blindagem",

            "preco":
                "R$ 50,00",

            "valor":
                5000,

            "por_unha":
                False,
        },

    ],


    "Nail arts": [

        {
            "nome":
                "Encapsulada",

            "preco":
                "R$ 7,00",

            "valor":
                700,

            "descricao":
                "Valor por unha",

            "por_unha":
                True,
        },

        {
            "nome":
                "Francesinha",

            "preco":
                "R$ 6,00",

            "valor":
                600,

            "por_unha":
                False,
        },

        {
            "nome":
                "Adesivo",

            "preco":
                "R$ 3,00",

            "valor":
                300,

            "por_unha":
                False,
        },

        {
            "nome":
                "Pedraria",

            "preco":
                "R$ 4,00",

            "valor":
                400,

            "por_unha":
                False,
        },

        {
            "nome":
                "Outros",

            "preco":
                "R$ 1,50",

            "valor":
                150,

            "por_unha":
                False,
        },

    ],


    "Manutenção": [

        {
            "nome":
                "Manutenção de molde F1",

            "preco":
                "R$ 80,00",

            "valor":
                8000,

            "por_unha":
                False,
        },

        {
            "nome":
                "Manutenção de fibra de vidro",

            "preco":
                "R$ 90,00",

            "valor":
                9000,

            "por_unha":
                False,
        },

    ],


    "Outros": [

        {
            "nome":
                "Remoção",

            "preco":
                "R$ 30,00",

            "valor":
                3000,

            "por_unha":
                False,
        },

        {
            "nome":
                "Reposição de unha",

            "preco":
                "R$ 10,00",

            "valor":
                1000,

            "descricao":
                "Valor por unha",

            "por_unha":
                True,
        },

        {
            "nome":
                "Troca de formato",

            "preco":
                "R$ 20,00",

            "valor":
                2000,

            "por_unha":
                False,
        },

    ],

}


SERVICOS_POR_NOME = {

    item["nome"]:
        item

    for itens
    in servicos.values()

    for item
    in itens

}


# ============================================================
# CSRF
# ============================================================

def csrf_token():

    token = session.get(
        "_csrf_token"
    )

    if not token:

        token = secrets.token_urlsafe(
            32
        )

        session[
            "_csrf_token"
        ] = token

    return token


app.jinja_env.globals[
    "csrf_token"
] = csrf_token


@app.before_request
def proteger_posts():

    if request.method != "POST":
        return None


    esperado = session.get(
        "_csrf_token",
        ""
    )


    recebido = (

        request.headers.get(
            "X-CSRF-Token",
            ""
        )

        or request.form.get(
            "csrf_token",
            ""
        )

    )


    if (
        esperado
        and recebido
        and hmac.compare_digest(
            esperado,
            recebido
        )
    ):

        return None


    if request.path.startswith(
        "/api/"
    ):

        return jsonify(
            erro=(
                "Sessão expirada. "
                "Atualize a página e tente novamente."
            )
        ), 400


    abort(400)


# ============================================================
# BANCO
# ============================================================

def conectar():

    con = sqlite3.connect(
        BANCO
    )

    con.row_factory = (
        sqlite3.Row
    )

    return con


def criar_banco():

    with conectar() as con:

        con.execute(
            """
            CREATE TABLE IF NOT EXISTS agendamentos (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                servico TEXT NOT NULL,

                data TEXT NOT NULL,

                hora TEXT NOT NULL,

                nome TEXT NOT NULL,

                telefone TEXT NOT NULL,

                criado_em TEXT NOT NULL,

                UNIQUE (data, hora)

            )
            """
        )


        con.execute(
            """
            CREATE TABLE IF NOT EXISTS bloqueios (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                data TEXT NOT NULL,

                hora TEXT,

                motivo TEXT NOT NULL DEFAULT ''

            )
            """
        )


        con.execute(
            """
            CREATE TABLE IF NOT EXISTS config (

                chave TEXT PRIMARY KEY,

                valor TEXT NOT NULL

            )
            """
        )


        con.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_agendamentos_data_hora

            ON agendamentos (
                data,
                hora
            )
            """
        )


        con.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_bloqueios_data_hora

            ON bloqueios (
                data,
                hora
            )
            """
        )


# ============================================================
# CONFIGURAÇÃO DE HORÁRIOS
# ============================================================

def normalizar_horarios(
    texto
):

    horarios = set()


    for pedaco in re.split(
        r"[,;\s]+",
        texto or ""
    ):

        pedaco = pedaco.strip()


        if not pedaco:
            continue


        resultado = re.fullmatch(
            r"(\d{1,2})[:h](\d{2})",
            pedaco
        )


        if not resultado:

            raise ValueError(
                (
                    f"Não entendi o horário "
                    f"“{pedaco}”. "
                    f"Use o formato 09:00."
                )
            )


        hora = int(
            resultado.group(1)
        )


        minuto = int(
            resultado.group(2)
        )


        if (
            hora > 23
            or minuto > 59
        ):

            raise ValueError(
                (
                    f"Não entendi o horário "
                    f"“{pedaco}”. "
                    f"Use o formato 09:00."
                )
            )


        horarios.add(
            f"{hora:02d}:{minuto:02d}"
        )


    return sorted(
        horarios
    )


def ler_config():

    with conectar() as con:

        linhas = con.execute(
            """
            SELECT chave, valor
            FROM config
            """
        ).fetchall()


    cfg = {

        linha["chave"]:
            linha["valor"]

        for linha
        in linhas

    }


    try:

        dias = sorted(
            {
                int(valor)

                for valor
                in cfg.get(
                    "dias_abertos",
                    ""
                ).split(",")

                if (
                    valor != ""
                    and 0 <= int(valor) <= 6
                )
            }
        )

    except ValueError:

        dias = list(
            DIAS_PADRAO
        )


    if (
        not dias
        and "dias_abertos"
        not in cfg
    ):

        dias = list(
            DIAS_PADRAO
        )


    try:

        horarios = normalizar_horarios(
            cfg.get(
                "horarios",
                ""
            )
        )

    except ValueError:

        horarios = []


    if not horarios:

        horarios = list(
            HORARIOS_PADRAO
        )


    return (
        dias,
        horarios
    )


def salvar_config(
    chave,
    valor
):

    with conectar() as con:

        con.execute(
            """
            INSERT OR REPLACE INTO config (
                chave,
                valor
            )
            VALUES (?, ?)
            """,
            (
                chave,
                valor
            )
        )


def mes_permitido(
    ano,
    mes
):

    try:

        alvo = date(
            ano,
            mes,
            1
        )

    except ValueError:

        return False


    atual = agora().date().replace(
        day=1
    )


    diferenca = (

        (
            alvo.year
            - atual.year
        )
        * 12

        + alvo.month
        - atual.month

    )


    return (
        0
        <= diferenca
        <= 11
    )


def horarios_do_dia(
    dia
):

    momento = agora()


    dias, horarios = (
        ler_config()
    )


    if dia.weekday() not in dias:

        return []


    if dia < momento.date():

        return []


    iso = dia.isoformat()


    with conectar() as con:

        ocupados = {

            linha["hora"]

            for linha
            in con.execute(
                """
                SELECT hora
                FROM agendamentos
                WHERE data = ?
                """,
                (
                    iso,
                )
            )

        }


        bloqueios = con.execute(
            """
            SELECT hora
            FROM bloqueios
            WHERE data = ?
            """,
            (
                iso,
            )
        ).fetchall()


    if any(
        bloqueio["hora"] is None

        for bloqueio
        in bloqueios
    ):

        return []


    bloqueados = {

        bloqueio["hora"]

        for bloqueio
        in bloqueios

        if bloqueio["hora"]

    }


    resultado = []


    for hora in horarios:

        inicio = datetime.combine(
            dia,

            datetime.strptime(
                hora,
                "%H:%M"
            ).time()
        )


        livre = (

            hora not in ocupados

            and hora not in bloqueados

            and inicio > momento

        )


        resultado.append(
            {
                "hora":
                    hora,

                "livre":
                    livre,
            }
        )


    return resultado


# ============================================================
# SERVIÇOS MÚLTIPLOS
# ============================================================

def formatar_moeda_centavos(
    valor
):

    reais = (
        valor / 100
    )


    texto = f"{reais:,.2f}"


    texto = (
        texto
        .replace(
            ",",
            "X"
        )
        .replace(
            ".",
            ","
        )
        .replace(
            "X",
            "."
        )
    )


    return (
        f"R$ {texto}"
    )


def validar_servicos_recebidos(
    dados
):

    recebidos = dados.get(
        "servicos"
    )


    if not isinstance(
        recebidos,
        list
    ):

        raise ValueError(
            "Escolha pelo menos um serviço."
        )


    if not recebidos:

        raise ValueError(
            "Escolha pelo menos um serviço."
        )


    if len(recebidos) > 20:

        raise ValueError(
            "Foram selecionados serviços demais."
        )


    nomes_vistos = set()

    itens = []

    total = 0


    for recebido in recebidos:

        if not isinstance(
            recebido,
            dict
        ):

            raise ValueError(
                "Há um serviço inválido na seleção."
            )


        nome = str(
            recebido.get(
                "nome",
                ""
            )
        ).strip()


        if (
            nome not in SERVICOS_POR_NOME
            or nome in nomes_vistos
        ):

            raise ValueError(
                "Há um serviço inválido na seleção."
            )


        nomes_vistos.add(
            nome
        )


        cadastro = (
            SERVICOS_POR_NOME[
                nome
            ]
        )


        if cadastro.get(
            "por_unha"
        ):

            try:

                quantidade = int(
                    recebido.get(
                        "quantidade",
                        1
                    )
                )

            except (
                TypeError,
                ValueError
            ):

                quantidade = 1


            if (
                quantidade < 1
                or quantidade > 10
            ):

                raise ValueError(
                    (
                        "Informe de 1 a 10 para "
                        f"{nome}."
                    )
                )

        else:

            quantidade = 1


        subtotal = (
            cadastro["valor"]
            * quantidade
        )


        total += subtotal


        itens.append(
            {

                "nome":
                    nome,

                "quantidade":
                    quantidade,

                "por_unha":
                    bool(
                        cadastro.get(
                            "por_unha"
                        )
                    ),

                "valor_unitario":
                    cadastro["valor"],

                "subtotal":
                    subtotal,

            }
        )


    return (
        itens,
        total
    )


def serializar_servicos(
    itens,
    total
):

    dados = {

        "versao":
            1,

        "itens":
            itens,

        "total":
            total,

    }


    return json.dumps(
        dados,
        ensure_ascii=False,
        separators=(
            ",",
            ":"
        )
    )


def ler_servicos_salvos(
    valor
):

    """
    Formato novo:
    JSON com vários serviços.

    Formato antigo:
    texto simples com um serviço.

    Assim os agendamentos antigos
    continuam funcionando.
    """

    try:

        dados = json.loads(
            valor
        )


        if (
            isinstance(
                dados,
                dict
            )
            and isinstance(
                dados.get(
                    "itens"
                ),
                list
            )
        ):

            itens = []


            for item in dados[
                "itens"
            ]:

                quantidade = int(
                    item.get(
                        "quantidade",
                        1
                    )
                )


                subtotal = int(
                    item.get(
                        "subtotal",
                        0
                    )
                )


                itens.append(
                    {

                        "nome":
                            str(
                                item.get(
                                    "nome",
                                    "Serviço"
                                )
                            ),

                        "quantidade":
                            quantidade,

                        "subtotal":
                            (
                                formatar_moeda_centavos(
                                    subtotal
                                )

                                if subtotal

                                else None
                            ),

                    }
                )


            total = int(
                dados.get(
                    "total",
                    0
                )
            )


            return {

                "itens":
                    itens,

                "total":
                    (
                        formatar_moeda_centavos(
                            total
                        )

                        if total

                        else None
                    ),

            }


    except (
        json.JSONDecodeError,
        TypeError,
        ValueError
    ):

        pass


    return {

        "itens": [
            {

                "nome":
                    valor,

                "quantidade":
                    1,

                "subtotal":
                    None,

            }
        ],

        "total":
            None,

    }


# ============================================================
# PÁGINA PÚBLICA
# ============================================================

@app.route("/")
def home():

    return render_template(
        "index.html",
        salao=salao,
        servicos=servicos,
        diferenciais=diferenciais,
    )


# ============================================================
# API - MÊS
# ============================================================

@app.route(
    "/api/mes"
)
def api_mes():

    try:

        ano = int(
            request.args.get(
                "ano",
                ""
            )
        )


        mes = int(
            request.args.get(
                "mes",
                ""
            )
        )

    except ValueError:

        return jsonify(
            {}
        ), 400


    if not mes_permitido(
        ano,
        mes
    ):

        return jsonify(
            {}
        ), 400


    dia = date(
        ano,
        mes,
        1
    )


    resultado = {}


    while dia.month == mes:

        horarios = horarios_do_dia(
            dia
        )


        if horarios:

            resultado[
                dia.isoformat()
            ] = sum(

                1

                for horario
                in horarios

                if horario[
                    "livre"
                ]

            )


        dia += timedelta(
            days=1
        )


    return jsonify(
        resultado
    )


# ============================================================
# API - HORÁRIOS
# ============================================================

@app.route(
    "/api/horarios"
)
def api_horarios():

    try:

        dia = date.fromisoformat(
            request.args.get(
                "data",
                ""
            )
        )

    except ValueError:

        return jsonify(
            []
        ), 400


    mes_do_dia = (
        dia.replace(
            day=1
        )
    )


    if not mes_permitido(
        mes_do_dia.year,
        mes_do_dia.month
    ):

        return jsonify(
            []
        ), 400


    return jsonify(
        horarios_do_dia(
            dia
        )
    )


# ============================================================
# API - AGENDAR
# ============================================================

@app.route(
    "/api/agendar",
    methods=[
        "POST"
    ]
)
def api_agendar():

    dados = (
        request.get_json(
            silent=True
        )
        or {}
    )


    nome = str(
        dados.get(
            "nome",
            ""
        )
    ).strip()


    telefone = "".join(

        caractere

        for caractere
        in str(
            dados.get(
                "telefone",
                ""
            )
        )

        if caractere.isdigit()

    )


    hora = str(
        dados.get(
            "hora",
            ""
        )
    ).strip()


    try:

        dia = date.fromisoformat(
            str(
                dados.get(
                    "data",
                    ""
                )
            )
        )

    except ValueError:

        return jsonify(
            erro="Data inválida."
        ), 400


    try:

        itens, total = (
            validar_servicos_recebidos(
                dados
            )
        )

    except ValueError as erro:

        return jsonify(
            erro=str(
                erro
            )
        ), 400


    if not nome:

        return jsonify(
            erro="Informe o seu nome."
        ), 400


    if len(nome) > 80:

        return jsonify(
            erro="O nome está muito longo."
        ), 400


    if len(telefone) not in (
        10,
        11
    ):

        return jsonify(
            erro="Informe um telefone com DDD."
        ), 400


    livres = {

        item["hora"]

        for item
        in horarios_do_dia(
            dia
        )

        if item[
            "livre"
        ]

    }


    if hora not in livres:

        return jsonify(
            erro=(
                "Esse horário não está mais "
                "disponível. Escolha outro."
            )
        ), 409


    servicos_salvos = (
        serializar_servicos(
            itens,
            total
        )
    )


    try:

        with conectar() as con:

            con.execute(
                """
                INSERT INTO agendamentos (

                    servico,
                    data,
                    hora,
                    nome,
                    telefone,
                    criado_em

                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,

                (
                    servicos_salvos,
                    dia.isoformat(),
                    hora,
                    nome,
                    telefone,
                    agora().isoformat(),
                )
            )


    except sqlite3.IntegrityError:

        return jsonify(
            erro=(
                "Esse horário acabou de ser "
                "reservado. Escolha outro."
            )
        ), 409


    return jsonify(

        ok=True,

        total=formatar_moeda_centavos(
            total
        )

    )


# ============================================================
# LOGIN ADMIN
# ============================================================

def exige_login(
    funcao
):

    @wraps(
        funcao
    )
    def interna(
        *args,
        **kwargs
    ):

        if (
            not ADMIN_SENHA
            or not session.get(
                "admin"
            )
        ):

            return redirect(
                url_for(
                    "admin_login"
                )
            )


        return funcao(
            *args,
            **kwargs
        )


    return interna


def formatar_telefone(
    digitos
):

    if len(digitos) == 11:

        return (
            f"({digitos[:2]}) "
            f"{digitos[2:7]}-"
            f"{digitos[7:]}"
        )


    if len(digitos) == 10:

        return (
            f"({digitos[:2]}) "
            f"{digitos[2:6]}-"
            f"{digitos[6:]}"
        )


    return digitos


def rotulo_data(
    iso
):

    dia = date.fromisoformat(
        iso
    )


    return (
        f"{ABREV_DIAS[dia.weekday()]}, "
        f"{dia.strftime('%d/%m/%Y')}"
    )


@app.route(
    "/admin/login",
    methods=[
        "GET",
        "POST"
    ]
)
def admin_login():

    if not ADMIN_SENHA:

        return render_template(
            "login.html",
            salao=salao,
            desativado=True,
            erro=None,
        )


    erro = None


    if request.method == "POST":

        senha = request.form.get(
            "senha",
            ""
        )


        if hmac.compare_digest(
            senha.encode(),
            ADMIN_SENHA.encode()
        ):

            session.clear()


            session[
                "admin"
            ] = True


            session.permanent = True


            return redirect(
                url_for(
                    "admin"
                )
            )


        time.sleep(
            1
        )


        erro = (
            "Senha incorreta."
        )


    return render_template(
        "login.html",
        salao=salao,
        desativado=False,
        erro=erro,
    )


@app.route(
    "/admin/sair",
    methods=[
        "POST"
    ]
)
def admin_sair():

    session.clear()


    return redirect(
        url_for(
            "admin_login"
        )
    )


# ============================================================
# PAINEL ADMIN
# ============================================================

@app.route(
    "/admin"
)
@exige_login
def admin():

    hoje = (
        agora()
        .date()
        .isoformat()
    )


    dias_abertos, horarios = (
        ler_config()
    )


    with conectar() as con:

        marcacoes = con.execute(
            """
            SELECT *
            FROM agendamentos
            WHERE data >= ?
            ORDER BY data, hora
            """,
            (
                hoje,
            )
        ).fetchall()


        bloqueios = con.execute(
            """
            SELECT *
            FROM bloqueios
            WHERE data >= ?
            ORDER BY data, hora
            """,
            (
                hoje,
            )
        ).fetchall()


    grupos = []


    for marcacao in marcacoes:

        if (
            not grupos
            or grupos[-1][
                "data"
            ] != marcacao[
                "data"
            ]
        ):

            grupos.append(
                {

                    "data":
                        marcacao[
                            "data"
                        ],

                    "rotulo":
                        rotulo_data(
                            marcacao[
                                "data"
                            ]
                        ),

                    "itens":
                        [],

                }
            )


        detalhes = (
            ler_servicos_salvos(
                marcacao[
                    "servico"
                ]
            )
        )


        grupos[-1][
            "itens"
        ].append(
            {

                "id":
                    marcacao[
                        "id"
                    ],

                "hora":
                    marcacao[
                        "hora"
                    ],

                "nome":
                    marcacao[
                        "nome"
                    ],

                "telefone":
                    marcacao[
                        "telefone"
                    ],

                "telefone_fmt":
                    formatar_telefone(
                        marcacao[
                            "telefone"
                        ]
                    ),

                "servicos":
                    detalhes[
                        "itens"
                    ],

                "total_servicos":
                    detalhes[
                        "total"
                    ],

            }
        )


    lista_bloqueios = [

        {

            "id":
                bloqueio[
                    "id"
                ],

            "rotulo":
                rotulo_data(
                    bloqueio[
                        "data"
                    ]
                ),

            "hora":
                (
                    bloqueio[
                        "hora"
                    ]
                    or "Dia inteiro"
                ),

            "motivo":
                bloqueio[
                    "motivo"
                ],

        }

        for bloqueio
        in bloqueios

    ]


    return render_template(
        "admin.html",
        salao=salao,
        grupos=grupos,
        total=len(
            marcacoes
        ),
        bloqueios=lista_bloqueios,
        hoje=hoje,
        horarios=horarios,
        horarios_texto=", ".join(
            horarios
        ),
        dias_abertos=dias_abertos,
        nomes_dias=list(
            enumerate(
                NOMES_DIAS
            )
        ),
    )


# ============================================================
# CANCELAR
# ============================================================

@app.route(
    "/admin/cancelar/<int:id>",
    methods=[
        "POST"
    ]
)
@exige_login
def admin_cancelar(
    id
):

    with conectar() as con:

        con.execute(
            """
            DELETE FROM agendamentos
            WHERE id = ?
            """,
            (
                id,
            )
        )


    flash(
        (
            "Marcação cancelada. "
            "O horário voltou a ficar livre."
        ),
        "ok"
    )


    return redirect(
        url_for(
            "admin"
        )
    )


# ============================================================
# BLOQUEAR
# ============================================================

@app.route(
    "/admin/bloquear",
    methods=[
        "POST"
    ]
)
@exige_login
def admin_bloquear():

    _, horarios = (
        ler_config()
    )


    motivo = (
        request.form.get(
            "motivo",
            ""
        )
        .strip()[:80]
    )


    hora = (
        request.form.get(
            "hora",
            ""
        )
        .strip()
    )


    try:

        dia = date.fromisoformat(
            request.form.get(
                "data",
                ""
            )
        )

    except ValueError:

        flash(
            (
                "Escolha uma data válida "
                "para bloquear."
            ),
            "erro"
        )


        return redirect(
            url_for(
                "admin"
            )
        )


    if dia < agora().date():

        flash(
            (
                "Não dá para bloquear "
                "um dia que já passou."
            ),
            "erro"
        )


        return redirect(
            url_for(
                "admin"
            )
        )


    if (
        hora
        and hora not in horarios
    ):

        flash(
            (
                "Esse horário não existe "
                "na sua lista de horários."
            ),
            "erro"
        )


        return redirect(
            url_for(
                "admin"
            )
        )


    iso = (
        dia.isoformat()
    )


    with conectar() as con:

        if hora:

            ja_existe = con.execute(
                """
                SELECT 1

                FROM bloqueios

                WHERE data = ?

                AND (
                    hora = ?
                    OR hora IS NULL
                )
                """,
                (
                    iso,
                    hora
                )
            ).fetchone()


            conflitos = con.execute(
                """
                SELECT COUNT(*)

                FROM agendamentos

                WHERE data = ?

                AND hora = ?
                """,
                (
                    iso,
                    hora
                )
            ).fetchone()[0]


        else:

            ja_existe = con.execute(
                """
                SELECT 1

                FROM bloqueios

                WHERE data = ?

                AND hora IS NULL
                """,
                (
                    iso,
                )
            ).fetchone()


            conflitos = con.execute(
                """
                SELECT COUNT(*)

                FROM agendamentos

                WHERE data = ?
                """,
                (
                    iso,
                )
            ).fetchone()[0]


        if ja_existe:

            flash(
                (
                    "Esse dia ou horário "
                    "já está bloqueado."
                ),
                "erro"
            )


            return redirect(
                url_for(
                    "admin"
                )
            )


        con.execute(
            """
            INSERT INTO bloqueios (
                data,
                hora,
                motivo
            )

            VALUES (?, ?, ?)
            """,
            (
                iso,
                hora or None,
                motivo
            )
        )


    if conflitos:

        flash(
            (
                f"Bloqueado! Atenção: já existia(m) "
                f"{conflitos} marcação(ões) nesse período. "
                "Elas continuam na agenda; cancele se precisar."
            ),
            "erro"
        )

    else:

        flash(
            (
                "Bloqueado! As clientes não conseguem "
                "mais marcar nesse período."
            ),
            "ok"
        )


    return redirect(
        url_for(
            "admin"
        )
    )


# ============================================================
# DESBLOQUEAR
# ============================================================

@app.route(
    "/admin/desbloquear/<int:id>",
    methods=[
        "POST"
    ]
)
@exige_login
def admin_desbloquear(
    id
):

    with conectar() as con:

        con.execute(
            """
            DELETE FROM bloqueios
            WHERE id = ?
            """,
            (
                id,
            )
        )


    flash(
        "Bloqueio removido.",
        "ok"
    )


    return redirect(
        url_for(
            "admin"
        )
    )


# ============================================================
# CONFIGURAR HORÁRIOS
# ============================================================

@app.route(
    "/admin/horarios",
    methods=[
        "POST"
    ]
)
@exige_login
def admin_horarios():

    dias = sorted(
        {

            int(valor)

            for valor
            in request.form.getlist(
                "dias"
            )

            if (
                valor.isdigit()
                and 0 <= int(valor) <= 6
            )

        }
    )


    if not dias:

        flash(
            (
                "Escolha pelo menos "
                "um dia de atendimento."
            ),
            "erro"
        )


        return redirect(
            url_for(
                "admin"
            )
        )


    try:

        horarios = normalizar_horarios(
            request.form.get(
                "horarios",
                ""
            )
        )

    except ValueError as erro:

        flash(
            str(
                erro
            ),
            "erro"
        )


        return redirect(
            url_for(
                "admin"
            )
        )


    if not horarios:

        flash(
            (
                "Informe pelo menos "
                "um horário."
            ),
            "erro"
        )


        return redirect(
            url_for(
                "admin"
            )
        )


    salvar_config(
        "dias_abertos",

        ",".join(
            str(dia)

            for dia
            in dias
        )
    )


    salvar_config(
        "horarios",

        ",".join(
            horarios
        )
    )


    flash(
        (
            "Horários de atendimento "
            "salvos!"
        ),
        "ok"
    )


    return redirect(
        url_for(
            "admin"
        )
    )


# ============================================================
# INICIALIZAÇÃO
# ============================================================

criar_banco()


if __name__ == "__main__":

    app.run(
        debug=(
            os.environ.get(
                "FLASK_DEBUG"
            )
            == "1"
        )
    )import hmac
import json
import os
import re
import secrets
import sqlite3
import time
from datetime import date, datetime, timedelta
from functools import wraps
from pathlib import Path
from zoneinfo import ZoneInfo

from flask import (
    Flask,
    abort,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)


app = Flask(__name__)


# ============================================================
# SEGREDOS / SESSÃO
# ============================================================

try:
    import segredos

    ADMIN_SENHA = getattr(segredos, "ADMIN_SENHA", None)
    SECRET_KEY = getattr(segredos, "SECRET_KEY", None)

except ImportError:
    ADMIN_SENHA = None
    SECRET_KEY = None


ADMIN_SENHA = (
    ADMIN_SENHA
    or os.environ.get("ADMIN_SENHA")
)


SECRET_KEY = (
    SECRET_KEY
    or os.environ.get("SECRET_KEY")
    or secrets.token_hex(32)
)


app.secret_key = SECRET_KEY


app.config.update(
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SECURE=(
        os.environ.get("COOKIE_SECURE") == "1"
    ),
    PERMANENT_SESSION_LIFETIME=timedelta(hours=12),
)


# ============================================================
# CAMINHOS / HORÁRIO
# ============================================================

PASTA = Path(__file__).parent

BANCO = PASTA / "agenda.db"

FUSO = ZoneInfo("America/Sao_Paulo")


def agora():
    return datetime.now(
        FUSO
    ).replace(
        tzinfo=None
    )


# Segunda = 0
# Terça = 1
# Quarta = 2
# Quinta = 3
# Sexta = 4
# Sábado = 5
# Domingo = 6

DIAS_PADRAO = [
    1,
    2,
    3,
    4,
    5,
]


HORARIOS_PADRAO = [
    "09:00",
    "10:00",
    "11:00",
    "12:00",
    "13:00",
    "14:00",
    "15:00",
    "16:00",
    "17:00",
]


NOMES_DIAS = [
    "Segunda",
    "Terça",
    "Quarta",
    "Quinta",
    "Sexta",
    "Sábado",
    "Domingo",
]


ABREV_DIAS = [
    "Seg",
    "Ter",
    "Qua",
    "Qui",
    "Sex",
    "Sáb",
    "Dom",
]


# ============================================================
# DADOS DO STUDIO
# ============================================================

salao = {

    "nome":
        "Studio Bastos",

    "slogan":
        "Beleza e bem-estar",

    "whatsapp":
        "(11) 97219-9804",

    "telefone":
        "+55 (11) 97219-9804",

    "instagram":
        "studiobastos.53",

    "funcionamento":
        " 9h às 18h",

    # Depois troque pelo endereço correto
    "endereco": "R. Itaquaquecetuba, 144 - Grajaú, São Paulo - SP, 04840-190, Brasil",

    "maps": "https://maps.app.goo.gl/FZxC1x5G9EFuv3vr8",

    "pagamentos":
        "Consulte as formas de pagamento pelo WhatsApp.",
}


# ============================================================
# DIFERENCIAIS
# ============================================================

diferenciais = [

    {
        "titulo":
            "Agendamento fácil",

        "texto":
            "Escolha os serviços, o dia e o horário em poucos passos.",
    },

    {
        "titulo":
            "Atendimento personalizado",

        "texto":
            "Cada combinação é pensada de acordo com o estilo da cliente.",
    },

    {
        "titulo":
            "Higiene e cuidado",

        "texto":
            "Organização e atenção aos detalhes durante o atendimento.",
    },

    {
        "titulo":
            "Acabamento de qualidade",

        "texto":
            "Cuidado em cada etapa para um resultado bonito e bem finalizado.",
    },

]


# ============================================================
# SERVIÇOS
# ============================================================

# valor = valor em centavos.
# Exemplo:
# R$ 150,00 = 15000
#
# por_unha = True
# permite escolher quantidade.

servicos = {

    "Alongamento": [

        {
            "nome":
                "Fibra de vidro",

            "preco":
                "R$ 150,00",

            "valor":
                15000,

            "por_unha":
                False,
        },

        {
            "nome":
                "Molde F1",

            "preco":
                "R$ 120,00",

            "valor":
                12000,

            "por_unha":
                False,
        },

        {
            "nome":
                "Banho de gel",

            "preco":
                "R$ 60,00",

            "valor":
                6000,

            "por_unha":
                False,
        },

        {
            "nome":
                "Blindagem",

            "preco":
                "R$ 50,00",

            "valor":
                5000,

            "por_unha":
                False,
        },

    ],


    "Nail arts": [

        {
            "nome":
                "Encapsulada",

            "preco":
                "R$ 7,00",

            "valor":
                700,

            "descricao":
                "Valor por unha",

            "por_unha":
                True,
        },

        {
            "nome":
                "Francesinha",

            "preco":
                "R$ 6,00",

            "valor":
                600,

            "por_unha":
                False,
        },

        {
            "nome":
                "Adesivo",

            "preco":
                "R$ 3,00",

            "valor":
                300,

            "por_unha":
                False,
        },

        {
            "nome":
                "Pedraria",

            "preco":
                "R$ 4,00",

            "valor":
                400,

            "por_unha":
                False,
        },

        {
            "nome":
                "Outros",

            "preco":
                "R$ 1,50",

            "valor":
                150,

            "por_unha":
                False,
        },

    ],


    "Manutenção": [

        {
            "nome":
                "Manutenção de molde F1",

            "preco":
                "R$ 80,00",

            "valor":
                8000,

            "por_unha":
                False,
        },

        {
            "nome":
                "Manutenção de fibra de vidro",

            "preco":
                "R$ 90,00",

            "valor":
                9000,

            "por_unha":
                False,
        },

    ],


    "Outros": [

        {
            "nome":
                "Remoção",

            "preco":
                "R$ 30,00",

            "valor":
                3000,

            "por_unha":
                False,
        },

        {
            "nome":
                "Reposição de unha",

            "preco":
                "R$ 10,00",

            "valor":
                1000,

            "descricao":
                "Valor por unha",

            "por_unha":
                True,
        },

        {
            "nome":
                "Troca de formato",

            "preco":
                "R$ 20,00",

            "valor":
                2000,

            "por_unha":
                False,
        },

    ],

}


SERVICOS_POR_NOME = {

    item["nome"]:
        item

    for itens
    in servicos.values()

    for item
    in itens

}


# ============================================================
# CSRF
# ============================================================

def csrf_token():

    token = session.get(
        "_csrf_token"
    )

    if not token:

        token = secrets.token_urlsafe(
            32
        )

        session[
            "_csrf_token"
        ] = token

    return token


app.jinja_env.globals[
    "csrf_token"
] = csrf_token


@app.before_request
def proteger_posts():

    if request.method != "POST":
        return None


    esperado = session.get(
        "_csrf_token",
        ""
    )


    recebido = (

        request.headers.get(
            "X-CSRF-Token",
            ""
        )

        or request.form.get(
            "csrf_token",
            ""
        )

    )


    if (
        esperado
        and recebido
        and hmac.compare_digest(
            esperado,
            recebido
        )
    ):

        return None


    if request.path.startswith(
        "/api/"
    ):

        return jsonify(
            erro=(
                "Sessão expirada. "
                "Atualize a página e tente novamente."
            )
        ), 400


    abort(400)


# ============================================================
# BANCO
# ============================================================

def conectar():

    con = sqlite3.connect(
        BANCO
    )

    con.row_factory = (
        sqlite3.Row
    )

    return con


def criar_banco():

    with conectar() as con:

        con.execute(
            """
            CREATE TABLE IF NOT EXISTS agendamentos (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                servico TEXT NOT NULL,

                data TEXT NOT NULL,

                hora TEXT NOT NULL,

                nome TEXT NOT NULL,

                telefone TEXT NOT NULL,

                criado_em TEXT NOT NULL,

                UNIQUE (data, hora)

            )
            """
        )


        con.execute(
            """
            CREATE TABLE IF NOT EXISTS bloqueios (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                data TEXT NOT NULL,

                hora TEXT,

                motivo TEXT NOT NULL DEFAULT ''

            )
            """
        )


        con.execute(
            """
            CREATE TABLE IF NOT EXISTS config (

                chave TEXT PRIMARY KEY,

                valor TEXT NOT NULL

            )
            """
        )


        con.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_agendamentos_data_hora

            ON agendamentos (
                data,
                hora
            )
            """
        )


        con.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_bloqueios_data_hora

            ON bloqueios (
                data,
                hora
            )
            """
        )


# ============================================================
# CONFIGURAÇÃO DE HORÁRIOS
# ============================================================

def normalizar_horarios(
    texto
):

    horarios = set()


    for pedaco in re.split(
        r"[,;\s]+",
        texto or ""
    ):

        pedaco = pedaco.strip()


        if not pedaco:
            continue


        resultado = re.fullmatch(
            r"(\d{1,2})[:h](\d{2})",
            pedaco
        )


        if not resultado:

            raise ValueError(
                (
                    f"Não entendi o horário "
                    f"“{pedaco}”. "
                    f"Use o formato 09:00."
                )
            )


        hora = int(
            resultado.group(1)
        )


        minuto = int(
            resultado.group(2)
        )


        if (
            hora > 23
            or minuto > 59
        ):

            raise ValueError(
                (
                    f"Não entendi o horário "
                    f"“{pedaco}”. "
                    f"Use o formato 09:00."
                )
            )


        horarios.add(
            f"{hora:02d}:{minuto:02d}"
        )


    return sorted(
        horarios
    )


def ler_config():

    with conectar() as con:

        linhas = con.execute(
            """
            SELECT chave, valor
            FROM config
            """
        ).fetchall()


    cfg = {

        linha["chave"]:
            linha["valor"]

        for linha
        in linhas

    }


    try:

        dias = sorted(
            {
                int(valor)

                for valor
                in cfg.get(
                    "dias_abertos",
                    ""
                ).split(",")

                if (
                    valor != ""
                    and 0 <= int(valor) <= 6
                )
            }
        )

    except ValueError:

        dias = list(
            DIAS_PADRAO
        )


    if (
        not dias
        and "dias_abertos"
        not in cfg
    ):

        dias = list(
            DIAS_PADRAO
        )


    try:

        horarios = normalizar_horarios(
            cfg.get(
                "horarios",
                ""
            )
        )

    except ValueError:

        horarios = []


    if not horarios:

        horarios = list(
            HORARIOS_PADRAO
        )


    return (
        dias,
        horarios
    )


def salvar_config(
    chave,
    valor
):

    with conectar() as con:

        con.execute(
            """
            INSERT OR REPLACE INTO config (
                chave,
                valor
            )
            VALUES (?, ?)
            """,
            (
                chave,
                valor
            )
        )


def mes_permitido(
    ano,
    mes
):

    try:

        alvo = date(
            ano,
            mes,
            1
        )

    except ValueError:

        return False


    atual = agora().date().replace(
        day=1
    )


    diferenca = (

        (
            alvo.year
            - atual.year
        )
        * 12

        + alvo.month
        - atual.month

    )


    return (
        0
        <= diferenca
        <= 11
    )


def horarios_do_dia(
    dia
):

    momento = agora()


    dias, horarios = (
        ler_config()
    )


    if dia.weekday() not in dias:

        return []


    if dia < momento.date():

        return []


    iso = dia.isoformat()


    with conectar() as con:

        ocupados = {

            linha["hora"]

            for linha
            in con.execute(
                """
                SELECT hora
                FROM agendamentos
                WHERE data = ?
                """,
                (
                    iso,
                )
            )

        }


        bloqueios = con.execute(
            """
            SELECT hora
            FROM bloqueios
            WHERE data = ?
            """,
            (
                iso,
            )
        ).fetchall()


    if any(
        bloqueio["hora"] is None

        for bloqueio
        in bloqueios
    ):

        return []


    bloqueados = {

        bloqueio["hora"]

        for bloqueio
        in bloqueios

        if bloqueio["hora"]

    }


    resultado = []


    for hora in horarios:

        inicio = datetime.combine(
            dia,

            datetime.strptime(
                hora,
                "%H:%M"
            ).time()
        )


        livre = (

            hora not in ocupados

            and hora not in bloqueados

            and inicio > momento

        )


        resultado.append(
            {
                "hora":
                    hora,

                "livre":
                    livre,
            }
        )


    return resultado


# ============================================================
# SERVIÇOS MÚLTIPLOS
# ============================================================

def formatar_moeda_centavos(
    valor
):

    reais = (
        valor / 100
    )


    texto = f"{reais:,.2f}"


    texto = (
        texto
        .replace(
            ",",
            "X"
        )
        .replace(
            ".",
            ","
        )
        .replace(
            "X",
            "."
        )
    )


    return (
        f"R$ {texto}"
    )


def validar_servicos_recebidos(
    dados
):

    recebidos = dados.get(
        "servicos"
    )


    if not isinstance(
        recebidos,
        list
    ):

        raise ValueError(
            "Escolha pelo menos um serviço."
        )


    if not recebidos:

        raise ValueError(
            "Escolha pelo menos um serviço."
        )


    if len(recebidos) > 20:

        raise ValueError(
            "Foram selecionados serviços demais."
        )


    nomes_vistos = set()

    itens = []

    total = 0


    for recebido in recebidos:

        if not isinstance(
            recebido,
            dict
        ):

            raise ValueError(
                "Há um serviço inválido na seleção."
            )


        nome = str(
            recebido.get(
                "nome",
                ""
            )
        ).strip()


        if (
            nome not in SERVICOS_POR_NOME
            or nome in nomes_vistos
        ):

            raise ValueError(
                "Há um serviço inválido na seleção."
            )


        nomes_vistos.add(
            nome
        )


        cadastro = (
            SERVICOS_POR_NOME[
                nome
            ]
        )


        if cadastro.get(
            "por_unha"
        ):

            try:

                quantidade = int(
                    recebido.get(
                        "quantidade",
                        1
                    )
                )

            except (
                TypeError,
                ValueError
            ):

                quantidade = 1


            if (
                quantidade < 1
                or quantidade > 10
            ):

                raise ValueError(
                    (
                        "Informe de 1 a 10 para "
                        f"{nome}."
                    )
                )

        else:

            quantidade = 1


        subtotal = (
            cadastro["valor"]
            * quantidade
        )


        total += subtotal


        itens.append(
            {

                "nome":
                    nome,

                "quantidade":
                    quantidade,

                "por_unha":
                    bool(
                        cadastro.get(
                            "por_unha"
                        )
                    ),

                "valor_unitario":
                    cadastro["valor"],

                "subtotal":
                    subtotal,

            }
        )


    return (
        itens,
        total
    )


def serializar_servicos(
    itens,
    total
):

    dados = {

        "versao":
            1,

        "itens":
            itens,

        "total":
            total,

    }


    return json.dumps(
        dados,
        ensure_ascii=False,
        separators=(
            ",",
            ":"
        )
    )


def ler_servicos_salvos(
    valor
):

    """
    Formato novo:
    JSON com vários serviços.

    Formato antigo:
    texto simples com um serviço.

    Assim os agendamentos antigos
    continuam funcionando.
    """

    try:

        dados = json.loads(
            valor
        )


        if (
            isinstance(
                dados,
                dict
            )
            and isinstance(
                dados.get(
                    "itens"
                ),
                list
            )
        ):

            itens = []


            for item in dados[
                "itens"
            ]:

                quantidade = int(
                    item.get(
                        "quantidade",
                        1
                    )
                )


                subtotal = int(
                    item.get(
                        "subtotal",
                        0
                    )
                )


                itens.append(
                    {

                        "nome":
                            str(
                                item.get(
                                    "nome",
                                    "Serviço"
                                )
                            ),

                        "quantidade":
                            quantidade,

                        "subtotal":
                            (
                                formatar_moeda_centavos(
                                    subtotal
                                )

                                if subtotal

                                else None
                            ),

                    }
                )


            total = int(
                dados.get(
                    "total",
                    0
                )
            )


            return {

                "itens":
                    itens,

                "total":
                    (
                        formatar_moeda_centavos(
                            total
                        )

                        if total

                        else None
                    ),

            }


    except (
        json.JSONDecodeError,
        TypeError,
        ValueError
    ):

        pass


    return {

        "itens": [
            {

                "nome":
                    valor,

                "quantidade":
                    1,

                "subtotal":
                    None,

            }
        ],

        "total":
            None,

    }


# ============================================================
# PÁGINA PÚBLICA
# ============================================================

@app.route("/")
def home():

    return render_template(
        "index.html",
        salao=salao,
        servicos=servicos,
        diferenciais=diferenciais,
    )


# ============================================================
# API - MÊS
# ============================================================

@app.route(
    "/api/mes"
)
def api_mes():

    try:

        ano = int(
            request.args.get(
                "ano",
                ""
            )
        )


        mes = int(
            request.args.get(
                "mes",
                ""
            )
        )

    except ValueError:

        return jsonify(
            {}
        ), 400


    if not mes_permitido(
        ano,
        mes
    ):

        return jsonify(
            {}
        ), 400


    dia = date(
        ano,
        mes,
        1
    )


    resultado = {}


    while dia.month == mes:

        horarios = horarios_do_dia(
            dia
        )


        if horarios:

            resultado[
                dia.isoformat()
            ] = sum(

                1

                for horario
                in horarios

                if horario[
                    "livre"
                ]

            )


        dia += timedelta(
            days=1
        )


    return jsonify(
        resultado
    )


# ============================================================
# API - HORÁRIOS
# ============================================================

@app.route(
    "/api/horarios"
)
def api_horarios():

    try:

        dia = date.fromisoformat(
            request.args.get(
                "data",
                ""
            )
        )

    except ValueError:

        return jsonify(
            []
        ), 400


    mes_do_dia = (
        dia.replace(
            day=1
        )
    )


    if not mes_permitido(
        mes_do_dia.year,
        mes_do_dia.month
    ):

        return jsonify(
            []
        ), 400


    return jsonify(
        horarios_do_dia(
            dia
        )
    )


# ============================================================
# API - AGENDAR
# ============================================================

@app.route(
    "/api/agendar",
    methods=[
        "POST"
    ]
)
def api_agendar():

    dados = (
        request.get_json(
            silent=True
        )
        or {}
    )


    nome = str(
        dados.get(
            "nome",
            ""
        )
    ).strip()


    telefone = "".join(

        caractere

        for caractere
        in str(
            dados.get(
                "telefone",
                ""
            )
        )

        if caractere.isdigit()

    )


    hora = str(
        dados.get(
            "hora",
            ""
        )
    ).strip()


    try:

        dia = date.fromisoformat(
            str(
                dados.get(
                    "data",
                    ""
                )
            )
        )

    except ValueError:

        return jsonify(
            erro="Data inválida."
        ), 400


    try:

        itens, total = (
            validar_servicos_recebidos(
                dados
            )
        )

    except ValueError as erro:

        return jsonify(
            erro=str(
                erro
            )
        ), 400


    if not nome:

        return jsonify(
            erro="Informe o seu nome."
        ), 400


    if len(nome) > 80:

        return jsonify(
            erro="O nome está muito longo."
        ), 400


    if len(telefone) not in (
        10,
        11
    ):

        return jsonify(
            erro="Informe um telefone com DDD."
        ), 400


    livres = {

        item["hora"]

        for item
        in horarios_do_dia(
            dia
        )

        if item[
            "livre"
        ]

    }


    if hora not in livres:

        return jsonify(
            erro=(
                "Esse horário não está mais "
                "disponível. Escolha outro."
            )
        ), 409


    servicos_salvos = (
        serializar_servicos(
            itens,
            total
        )
    )


    try:

        with conectar() as con:

            con.execute(
                """
                INSERT INTO agendamentos (

                    servico,
                    data,
                    hora,
                    nome,
                    telefone,
                    criado_em

                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,

                (
                    servicos_salvos,
                    dia.isoformat(),
                    hora,
                    nome,
                    telefone,
                    agora().isoformat(),
                )
            )


    except sqlite3.IntegrityError:

        return jsonify(
            erro=(
                "Esse horário acabou de ser "
                "reservado. Escolha outro."
            )
        ), 409


    return jsonify(

        ok=True,

        total=formatar_moeda_centavos(
            total
        )

    )


# ============================================================
# LOGIN ADMIN
# ============================================================

def exige_login(
    funcao
):

    @wraps(
        funcao
    )
    def interna(
        *args,
        **kwargs
    ):

        if (
            not ADMIN_SENHA
            or not session.get(
                "admin"
            )
        ):

            return redirect(
                url_for(
                    "admin_login"
                )
            )


        return funcao(
            *args,
            **kwargs
        )


    return interna


def formatar_telefone(
    digitos
):

    if len(digitos) == 11:

        return (
            f"({digitos[:2]}) "
            f"{digitos[2:7]}-"
            f"{digitos[7:]}"
        )


    if len(digitos) == 10:

        return (
            f"({digitos[:2]}) "
            f"{digitos[2:6]}-"
            f"{digitos[6:]}"
        )


    return digitos


def rotulo_data(
    iso
):

    dia = date.fromisoformat(
        iso
    )


    return (
        f"{ABREV_DIAS[dia.weekday()]}, "
        f"{dia.strftime('%d/%m/%Y')}"
    )


@app.route(
    "/admin/login",
    methods=[
        "GET",
        "POST"
    ]
)
def admin_login():

    if not ADMIN_SENHA:

        return render_template(
            "login.html",
            salao=salao,
            desativado=True,
            erro=None,
        )


    erro = None


    if request.method == "POST":

        senha = request.form.get(
            "senha",
            ""
        )


        if hmac.compare_digest(
            senha.encode(),
            ADMIN_SENHA.encode()
        ):

            session.clear()


            session[
                "admin"
            ] = True


            session.permanent = True


            return redirect(
                url_for(
                    "admin"
                )
            )


        time.sleep(
            1
        )


        erro = (
            "Senha incorreta."
        )


    return render_template(
        "login.html",
        salao=salao,
        desativado=False,
        erro=erro,
    )


@app.route(
    "/admin/sair",
    methods=[
        "POST"
    ]
)
def admin_sair():

    session.clear()


    return redirect(
        url_for(
            "admin_login"
        )
    )


# ============================================================
# PAINEL ADMIN
# ============================================================

@app.route(
    "/admin"
)
@exige_login
def admin():

    hoje = (
        agora()
        .date()
        .isoformat()
    )


    dias_abertos, horarios = (
        ler_config()
    )


    with conectar() as con:

        marcacoes = con.execute(
            """
            SELECT *
            FROM agendamentos
            WHERE data >= ?
            ORDER BY data, hora
            """,
            (
                hoje,
            )
        ).fetchall()


        bloqueios = con.execute(
            """
            SELECT *
            FROM bloqueios
            WHERE data >= ?
            ORDER BY data, hora
            """,
            (
                hoje,
            )
        ).fetchall()


    grupos = []


    for marcacao in marcacoes:

        if (
            not grupos
            or grupos[-1][
                "data"
            ] != marcacao[
                "data"
            ]
        ):

            grupos.append(
                {

                    "data":
                        marcacao[
                            "data"
                        ],

                    "rotulo":
                        rotulo_data(
                            marcacao[
                                "data"
                            ]
                        ),

                    "itens":
                        [],

                }
            )


        detalhes = (
            ler_servicos_salvos(
                marcacao[
                    "servico"
                ]
            )
        )


        grupos[-1][
            "itens"
        ].append(
            {

                "id":
                    marcacao[
                        "id"
                    ],

                "hora":
                    marcacao[
                        "hora"
                    ],

                "nome":
                    marcacao[
                        "nome"
                    ],

                "telefone":
                    marcacao[
                        "telefone"
                    ],

                "telefone_fmt":
                    formatar_telefone(
                        marcacao[
                            "telefone"
                        ]
                    ),

                "servicos":
                    detalhes[
                        "itens"
                    ],

                "total_servicos":
                    detalhes[
                        "total"
                    ],

            }
        )


    lista_bloqueios = [

        {

            "id":
                bloqueio[
                    "id"
                ],

            "rotulo":
                rotulo_data(
                    bloqueio[
                        "data"
                    ]
                ),

            "hora":
                (
                    bloqueio[
                        "hora"
                    ]
                    or "Dia inteiro"
                ),

            "motivo":
                bloqueio[
                    "motivo"
                ],

        }

        for bloqueio
        in bloqueios

    ]


    return render_template(
        "admin.html",
        salao=salao,
        grupos=grupos,
        total=len(
            marcacoes
        ),
        bloqueios=lista_bloqueios,
        hoje=hoje,
        horarios=horarios,
        horarios_texto=", ".join(
            horarios
        ),
        dias_abertos=dias_abertos,
        nomes_dias=list(
            enumerate(
                NOMES_DIAS
            )
        ),
    )


# ============================================================
# CANCELAR
# ============================================================

@app.route(
    "/admin/cancelar/<int:id>",
    methods=[
        "POST"
    ]
)
@exige_login
def admin_cancelar(
    id
):

    with conectar() as con:

        con.execute(
            """
            DELETE FROM agendamentos
            WHERE id = ?
            """,
            (
                id,
            )
        )


    flash(
        (
            "Marcação cancelada. "
            "O horário voltou a ficar livre."
        ),
        "ok"
    )


    return redirect(
        url_for(
            "admin"
        )
    )


# ============================================================
# BLOQUEAR
# ============================================================

@app.route(
    "/admin/bloquear",
    methods=[
        "POST"
    ]
)
@exige_login
def admin_bloquear():

    _, horarios = (
        ler_config()
    )


    motivo = (
        request.form.get(
            "motivo",
            ""
        )
        .strip()[:80]
    )


    hora = (
        request.form.get(
            "hora",
            ""
        )
        .strip()
    )


    try:

        dia = date.fromisoformat(
            request.form.get(
                "data",
                ""
            )
        )

    except ValueError:

        flash(
            (
                "Escolha uma data válida "
                "para bloquear."
            ),
            "erro"
        )


        return redirect(
            url_for(
                "admin"
            )
        )


    if dia < agora().date():

        flash(
            (
                "Não dá para bloquear "
                "um dia que já passou."
            ),
            "erro"
        )


        return redirect(
            url_for(
                "admin"
            )
        )


    if (
        hora
        and hora not in horarios
    ):

        flash(
            (
                "Esse horário não existe "
                "na sua lista de horários."
            ),
            "erro"
        )


        return redirect(
            url_for(
                "admin"
            )
        )


    iso = (
        dia.isoformat()
    )


    with conectar() as con:

        if hora:

            ja_existe = con.execute(
                """
                SELECT 1

                FROM bloqueios

                WHERE data = ?

                AND (
                    hora = ?
                    OR hora IS NULL
                )
                """,
                (
                    iso,
                    hora
                )
            ).fetchone()


            conflitos = con.execute(
                """
                SELECT COUNT(*)

                FROM agendamentos

                WHERE data = ?

                AND hora = ?
                """,
                (
                    iso,
                    hora
                )
            ).fetchone()[0]


        else:

            ja_existe = con.execute(
                """
                SELECT 1

                FROM bloqueios

                WHERE data = ?

                AND hora IS NULL
                """,
                (
                    iso,
                )
            ).fetchone()


            conflitos = con.execute(
                """
                SELECT COUNT(*)

                FROM agendamentos

                WHERE data = ?
                """,
                (
                    iso,
                )
            ).fetchone()[0]


        if ja_existe:

            flash(
                (
                    "Esse dia ou horário "
                    "já está bloqueado."
                ),
                "erro"
            )


            return redirect(
                url_for(
                    "admin"
                )
            )


        con.execute(
            """
            INSERT INTO bloqueios (
                data,
                hora,
                motivo
            )

            VALUES (?, ?, ?)
            """,
            (
                iso,
                hora or None,
                motivo
            )
        )


    if conflitos:

        flash(
            (
                f"Bloqueado! Atenção: já existia(m) "
                f"{conflitos} marcação(ões) nesse período. "
                "Elas continuam na agenda; cancele se precisar."
            ),
            "erro"
        )

    else:

        flash(
            (
                "Bloqueado! As clientes não conseguem "
                "mais marcar nesse período."
            ),
            "ok"
        )


    return redirect(
        url_for(
            "admin"
        )
    )


# ============================================================
# DESBLOQUEAR
# ============================================================

@app.route(
    "/admin/desbloquear/<int:id>",
    methods=[
        "POST"
    ]
)
@exige_login
def admin_desbloquear(
    id
):

    with conectar() as con:

        con.execute(
            """
            DELETE FROM bloqueios
            WHERE id = ?
            """,
            (
                id,
            )
        )


    flash(
        "Bloqueio removido.",
        "ok"
    )


    return redirect(
        url_for(
            "admin"
        )
    )


# ============================================================
# CONFIGURAR HORÁRIOS
# ============================================================

@app.route(
    "/admin/horarios",
    methods=[
        "POST"
    ]
)
@exige_login
def admin_horarios():

    dias = sorted(
        {

            int(valor)

            for valor
            in request.form.getlist(
                "dias"
            )

            if (
                valor.isdigit()
                and 0 <= int(valor) <= 6
            )

        }
    )


    if not dias:

        flash(
            (
                "Escolha pelo menos "
                "um dia de atendimento."
            ),
            "erro"
        )


        return redirect(
            url_for(
                "admin"
            )
        )


    try:

        horarios = normalizar_horarios(
            request.form.get(
                "horarios",
                ""
            )
        )

    except ValueError as erro:

        flash(
            str(
                erro
            ),
            "erro"
        )


        return redirect(
            url_for(
                "admin"
            )
        )


    if not horarios:

        flash(
            (
                "Informe pelo menos "
                "um horário."
            ),
            "erro"
        )


        return redirect(
            url_for(
                "admin"
            )
        )


    salvar_config(
        "dias_abertos",

        ",".join(
            str(dia)

            for dia
            in dias
        )
    )


    salvar_config(
        "horarios",

        ",".join(
            horarios
        )
    )


    flash(
        (
            "Horários de atendimento "
            "salvos!"
        ),
        "ok"
    )


    return redirect(
        url_for(
            "admin"
        )
    )


# ============================================================
# INICIALIZAÇÃO
# ============================================================

criar_banco()


if __name__ == "__main__":

    app.run(
        debug=(
            os.environ.get(
                "FLASK_DEBUG"
            )
            == "1"
        )
    )
