# Clanvas
Command-line shell client for the [Canvas Learning Management System](https://github.com/instructure/canvas-lms)

### Installation

Clanvas is hosted on [PyPi](https://pypi.python.org/pypi/clanvas) and can be installed with `pip`

```
pip install clanvas
```

`clanvas` should now be available on your path.

### Example Usage
Start the Clanvas shell
```
bob@host:~$ clanvas
$
```
Login using an API token (see Generating an API Token)
```
$ login https://canvas.school.edu bOYc5cOIldA3eB9NTr7X0Um9Z8TPMACb0HtdgHTMtp10T5UKH0b4HOqTmOCvWZlYRpJ9dN
Logged in as Bob Roberts (bmr23)
bmr23@canvas.school.edu:~:~ $
```
Run commands
```
bmr23@canvas.school.edu:~:~ $ lc -l
EECS 325  7832  Spring 2018  Computer Networks (100/5013)
EECS 338  6939  Spring 2018  Operating Systems (100/4593)
EECS 391  7136  Spring 2018  Artificial Intelligence (100/4163)
EECS 345  6937  Spring 2018  Programming Language Concepts (100/4699)
bmr23@canvas.school.edu:~:~ $ cc 325
bmr23@canvas.school.edu:EECS 325:~ $ lg -g
Computer Networks (100/5013)
├── Quizzes
│   ├── Quiz 1 100/100 100%
│   ├── Quiz 2 85/100 85%
│   └── Quiz 3 95/100 95%
├── Exams
│   └── Exam 1 86/100 86%
└── Homework
    ├── HW 1 20/20 100%
    ├── HW 2 18/20 90%
    └── HW 3 17/20 85%
bmr23@canvas.school.edu:EECS 325:~ $ pullf
bmr23@canvas.school.edu:EECS 325:~ $ tree ~/canvas/courses/EECS325-7832/files
/home/bob/canvas/courses/EECS325-7832/files
├── HW1_2018S.pdf
├── HW2_2018S.pdf
├── HW3-2018S.pdf
├── HW Solutions
│   └── HW1_2018S_Solutions
├── Lecture Notes
│   ├── Lecture1.ppt
│   ├── Lecture2.ppt
│   ├── Lecture3_Layering_AppLayerOverview.ppt
│   ├── Lecture4_5_Web.ppt
│   ├── Lecture6_DNS_CDN.ppt
│   ├── Lecture7_SMTP_P2P_SPAM.ppt
│   ├── Lecture8-Sockets_TransportIntro.ppt
│   └── Lecture9-UDP_RelXmit.ppt
├── Project1Files.zip
├── Project1Instructions.pdf
└── Syllabus.pdf
```

### Automatic Login
Clanvas will look for a `.clanvasrc` file in your home directory to execute initial commands. Here you can insert the login command so that logging in is done automatically on start-up

```
echo "login https://canvas.school.edu bOYc5cOIldA3eB9NTr7X0Um9Z8TPMACb0HtdgHTMtp10T5UKH0b4HOqTmOCvWZlYRpJ9dN" > ~/.clanvasrc
```

Additionally, you should change the permissions of this file so that other users of your computer cannot read your API token and consequently access your account.

```
chmod 600 ~/.clanvasrc
```

### Available Commands

In the Clanvas shell, all commands already on your system PATH are available.

In addition, the shell provides the following commands:

|  Command  | Meaning               |
|-----------|-----------------------|
| lc        | list classes          |
| cc        | change current class  |
| la        | list assignments      |
| lg        | list grades           |
| wopen     | open in web interface |
| whoami    | show login info       |
| quit      | quit the shell        |

Use the `-h` flag to show usage details for any command.

### Generating an API Token
1. Navigate to /profile/settings
2. Under the "Approved Integrations" section, click the button to generate a new access token.
3. Once the token is generated, you cannot view it again, so you'll have to generate a new token if it is lost.

## Contributing
Currently the project is in an exploratory phase. I am implementing features that that I find useful and trying to tweak them as I go along to find a balance of easy-to-use and powerful. I would greatly appreciate feedback about what is missing or what interfaces should be changed.

Once the general interfaces and most core commands are solidified, then tests will be added and a formal TODO list may be created.

## Built With
* [cmd2](https://github.com/python-cmd2/cmd2)
* [CanvasAPI](https://github.com/ucfopen/canvasapi)

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
