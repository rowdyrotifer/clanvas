### 0.2.1

* Cleaned up tab-completion code and hooked in to some nice cmd2
argparse integration, now tab completes flags and gives hints
with descriptions.
* Added command `ua` for uploading submissions to assignments.
* Made `lc -l` not require an enrollment term ID since sometimes a
course object does not always exactly model a course.
* Removed usage of deprecated canvasapi functions which were spraying
warning messages all over the place.
* Add categories to the `help` command.
* Add bounds (major version) to cmd2 and canvasapi dependencies to avoid
random breaking in the future.

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
