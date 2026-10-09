import sys

from onboarding.cli import main

# En Windows, si la salida no es la consola (Git Bash, redirección a archivo),
# Python usa cp1252 y las tildes y eñes salen mal.
sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

sys.exit(main())
