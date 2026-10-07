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


const hoje =
    new Date();


hoje.setHours(
    0,
    0,
    0,
    0
);


const anoInicial =
    hoje.getFullYear();


const mesInicial =
    hoje.getMonth();


let ano =
    anoInicial;


let mes =
    mesInicial;


let disponibilidade =
    {};


let diaEscolhido =
    null;


let horaEscolhida =
    null;


const $ = (id) =>
    document.getElementById(
        id
    );


const dois = (numero) =>
    String(
        numero
    ).padStart(
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


/* ============================================================
   MOEDA
============================================================ */

function formatarMoedaCentavos(
    valor
) {

    return (
        valor / 100
    ).toLocaleString(
        "pt-BR",
        {
            style:
                "currency",

            currency:
                "BRL"
        }
    );
}


/* ============================================================
   MENSAGENS
============================================================ */

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


/* ============================================================
   QUANTIDADE
============================================================ */

function limitarQuantidade(
    input
) {

    let valor =
        Number.parseInt(
            input.value,
            10
        );


    if (
        !Number.isFinite(
            valor
        )
        || valor < 1
    ) {

        valor =
            1;
    }


    if (
        valor > 10
    ) {

        valor =
            10;
    }


    input.value =
        String(
            valor
        );


    return valor;
}


/* ============================================================
   SERVIÇOS SELECIONADOS
============================================================ */

function servicosSelecionados() {

    const selecionados =
        [];


    document
        .querySelectorAll(
            ".servico-checkbox:checked"
        )
        .forEach(
            (checkbox) => {


                const card =
                    checkbox.closest(
                        ".servico-card"
                    );


                const inputQuantidade =
                    card?.querySelector(
                        ".servico-qtd"
                    );


                const quantidade =
                    inputQuantidade

                        ? limitarQuantidade(
                            inputQuantidade
                        )

                        : 1;


                selecionados.push(
                    {

                        nome:
                            checkbox.dataset.nome,

                        quantidade:
                            quantidade,

                        valor:
                            Number.parseInt(
                                checkbox.dataset.valor,
                                10
                            ) || 0

                    }
                );

            }
        );


    return selecionados;
}


/* ============================================================
   RESUMO DE SERVIÇOS
============================================================ */

function atualizarResumoServicos() {

    const selecionados =
        servicosSelecionados();


    const lista =
        $("resumo-lista");


    const totalElemento =
        $("resumo-total");


    const contador =
        $("contador-servicos");


    let total =
        0;


    document
        .querySelectorAll(
            ".servico-card"
        )
        .forEach(
            (card) => {


                const checkbox =
                    card.querySelector(
                        ".servico-checkbox"
                    );


                const quantidade =
                    card.querySelector(
                        ".quantidade-servico"
                    );


                card.classList.toggle(
                    "selecionado",
                    checkbox.checked
                );


                if (
                    quantidade
                ) {

                    quantidade.hidden =
                        !checkbox.checked;
                }

            }
        );


    selecionados.forEach(
        (item) => {

            total +=
                item.valor
                * item.quantidade;

        }
    );


    contador.textContent =

        selecionados.length === 1

            ? "1 selecionado"

            : `${selecionados.length} selecionados`;


    totalElemento.textContent =
        formatarMoedaCentavos(
            total
        );


    if (
        selecionados.length === 0
    ) {

        lista.innerHTML =
            '<p class="resumo-vazio">Nenhum serviço selecionado.</p>';


        atualizarEstadoBotao();


        return;
    }


    lista.innerHTML =
        "";


    selecionados.forEach(
        (item) => {


            const linha =
                document.createElement(
                    "div"
                );


            linha.className =
                "resumo-item";


            const nome =
                document.createElement(
                    "span"
                );


            nome.textContent =

                item.quantidade > 1

                    ? `${item.nome} × ${item.quantidade}`

                    : item.nome;


            const subtotal =
                document.createElement(
                    "strong"
                );


            subtotal.textContent =
                formatarMoedaCentavos(
                    item.valor
                    * item.quantidade
                );


            linha.append(
                nome,
                subtotal
            );


            lista.appendChild(
                linha
            );

        }
    );


    atualizarEstadoBotao();
}


/* ============================================================
   BOTÃO CONFIRMAR
============================================================ */

function atualizarEstadoBotao() {

    botaoConfirmar.disabled = !(

        servicosSelecionados().length > 0

        && diaEscolhido

        && horaEscolhida

        && $("nome")?.value.trim()

        && $("telefone")?.value.trim()

    );
}


/* ============================================================
   CARREGAR MÊS
============================================================ */

async function carregarMes(
    limparAviso = true
) {

    const titulo =
        $("mes-titulo");


    titulo.textContent =
        `${MESES[mes]} ${ano}`;


    if (
        limparAviso
    ) {

        limparMensagem();
    }


    const indice =

        (
            ano
            - anoInicial
        )
        * 12

        + (
            mes
            - mesInicial
        );


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

                        "Accept":
                            "application/json"

                    }

                }

            );


        if (
            !resposta.ok
        ) {

            throw new Error(
                "Falha ao carregar o mês."
            );
        }


        disponibilidade =
            await resposta.json();


        desenharDias();


    } catch (
        erro
    ) {


        disponibilidade =
            {};


        desenharDias();


        mostrarMensagem(

            "Não foi possível carregar o calendário. Tente novamente.",

            true

        );

    }

}


