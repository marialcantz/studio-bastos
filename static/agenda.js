const MESES = [
    "Janeiro",
    "Fevereiro",
    "Março",
    "Abril",
    "Maio",
    "Junho",
    "Julho",
    "Agosto",
    "Setembro",
    "Outubro",
    "Novembro",
    "Dezembro"
];


const hoje = new Date();

hoje.setHours(
    0,
    0,
    0,
    0
);


const anoInicial = hoje.getFullYear();
const mesInicial = hoje.getMonth();


let ano = anoInicial;
let mes = mesInicial;

let disponibilidade = {};

let diaEscolhido = null;
let horaEscolhida = null;


const $ = (id) =>
    document.getElementById(id);


const dois = (numero) =>
    String(numero).padStart(
        2,
        "0"
    );


const chave = (data) =>
    `${data.getFullYear()}-${dois(data.getMonth() + 1)}-${dois(data.getDate())}`;


const csrfToken =
    document.querySelector(
        'meta[name="csrf-token"]'
    )?.content || "";


const botaoConfirmar =
    $("confirmar");


// ============================================================
// MENSAGENS
// ============================================================
function mostrarMensagem(
    texto,
    erro = false
) {

    const elemento =
        $("mensagem");

    elemento.textContent =
        texto;

    elemento.className =
        `mensagem ${erro ? "erro" : "ok"}`;

    elemento.hidden =
        false;
}


function limparMensagem() {

    const elemento =
        $("mensagem");

    elemento.textContent =
        "";

    elemento.className =
        "mensagem";

    elemento.hidden =
        true;
}


// ============================================================
// BOTÃO DE CONFIRMAÇÃO
// ============================================================
function atualizarEstadoBotao() {

    botaoConfirmar.disabled = !(
        $("servico")?.value &&
        diaEscolhido &&
        horaEscolhida &&
        $("nome")?.value.trim() &&
        $("telefone")?.value.trim()
    );
}


// ============================================================
// CARREGAR MÊS
// ============================================================
async function carregarMes(
    limparAviso = true
) {

    const titulo =
        $("mes-titulo");


    titulo.textContent =
        `${MESES[mes]} ${ano}`;


    if (limparAviso) {
        limparMensagem();
    }


    const indice =
        (ano - anoInicial) * 12
        + (mes - mesInicial);


    $("mes-anterior").disabled =
        indice <= 0;


    $("mes-proximo").disabled =
        indice >= 11;


    try {

        const resposta =
            await fetch(
                `/api/mes?ano=${ano}&mes=${mes + 1}`,
                {
                    headers: {
                        "Accept": "application/json"
                    }
                }
            );


        if (!resposta.ok) {

            throw new Error(
                "Falha ao carregar o mês."
            );

        }


        disponibilidade =
            await resposta.json();


        desenharDias();

    } catch (erro) {

        disponibilidade = {};

        desenharDias();


        mostrarMensagem(
            "Não foi possível carregar o calendário. Tente novamente.",
            true
        );

    }
}


