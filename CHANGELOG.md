### 0.2.4
* Fix bug which caused crash if no courses were associated with the account.
* Fix bug which caused crash if a course has no name.

### 0.2.3
* Change the default prompt colors to higher contrast.
* Make it easy to customize prompt colors by allowing `ESC` (`\x1B`) in the `prompt_format`
* Rename `prompt_string` to `prompt_format`
* Fix `pullf` which was totally broken by a change in the previous release. This is why adding more regression tests is priority!

### 0.2.2
* Fixes the version of `cmd2` to exactly `0.9.4` because of a bug that caused Clanvas to crash. This should be resolved in `0.9.6` of `cmd2`.
* Regression tests in the dev environment!

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
