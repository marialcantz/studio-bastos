import hmac
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
# CONFIGURAÇÃO E SEGREDOS
# ============================================================
# A senha e a chave permanente podem ficar em segredos.py:
#
# ADMIN_SENHA = "uma-senha-forte"
# SECRET_KEY = "uma-chave-longa-e-aleatoria"
#
# O arquivo segredos.py NÃO deve ser enviado ao Git.
try:
    import segredos

    ADMIN_SENHA = str(segredos.ADMIN_SENHA)
    SECRET_KEY = str(segredos.SECRET_KEY)
except (ImportError, AttributeError):
    # O site público continua funcionando, mas o /admin fica desativado.
    # A chave aleatória evita usar uma chave previsível como "sem-segredos".
    ADMIN_SENHA = None
    SECRET_KEY = os.environ.get("SECRET_KEY") or secrets.token_hex(32)

app.secret_key = SECRET_KEY

app.config.update(
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_HTTPONLY=True,
    # Em produção com HTTPS, defina COOKIE_SECURE=1.
    SESSION_COOKIE_SECURE=os.environ.get("COOKIE_SECURE") == "1",
)

app.permanent_session_lifetime = timedelta(hours=12)

PASTA = Path(__file__).resolve().parent
BANCO = PASTA / "agenda.db"
FUSO = ZoneInfo("America/Sao_Paulo")

# ============================================================
# DADOS DO SALÃO
# ============================================================
DIAS_PADRAO = [1, 2, 3, 4, 5]  # Terça a sábado

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

salao = {
    "nome": "Studio Bastos",
    "slogan": "Beleza e bem-estar",
    "whatsapp": "5511972199804",
    "telefone": "(11) 97219-9804",
    "instagram": "studiobastos.53",
    "funcionamento": "Ter a Sáb · 9h às 18h",
}

diferenciais = [
    {
        "titulo": "Agendamento fácil",
        "texto": "Escolha o serviço, o dia e o horário em poucos cliques.",
    },
    {
        "titulo": "Atendimento personalizado",
        "texto": "Cada trabalho é pensado para o seu estilo.",
    },
    {
        "titulo": "Higiene e segurança",
        "texto": "Materiais esterilizados e ambiente cuidado.",
    },
    {
        "titulo": "Acabamento de qualidade",
        "texto": "Naturalidade e durabilidade em cada detalhe.",
    },
]

sobre = {
    "titulo": "Conheça o Studio",
    "texto": (
        "Escreva aqui um parágrafo curto sobre o Studio Bastos, "
        "contando a história do atendimento e o que as clientes "
        "encontram no espaço."
    ),
}

servicos = {
    "Alongamento": [
        {
            "nome": "Fibra de vidro",
            "preco": "R$ 150,00",
        },
        {
            "nome": "Molde F1",
            "preco": "R$ 120,00",
        },
        {
            "nome": "Banho de gel",
            "preco": "R$ 60,00",
        },
        {
            "nome": "Blindagem",
            "preco": "R$ 50,00",
        },
    ],

    "Nail arts": [
        {
            "nome": "Encapsulada",
            "preco": "R$ 7,00",
            "descricao": "Valor por unha",
        },
        {
            "nome": "Francesinha",
            "preco": "R$ 6,00",
        },
        {
            "nome": "Adesivo",
            "preco": "R$ 3,00",
        },
        {
            "nome": "Pedraria",
            "preco": "R$ 4,00",
        },
        {
            "nome": "Outros",
            "preco": "R$ 1,50",
        },
    ],

    "Manutenção": [
        {
            "nome": "Manutenção de molde F1",
            "preco": "R$ 80,00",
        },
        {
            "nome": "Manutenção de fibra de vidro",
            "preco": "R$ 90,00",
        },
    ],

    "Outros": [
        {
            "nome": "Remoção",
            "preco": "R$ 30,00",
        },
        {
            "nome": "Reposição de unha",
            "preco": "R$ 10,00",
            "descricao": "Valor por unha",
        },
        {
            "nome": "Troca de formato",
            "preco": "R$ 20,00",
        },
    ],
}


# ============================================================
# UTILITÁRIOS
# ============================================================
def agora():
    """
    Retorna a data e hora atual no fuso de São Paulo.

    O tzinfo é removido para facilitar comparações locais
    com os horários salvos no sistema.
    """
    return datetime.now(FUSO).replace(tzinfo=None)