// ============================================================
// DESENHAR CALENDÁRIO
// ============================================================
function desenharDias() {

    const grade =
        $("dias");


    grade.innerHTML =
        "";


    const primeiro =
        new Date(
            ano,
            mes,
            1
        );


    const ultimo =
        new Date(
            ano,
            mes + 1,
            0
        );


    // JavaScript:
    // domingo = 0
    //
    // Nosso calendário:
    // segunda = 0
    const deslocamento =
        (primeiro.getDay() + 6) % 7;


    for (
        let i = 0;
        i < deslocamento;
        i++
    ) {

        const vazio =
            document.createElement(
                "span"
            );


        vazio.className =
            "dia vazio";


        vazio.setAttribute(
            "aria-hidden",
            "true"
        );


        grade.appendChild(
            vazio
        );
    }


    for (
        let numero = 1;
        numero <= ultimo.getDate();
        numero++
    ) {

        const data =
            new Date(
                ano,
                mes,
                numero
            );


        const dataISO =
            chave(data);


        const livres =
            disponibilidade[
                dataISO
            ];


        const botao =
            document.createElement(
                "button"
            );


        botao.type =
            "button";


        botao.className =
            "dia";


        botao.textContent =
            numero;


        botao.dataset.data =
            dataISO;


        if (
            livres === undefined
        ) {

            botao.classList.add(
                "fechado"
            );


            botao.disabled =
                true;


            botao.setAttribute(
                "aria-label",
                `${numero} de ${MESES[mes]}, fechado`
            );

        } else if (
            livres === 0
        ) {

            botao.classList.add(
                "lotado"
            );


            botao.disabled =
                true;


            botao.setAttribute(
                "aria-label",
                `${numero} de ${MESES[mes]}, lotado`
            );

        } else {

            botao.classList.add(
                "livre"
            );


            botao.setAttribute(
                "aria-label",
                `${numero} de ${MESES[mes]}, ${livres} horários livres`
            );


            botao.addEventListener(
                "click",
                () =>
                    escolherDia(
                        dataISO
                    )
            );

        }


        if (
            dataISO === diaEscolhido
        ) {

            botao.classList.add(
                "escolhido"
            );


            botao.setAttribute(
                "aria-pressed",
                "true"
            );

        }


        grade.appendChild(
            botao
        );
    }
}


// ============================================================
// ESCOLHER DIA
// ============================================================
async function escolherDia(
    dataISO,
    limparAviso = true
) {

    diaEscolhido =
        dataISO;


    horaEscolhida =
        null;


    if (limparAviso) {
        limparMensagem();
    }


    atualizarEstadoBotao();

    desenharDias();


    const area =
        $("horarios");


    area.innerHTML =
        '<p class="carregando">Carregando horários...</p>';


    try {

        const resposta =
            await fetch(
                `/api/horarios?data=${encodeURIComponent(dataISO)}`,
                {
                    headers: {
                        "Accept": "application/json"
                    }
                }
            );


        if (!resposta.ok) {

            throw new Error(
                "Falha ao carregar horários."
            );

        }


        const lista =
            await resposta.json();


        area.innerHTML =
            "";


        if (
            !Array.isArray(lista)
            || lista.length === 0
        ) {

            area.innerHTML =
                '<p class="sem-horarios">Não há horários disponíveis neste dia.</p>';


            atualizarEstadoBotao();

            return;
        }


        lista.forEach(
            (item) => {

                const botao =
                    document.createElement(
                        "button"
                    );


                botao.type =
                    "button";


                botao.className =
                    "hora";


                botao.textContent =
                    item.hora;


                if (!item.livre) {

                    botao.classList.add(
                        "ocupado"
                    );


                    botao.disabled =
                        true;


                    botao.setAttribute(
                        "aria-label",
                        `${item.hora}, indisponível`
                    );

                } else {

                    botao.classList.add(
                        "livre"
                    );


                    botao.addEventListener(
                        "click",
                        () => {

                            horaEscolhida =
                                item.hora;


                            document
                                .querySelectorAll(
                                    ".hora.escolhido"
                                )
                                .forEach(
                                    (elemento) => {

                                        elemento
                                            .classList
                                            .remove(
                                                "escolhido"
                                            );


                                        elemento
                                            .setAttribute(
                                                "aria-pressed",
                                                "false"
                                            );

                                    }
                                );


                            botao.classList.add(
                                "escolhido"
                            );


                            botao.setAttribute(
                                "aria-pressed",
                                "true"
                            );


                            atualizarEstadoBotao();

                        }
                    );

                }


                area.appendChild(
                    botao
                );

            }
        );

    } catch (erro) {

        area.innerHTML =
            "";


        mostrarMensagem(
            "Não foi possível carregar os horários. Tente novamente.",
            true
        );

    }


    atualizarEstadoBotao();
}


