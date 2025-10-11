# test-manager
Ferramenta de gestão de testes de software.

# Conteúdos

1. [Introdução](#1-introdução)
2. [Requisitos de Sistema](#2-requisitos-de-sistema)
3. [Instalação](#3-instalação)

## 1. Introdução

Test Manager é um sistema de gerenciamento de testes que permita a criação, organização, execução e rastreabilidade de casos de testes de software.
O foco é substituir planilhas e documentos dispersos por uma plataforma centralizada.

O uso de ferramentas genéricas como planilhas e documentos para gerenciar testes de software é ineficiente.
Isso causa problemas como desorganização, falta de rastreabilidade, colaboração limitada e relatórios ineficazes.

O sistema irá centralizar o gerenciamento de testes, aumentando a eficiência das equipes de QA.
Isso levará a uma melhoria na qualidade do software, redução de bugs em produção e aceleração do ciclo de desenvolvimento, permitindo que as equipes se concentrem em criar e não em gerenciar documentos.

## 2. Requisitos de Sistema

O ambiente do servidor deve consistir de:
- web-server: Nginx x.x
- Python > 3.10
- DBMS
  - MySQL x.x.x
  - MariaDB x.x
  - Postgres x.x

Testado nos nevegadores web:
- Firefox
- Chrome

## 3. Instalação

### Com Docker
use [README.docker.md](README.docker.md)

### Sem Docker

A seguir detalhamos as etapas básicas para instalação em qualquer sistema.

1. Primeiro, transfira o arquivo para o seu servidor web usando o método que você preferir (ftp, scp, etc).

Você precisará fazer telnet/ssh na máquina servidora para as próximas etapas.

2. Em seguida, descompacte-o no diretório desejado.

O comando usual é:

`
tar zxvf <filename.tar.gz>
`

Neste ponto, você pode querer renomear o diretório para algo diferente de 'testmanager'.

3. Inicie o instalador web
Criaremos as tabelas de banco de dados necessárias e um arquivo de configuração básico.
No seu servidor web, acesse http://seusite/testmanager/ ou URL similar e siga as instruções.