def conectar():
    con = sqlite3.connect(BANCO)

    con.row_factory = sqlite3.Row

    con.execute("PRAGMA foreign_keys = ON")

    return con


def validar_hora(valor):
    return bool(
        re.fullmatch(
            r"(?:[01]\d|2[0-3]):[0-5]\d",
            valor or "",
        )
    )


def normalizar_horarios(valores):
    """
    Recebe horários separados e devolve
    apenas horários válidos e ordenados.
    """

    resultado = set()

    for valor in valores:
        valor = valor.strip().replace("h", ":", 1)

        if not valor:
            continue

        if re.fullmatch(r"\d{1,2}:\d{1,2}", valor):
            h, m = valor.split(":", 1)

            if 0 <= int(h) <= 23 and 0 <= int(m) <= 59:
                resultado.add(
                    f"{int(h):02d}:{int(m):02d}"
                )

    return sorted(resultado)


def formatar_telefone(digitos):
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


def rotulo_data(iso):
    d = date.fromisoformat(iso)

    return (
        f"{ABREV_DIAS[d.weekday()]}, "
        f"{d.strftime('%d/%m/%Y')}"
    )


# ============================================================
# PROTEÇÃO CSRF
# ============================================================
def csrf_token():
    """
    Cria um token de segurança por sessão.

    Esse token será utilizado para proteger
    as requisições POST.
    """

    token = session.get("csrf_token")

    if not token:
        token = secrets.token_urlsafe(32)
        session["csrf_token"] = token

    return token


@app.context_processor
def injetar_csrf():
    return {
        "csrf_token": csrf_token
    }


def exigir_csrf():
    enviado = (
        request.form.get("csrf_token")
        or request.headers.get("X-CSRF-Token")
    )

    esperado = session.get("csrf_token")

    if (
        not esperado
        or not enviado
        or not hmac.compare_digest(
            str(enviado),
            str(esperado),
        )
    ):
        return (
            jsonify(
                erro=(
                    "Sessão de segurança inválida. "
                    "Recarregue a página e tente novamente."
                )
            ),
            400,
        )

    return None


# ============================================================
# BANCO DE DADOS
# ============================================================
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
            CREATE INDEX IF NOT EXISTS
            idx_agendamentos_data_hora
            ON agendamentos(data, hora)
            """
        )

        con.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_bloqueios_data_hora
            ON bloqueios(data, hora)
            """
        )


def ler_config():
    with conectar() as con:
        linhas = con.execute(
            "SELECT chave, valor FROM config"
        ).fetchall()

    cfg = {
        linha["chave"]: linha["valor"]
        for linha in linhas
    }

    try:
        dias = sorted(
            {
                int(x)
                for x in cfg["dias_abertos"].split(",")
                if x != ""
            }
        )

        if any(
            dia < 0 or dia > 6
            for dia in dias
        ):
            raise ValueError

    except (KeyError, ValueError):
        dias = list(DIAS_PADRAO)

    horarios = normalizar_horarios(
        cfg.get(
            "horarios",
            "",
        ).split(",")
    )

    return (
        dias,
        horarios or list(HORARIOS_PADRAO),
    )


def salvar_config(chave, valor):
    with conectar() as con:
        con.execute(
            """
            INSERT OR REPLACE INTO config
            (chave, valor)
            VALUES (?, ?)
            """,
            (
                chave,
                valor,
            ),
        )


def horarios_do_dia(dia):
    """
    Retorna todos os horários configurados,
    informando se cada horário está livre.
    """

    momento = agora()

    dias, horarios = ler_config()

    if (
        dia.weekday() not in dias
        or dia < momento.date()
    ):
        return []

    iso = dia.isoformat()

    with conectar() as con:

        ocupados = {
            linha["hora"]
            for linha in con.execute(
                """
                SELECT hora
                FROM agendamentos
                WHERE data = ?
                """,
                (iso,),
            )
        }

        bloqueios = con.execute(
            """
            SELECT hora
            FROM bloqueios
            WHERE data = ?
            """,
            (iso,),
        ).fetchall()

    # Se existir um bloqueio sem horário,
    # significa que o dia inteiro está bloqueado.
    if any(
        bloqueio["hora"] is None
        for bloqueio in bloqueios
    ):
        return []

    bloqueados = {
        bloqueio["hora"]
        for bloqueio in bloqueios
    }

    resultado = []

    for hora in horarios:

        inicio = datetime.combine(
            dia,
            datetime.strptime(
                hora,
                "%H:%M",
            ).time(),
        )

        livre = (
            hora not in ocupados
            and hora not in bloqueados
            and inicio > momento
        )

        resultado.append(
            {
                "hora": hora,
                "livre": livre,
            }
        )

    return resultado


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
        sobre=sobre,
    )