// ============================================================
// CONFIRMAR AGENDAMENTO
// ============================================================
async function confirmar() {

    const servico =
        $("servico").value;


    const nome =
        $("nome")
            .value
            .trim();


    const telefone =
        $("telefone")
            .value
            .trim();


    if (
        !servico ||
        !diaEscolhido ||
        !horaEscolhida ||
        !nome ||
        !telefone
    ) {

        mostrarMensagem(
            "Preencha serviço, data, horário, nome e WhatsApp.",
            true
        );

        return;
    }


    botaoConfirmar.disabled =
        true;


    botaoConfirmar.textContent =
        "Agendando...";


    limparMensagem();


    try {

        const resposta =
            await fetch(
                "/api/agendar",
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json",

                        "Accept":
                            "application/json",

                        "X-CSRF-Token":
                            csrfToken
                    },

                    body: JSON.stringify(
                        {
                            servico,
                            data:
                                diaEscolhido,
                            hora:
                                horaEscolhida,
                            nome,
                            telefone
                        }
                    )
                }
            );


        const dados =
            await resposta
                .json()
                .catch(
                    () => ({})
                );


        // ====================================================
        // ERRO
        // ====================================================
        if (!resposta.ok) {

            const mensagemErro =
                dados.erro
                || "Não foi possível concluir o agendamento.";


            if (
                resposta.status === 409
            ) {

                const diaAnterior =
                    diaEscolhido;


                await carregarMes(
                    false
                );


                if (diaAnterior) {

                    await escolherDia(
                        diaAnterior,
                        false
                    );

                }
            }


            mostrarMensagem(
                mensagemErro,
                true
            );


            return;
        }


        // ====================================================
        // SUCESSO
        // ====================================================
        $("nome").value =
            "";


        $("telefone").value =
            "";


        horaEscolhida =
            null;


        const diaAnterior =
            diaEscolhido;


        await carregarMes(
            false
        );


        if (diaAnterior) {

            await escolherDia(
                diaAnterior,
                false
            );

        }


        mostrarMensagem(
            "Agendamento realizado com sucesso!",
            false
        );

    } catch (erro) {

        mostrarMensagem(
            "Não foi possível concluir o agendamento. Verifique sua conexão e tente novamente.",
            true
        );

    } finally {

        botaoConfirmar.textContent =
            "Confirmar agendamento";


        atualizarEstadoBotao();

    }
}


// ============================================================
// MÊS ANTERIOR
// ============================================================
$("mes-anterior")
    .addEventListener(
        "click",
        () => {

            if (
                mes === 0
            ) {

                mes = 11;
                ano--;

            } else {

                mes--;

            }


            diaEscolhido =
                null;


            horaEscolhida =
                null;


            $("horarios").innerHTML =
                '<p class="sem-horarios">Escolha um dia para ver os horários.</p>';


            atualizarEstadoBotao();

            carregarMes();

        }
    );


// ============================================================
// PRÓXIMO MÊS
// ============================================================
$("mes-proximo")
    .addEventListener(
        "click",
        () => {

            if (
                mes === 11
            ) {

                mes = 0;
                ano++;

            } else {

                mes++;

            }


            diaEscolhido =
                null;


            horaEscolhida =
                null;


            $("horarios").innerHTML =
                '<p class="sem-horarios">Escolha um dia para ver os horários.</p>';


            atualizarEstadoBotao();

            carregarMes();

        }
    );


// ============================================================
// EVENTOS
// ============================================================
$("confirmar")
    .addEventListener(
        "click",
        confirmar
    );


$("servico")
    .addEventListener(
        "change",
        atualizarEstadoBotao
    );


$("nome")
    .addEventListener(
        "input",
        atualizarEstadoBotao
    );


$("telefone")
    .addEventListener(
        "input",
        atualizarEstadoBotao
    );


// ============================================================
// INICIALIZAÇÃO
// ============================================================
carregarMes();

atualizarEstadoBotao();