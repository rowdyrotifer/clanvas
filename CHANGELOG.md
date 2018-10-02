### 0.2.0

Added commands for navigating announcements.

|  Command  | Meaning               |
|-----------|-----------------------|
| lann      | list announcements    |
| catann    | print announcements   |

* Fixed program crashing from a [cmd2](https://github.com/python-cmd2/cmd2) update

### 0.1.1

* Eagerly request courses in background on login.
* Tab-complete `wopen` command.
* Tab-complete the `-c` (`--course`) option for course-optional commands.
* Output directory (`-o`) option available to the `pullf` command.
* Assignment group grades and overall class grades shown in the `lg` command.
* Grades now colored based on score in the `lg` command.
* Quiet (`-q`) option available to the `login` command.

### 0.1.0

Added basic commands for navigating most basic resources.

|  Command  | Meaning               |
|-----------|-----------------------|
| lc        | list classes          |
| cc        | change current class  |
| la        | list assignments      |
| lg        | list grades           |
| pullf     | pull files            |
| wopen     | open in web interface |
| whoami    | show login info       |
| quit      | quit the shell        |