# ============================================================
# API — CALENDÁRIO
# ============================================================
@app.route("/api/mes")
def api_mes():

    try:
        ano = int(
            request.args.get(
                "ano",
                "",
            )
        )

        mes = int(
            request.args.get(
                "mes",
                "",
            )
        )

        dia = date(
            ano,
            mes,
            1,
        )

    except (TypeError, ValueError):
        return jsonify(
            erro="Mês inválido."
        ), 400

    hoje = agora().date().replace(
        day=1
    )

    limite = (
        hoje.replace(day=1)
        + timedelta(days=365)
    ).replace(day=1)

    if dia < hoje or dia > limite:
        return jsonify({}), 400

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
                for horario in horarios
                if horario["livre"]
            )

        dia += timedelta(days=1)

    return jsonify(resultado)


# ============================================================
# API — HORÁRIOS
# ============================================================
@app.route("/api/horarios")
def api_horarios():

    try:
        dia = date.fromisoformat(
            request.args.get(
                "data",
                "",
            )
        )

    except (TypeError, ValueError):
        return jsonify(
            erro="Data inválida."
        ), 400

    hoje = agora().date()

    limite = (
        hoje
        + timedelta(days=366)
    )

    if dia < hoje or dia > limite:
        return jsonify([])

    return jsonify(
        horarios_do_dia(dia)
    )


# ============================================================
# API — REALIZAR AGENDAMENTO
# ============================================================
@app.route(
    "/api/agendar",
    methods=["POST"],
)
def api_agendar():

    erro_csrf = exigir_csrf()

    if erro_csrf:
        return erro_csrf

    dados = (
        request.get_json(
            silent=True
        )
        or {}
    )

    servico = str(
        dados.get(
            "servico",
            "",
        )
    ).strip()

    nome = str(
        dados.get(
            "nome",
            "",
        )
    ).strip()

    telefone = "".join(
        caractere
        for caractere in str(
            dados.get(
                "telefone",
                "",
            )
        )
        if caractere.isdigit()
    )

    hora = str(
        dados.get(
            "hora",
            "",
        )
    ).strip()

    try:
        dia = date.fromisoformat(
            str(
                dados.get(
                    "data",
                    "",
                )
            )
        )

    except ValueError:
        return jsonify(
            erro="Data inválida."
        ), 400

    nomes_validos = {
        servico_item["nome"]
        for itens in servicos.values()
        for servico_item in itens
    }

    if servico not in nomes_validos:
        return jsonify(
            erro="Escolha um serviço da lista."
        ), 400

    if not nome:
        return jsonify(
            erro="Informe o seu nome."
        ), 400

    if len(nome) > 80:
        return jsonify(
            erro="O nome está muito longo."
        ), 400

    if len(telefone) not in (10, 11):
        return jsonify(
            erro="Informe um telefone com DDD."
        ), 400

    if not validar_hora(hora):
        return jsonify(
            erro="Horário inválido."
        ), 400

    livres = {
        horario["hora"]
        for horario in horarios_do_dia(dia)
        if horario["livre"]
    }

    if hora not in livres:
        return jsonify(
            erro=(
                "Esse horário não está mais disponível. "
                "Escolha outro."
            )
        ), 409

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
                    servico,
                    dia.isoformat(),
                    hora,
                    nome,
                    telefone,
                    agora().isoformat(),
                ),
            )

    except sqlite3.IntegrityError:

        return jsonify(
            erro=(
                "Esse horário acabou de ser reservado. "
                "Escolha outro."
            )
        ), 409

    return jsonify(
        ok=True
    )


# ============================================================
# ADMIN — PROTEÇÃO DE LOGIN
# ============================================================
def exige_login(funcao):

    @wraps(funcao)
    def interna(
        *args,
        **kwargs,
    ):

        if (
            not ADMIN_SENHA
            or not session.get("admin")
        ):
            return redirect(
                url_for(
                    "admin_login"
                )
            )

        return funcao(
            *args,
            **kwargs,
        )

    return interna