/* ============================================================
   DESENHAR CALENDÁRIO
============================================================ */

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


    const deslocamento =
        (
            primeiro.getDay()
            + 6
        )
        % 7;


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
            chave(
                data
            );


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


/* ============================================================
   ESCOLHER DIA
============================================================ */

async function escolherDia(
    dataISO,
    limparAviso = true
) {

    diaEscolhido =
        dataISO;


    horaEscolhida =
        null;


    if (
        limparAviso
    ) {

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

                        "Accept":
                            "application/json"

                    }

                }

            );


        if (
            !resposta.ok
        ) {

            throw new Error(
                "Falha ao carregar horários."
            );
        }


        const lista =
            await resposta.json();


        area.innerHTML =
            "";


        if (
            !Array.isArray(
                lista
            )
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


                if (
                    !item.livre
                ) {


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


    } catch (
        erro
    ) {


        area.innerHTML =
            "";


        mostrarMensagem(

            "Não foi possível carregar os horários. Tente novamente.",

            true

        );

    }


    atualizarEstadoBotao();

}


/* ============================================================
   TELEFONE
============================================================ */

function formatarTelefoneInput(
    valor
) {

    const numeros =
        valor
            .replace(
                /\D/g,
                ""
            )
            .slice(
                0,
                11
            );


    if (
        numeros.length <= 2
    ) {

        return numeros;
    }


    if (
        numeros.length <= 6
    ) {

        return (
            `(${numeros.slice(0, 2)}) `
            + numeros.slice(2)
        );
    }


    if (
        numeros.length <= 10
    ) {

        return (
            `(${numeros.slice(0, 2)}) `
            + `${numeros.slice(2, 6)}-`
            + numeros.slice(6)
        );
    }


    return (

        `(${numeros.slice(0, 2)}) `

        + `${numeros.slice(2, 7)}-`

        + numeros.slice(7)

    );

}


/* ============================================================
   CONFIRMAR AGENDAMENTO
============================================================ */

