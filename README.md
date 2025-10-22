# test-manager
Software test management tool.

# Contents

1. [Introduction](#1-introduction)
2. [System Requirements](#2-system-requirements)
3. [Installation](#3-installation)

## 1. Introduction

Test Manager is a test management system that allows you to create, organize, execute, and track software test cases. Its focus is to replace scattered spreadsheets and documents with a centralized platform.

Using generic tools like spreadsheets and documents to manage software testing is inefficient. This leads to problems like disorganization, lack of traceability, limited collaboration, and ineffective reporting.

The system will centralize test management, increasing the efficiency of QA teams. This will lead to improved software quality, reduced bugs in production, and accelerated development cycles, allowing teams to focus on creating, not managing, documents.

## 2. System Requirements

The server environment should consist of:
- web-server: Nginx x.x
- Python > 3.12
- DBMS
  - MySQL x.x.x
  - MariaDB x.x
  - Postgres x.x

Tested on web browsers:
- Firefox
- Chrome

## 3. Installation

### With Docker

Use `docker-compose up` to start containers in the foreground.

### Without Docker

Below we detail the basic steps for installation on any system.

1. First, transfer the file to your web server using your preferred method (ftp, scp, etc).

You will need to telnet/ssh into the server machine for the next steps.

2. Then unzip it to the desired directory.

The usual command is: `tar zxvf <filename.tar.gz>`

At this point, you may want to rename the directory to something other than 'test-manager'.

3. Launch the web installer
We'll create the necessary database tables and a basic configuration file.
On your web server, go to http://yoursite/ or a similar URL and follow the instructions.