# ============================================================
# ADMIN — LOGIN
# ============================================================
@app.route(
    "/admin/login",
    methods=[
        "GET",
        "POST",
    ],
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

        erro_csrf = exigir_csrf()

        if erro_csrf:

            return render_template(
                "login.html",
                salao=salao,
                desativado=False,
                erro=(
                    "Sessão de segurança inválida. "
                    "Recarregue a página."
                ),
            ), 400

        senha = request.form.get(
            "senha",
            "",
        )

        if hmac.compare_digest(
            senha.encode(),
            ADMIN_SENHA.encode(),
        ):

            session.clear()

            session["admin"] = True

            session["csrf_token"] = (
                secrets.token_urlsafe(32)
            )

            session.permanent = True

            return redirect(
                url_for("admin")
            )

        # Pequena espera contra tentativas
        # repetidas de senha.
        time.sleep(1)

        erro = "Senha incorreta."

    return render_template(
        "login.html",
        salao=salao,
        desativado=False,
        erro=erro,
    )


# ============================================================
# ADMIN — SAIR
# ============================================================
@app.route(
    "/admin/sair",
    methods=["POST"],
)
def admin_sair():

    if session.get("admin"):

        erro_csrf = exigir_csrf()

        if erro_csrf:
            return redirect(
                url_for("admin")
            )

    session.clear()

    return redirect(
        url_for(
            "admin_login"
        )
    )


# ============================================================
# ADMIN — PAINEL
# ============================================================
@app.route("/admin")
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
            (hoje,),
        ).fetchall()

        bloqueios = con.execute(
            """
            SELECT *
            FROM bloqueios
            WHERE data >= ?
            ORDER BY data, hora
            """,
            (hoje,),
        ).fetchall()

    grupos = []

    for marcacao in marcacoes:

        if (
            not grupos
            or grupos[-1]["data"]
            != marcacao["data"]
        ):

            grupos.append(
                {
                    "data": marcacao["data"],
                    "rotulo": rotulo_data(
                        marcacao["data"]
                    ),
                    "itens": [],
                }
            )

        grupos[-1]["itens"].append(
            {
                "id": marcacao["id"],
                "hora": marcacao["hora"],
                "servico": marcacao["servico"],
                "nome": marcacao["nome"],
                "telefone": marcacao["telefone"],
                "telefone_fmt": formatar_telefone(
                    marcacao["telefone"]
                ),
            }
        )

    lista_bloqueios = [
        {
            "id": bloqueio["id"],
            "rotulo": rotulo_data(
                bloqueio["data"]
            ),
            "hora": (
                bloqueio["hora"]
                or "Dia inteiro"
            ),
            "motivo": bloqueio["motivo"],
        }
        for bloqueio in bloqueios
    ]

    return render_template(
        "admin.html",
        salao=salao,
        grupos=grupos,
        total=len(marcacoes),
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
# ADMIN — CANCELAR AGENDAMENTO
# ============================================================
@app.route(
    "/admin/cancelar/<int:id>",
    methods=["POST"],
)
@exige_login
def admin_cancelar(id):

    erro_csrf = exigir_csrf()

    if erro_csrf:

        flash(
            (
                "Sessão de segurança inválida. "
                "Recarregue a página."
            ),
            "erro",
        )

        return redirect(
            url_for("admin")
        )

    with conectar() as con:

        con.execute(
            """
            DELETE FROM agendamentos
            WHERE id = ?
            """,
            (id,),
        )

    flash(
        (
            "Marcação cancelada. "
            "O horário voltou a ficar livre."
        ),
        "ok",
    )

    return redirect(
        url_for("admin")
    )


# ============================================================
# ADMIN — BLOQUEAR DIA/HORÁRIO
# ============================================================
@app.route(
    "/admin/bloquear",
    methods=["POST"],
)
@exige_login
def admin_bloquear():

    erro_csrf = exigir_csrf()

    if erro_csrf:

        flash(
            (
                "Sessão de segurança inválida. "
                "Recarregue a página."
            ),
            "erro",
        )

        return redirect(
            url_for("admin")
        )

    _, horarios = ler_config()

    motivo = (
        request.form
        .get(
            "motivo",
            "",
        )
        .strip()[:80]
    )

    hora = (
        request.form
        .get(
            "hora",
            "",
        )
        .strip()
    )

    try:

        dia = date.fromisoformat(
            request.form.get(
                "data",
                "",
            )
        )

    except (TypeError, ValueError):

        flash(
            "Escolha uma data válida para bloquear.",
            "erro",
        )

        return redirect(
            url_for("admin")
        )

    if dia < agora().date():

        flash(
            (
                "Não dá para bloquear "
                "um dia que já passou."
            ),
            "erro",
        )

        return redirect(
            url_for("admin")
        )

    if hora and hora not in horarios:

        flash(
            (
                "Esse horário não existe "
                "na sua lista de horários."
            ),
            "erro",
        )

        return redirect(
            url_for("admin")
        )

    iso = dia.isoformat()

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
                    hora,
                ),
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
                    hora,
                ),
            ).fetchone()[0]

        else:

            ja_existe = con.execute(
                """
                SELECT 1
                FROM bloqueios
                WHERE data = ?
                AND hora IS NULL
                """,
                (iso,),
            ).fetchone()

            conflitos = con.execute(
                """
                SELECT COUNT(*)
                FROM agendamentos
                WHERE data = ?
                """,
                (iso,),
            ).fetchone()[0]

        if ja_existe:

            flash(
                (
                    "Esse dia ou horário "
                    "já está bloqueado."
                ),
                "erro",
            )

            return redirect(
                url_for("admin")
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
                motivo,
            ),
        )

    if conflitos:

        flash(
            (
                f"Bloqueado! Atenção: já existia(m) "
                f"{conflitos} marcação(ões) nesse período. "
                "Elas continuam na agenda; "
                "cancele se precisar."
            ),
            "erro",
        )

    else:

        flash(
            (
                "Bloqueado! As clientes "
                "não conseguem mais marcar "
                "nesse período."
            ),
            "ok",
        )

    return redirect(
        url_for("admin")
    )


