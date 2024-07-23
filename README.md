# NEPTUNCLI

## Run Application

```shell
(venv) $ python -m neptun -v
neptun v0.1.0

(venv) $ python -m neptun --help
Usage: neptun [OPTIONS] COMMAND [ARGS]...

Options:
  -v, --version         Show the application's version and exit.
  --install-completion  Install completion for the current shell.
  --show-completion     Show completion for the current shell, to copy it
                        or customize the installation.

  --help                Show this message and exit.
```

* Make sure you create a `neptun/config/config.ini`-file if you are getting a error message(This is due to the non installed cli tool).


## Useful
* https://realpython.com/python-typer-cli/ -> project-structure & explanation
* https://www.codecentric.de/wissens-hub/blog/lets-build-a-modern-cmd-tool-with-python-using-typer-and-rich -> rich & taper
* https://www.freecodecamp.org/news/how-to-build-and-publish-python-packages-with-poetry/ -> poetry docs
* https://github.com/tmbo/questionary/tree/master/examples-> selections, inputs