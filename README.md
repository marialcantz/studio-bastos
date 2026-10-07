# Studio Bastos 💅

Sistema web de agendamento desenvolvido para o **Studio Bastos**, permitindo que clientes consultem horários disponíveis e realizem agendamentos diretamente pelo site.

O projeto também possui uma área administrativa protegida por senha, onde é possível acompanhar e gerenciar a agenda do salão.

🔗 **Site em produção:**  
https://marina2222.pythonanywhere.com

---

## Sobre o projeto

O Studio Bastos foi desenvolvido com o objetivo de facilitar o processo de agendamento entre o salão e suas clientes.

Pelo site, a cliente pode:

- visualizar os serviços disponíveis;
- escolher uma data;
- consultar os horários livres;
- informar nome e WhatsApp;
- realizar o agendamento online.

O sistema verifica a disponibilidade antes de confirmar a reserva, evitando que duas clientes ocupem o mesmo horário.

---

## Área administrativa

O projeto possui uma área exclusiva para administração.

Por meio dela é possível:

- visualizar os próximos agendamentos;
- consultar nome, serviço, horário e telefone da cliente;
- cancelar agendamentos;
- bloquear horários específicos;
- bloquear um dia inteiro;
- remover bloqueios;
- configurar os dias de atendimento;
- configurar os horários disponíveis.

A área administrativa possui autenticação por senha.

---

## Tecnologias utilizadas

- Python
- Flask
- SQLite
- HTML5
- CSS3
- JavaScript
- Jinja2
- PythonAnywhere
- Git
- GitHub

---

## Estrutura do projeto

```text
studio-bastos/
│
├── app.py
├── .gitignore
│
├── static/
│   ├── agenda.js
│   ├── logo.png
│   └── style.css
│
└── templates/
    ├── admin.html
    ├── index.html
    └── login.html