# ============================================================
# ADMIN — DESBLOQUEAR
# ============================================================
@app.route(
    "/admin/desbloquear/<int:id>",
    methods=["POST"],
)
@exige_login
def admin_desbloquear(id):

    erro_csrf = exigir_csrf()

    if erro_csrf:

        flash(
            (
                "Sessão de segurança inválida. "
                "Recarregue a página."
            ),
            "erro",
        )

        return redirect(
            url_for("admin")
        )

    with conectar() as con:

        con.execute(
            """
            DELETE FROM bloqueios
            WHERE id = ?
            """,
            (id,),
        )

    flash(
        "Bloqueio removido.",
        "ok",
    )

    return redirect(
        url_for("admin")
    )


# ============================================================
# ADMIN — CONFIGURAR HORÁRIOS
# ============================================================
@app.route(
    "/admin/horarios",
    methods=["POST"],
)
@exige_login
def admin_horarios():

    erro_csrf = exigir_csrf()

    if erro_csrf:

        flash(
            (
                "Sessão de segurança inválida. "
                "Recarregue a página."
            ),
            "erro",
        )

        return redirect(
            url_for("admin")
        )

    dias = sorted(
        {
            int(dia)
            for dia in request.form.getlist(
                "dias"
            )
            if (
                dia.isdigit()
                and 0 <= int(dia) <= 6
            )
        }
    )

    horarios = normalizar_horarios(
        re.split(
            r"[,;\s]+",
            request.form.get(
                "horarios",
                "",
            ),
        )
    )

    if not horarios:

        flash(
            (
                "Informe pelo menos "
                "um horário válido."
            ),
            "erro",
        )

        return redirect(
            url_for("admin")
        )

    salvar_config(
        "dias_abertos",
        ",".join(
            str(dia)
            for dia in dias
        ),
    )

    salvar_config(
        "horarios",
        ",".join(
            horarios
        ),
    )

    flash(
        "Horários de atendimento salvos!",
        "ok",
    )

    return redirect(
        url_for("admin")
    )


# ============================================================
# INICIALIZAÇÃO
# ============================================================

# Cria o banco caso ainda não exista.
criar_banco()


if __name__ == "__main__":
    # Para desenvolvimento local.
    #
    # O debug NÃO fica mais ativado obrigatoriamente.
    #
    # Se quiser ativá-lo:
    # FLASK_DEBUG=1

    app.run(
        debug=(
            os.environ.get(
                "FLASK_DEBUG"
            )
            == "1"
        )
    )