async function confirmar() {

    const servicos =
        servicosSelecionados()
            .map(
                (item) => (
                    {

                        nome:
                            item.nome,

                        quantidade:
                            item.quantidade

                    }
                )
            );


    const nome =
        $("nome")
            .value
            .trim();


    const telefone =
        $("telefone")
            .value
            .trim();


    if (

        servicos.length === 0

        || !diaEscolhido

        || !horaEscolhida

        || !nome

        || !telefone

    ) {


        mostrarMensagem(

            "Escolha os serviços, a data, o horário e preencha seus dados.",

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

                    method:
                        "POST",


                    headers: {

                        "Content-Type":
                            "application/json",

                        "Accept":
                            "application/json",

                        "X-CSRF-Token":
                            csrfToken

                    },


                    body:
                        JSON.stringify(
                            {

                                servicos:
                                    servicos,

                                data:
                                    diaEscolhido,

                                hora:
                                    horaEscolhida,

                                nome:
                                    nome,

                                telefone:
                                    telefone

                            }
                        )

                }

            );


        const dados =
            await resposta
                .json()
                .catch(
                    () => (
                        {}
                    )
                );


        if (
            !resposta.ok
        ) {


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


                if (
                    diaAnterior
                ) {

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


        $("nome").value =
            "";


        $("telefone").value =
            "";


        document
            .querySelectorAll(
                ".servico-checkbox"
            )
            .forEach(
                (checkbox) => {

                    checkbox.checked =
                        false;

                }
            );


        document
            .querySelectorAll(
                ".servico-qtd"
            )
            .forEach(
                (input) => {

                    input.value =
                        "1";

                }
            );


        atualizarResumoServicos();


        horaEscolhida =
            null;


        const diaAnterior =
            diaEscolhido;


        await carregarMes(
            false
        );


        if (
            diaAnterior
        ) {


            await escolherDia(
                diaAnterior,
                false
            );

        }


        const total =

            dados.total

                ? ` Valor estimado: ${dados.total}.`

                : "";


        mostrarMensagem(

            `Agendamento realizado com sucesso!${total}`,

            false

        );


    } catch (
        erro
    ) {


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


/* ============================================================
   MÊS ANTERIOR
============================================================ */

$("mes-anterior")
    .addEventListener(

        "click",

        () => {


            if (
                mes === 0
            ) {

                mes =
                    11;

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


/* ============================================================
   PRÓXIMO MÊS
============================================================ */

$("mes-proximo")
    .addEventListener(

        "click",

        () => {


            if (
                mes === 11
            ) {


                mes =
                    0;

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


/* ============================================================
   EVENTOS DOS SERVIÇOS
============================================================ */

document
    .querySelectorAll(
        ".servico-checkbox"
    )
    .forEach(
        (checkbox) => {


            checkbox.addEventListener(

                "change",

                () => {


                    limparMensagem();


                    atualizarResumoServicos();

                }

            );

        }
    );


/* ============================================================
   DIMINUIR QUANTIDADE
============================================================ */

document
    .querySelectorAll(
        ".qtd-menos"
    )
    .forEach(
        (botao) => {


            botao.addEventListener(

                "click",

                () => {


                    const card =
                        botao.closest(
                            ".servico-card"
                        );


                    const input =
                        card.querySelector(
                            ".servico-qtd"
                        );


                    input.value =
                        Math.max(

                            1,

                            limitarQuantidade(
                                input
                            )
                            - 1

                        );


                    atualizarResumoServicos();

                }

            );

        }
    );


/* ============================================================
   AUMENTAR QUANTIDADE
============================================================ */

document
    .querySelectorAll(
        ".qtd-mais"
    )
    .forEach(
        (botao) => {


            botao.addEventListener(

                "click",

                () => {


                    const card =
                        botao.closest(
                            ".servico-card"
                        );


                    const input =
                        card.querySelector(
                            ".servico-qtd"
                        );


                    input.value =
                        Math.min(

                            10,

                            limitarQuantidade(
                                input
                            )
                            + 1

                        );


                    atualizarResumoServicos();

                }

            );

        }
    );


/* ============================================================
   ALTERAR QUANTIDADE MANUALMENTE
============================================================ */

document
    .querySelectorAll(
        ".servico-qtd"
    )
    .forEach(
        (input) => {


            input.addEventListener(

                "input",

                () => {


                    limitarQuantidade(
                        input
                    );


                    atualizarResumoServicos();

                }

            );

        }
    );


/* ============================================================
   EVENTOS GERAIS
============================================================ */

$("confirmar")
    .addEventListener(
        "click",
        confirmar
    );


$("nome")
    .addEventListener(
        "input",
        atualizarEstadoBotao
    );


$("telefone")
    .addEventListener(

        "input",

        (evento) => {


            evento.target.value =
                formatarTelefoneInput(
                    evento.target.value
                );


            atualizarEstadoBotao();

        }

    );


/* ============================================================
   INICIALIZAÇÃO
============================================================ */

atualizarResumoServicos();

carregarMes();

atualizarEstadoBotao();
