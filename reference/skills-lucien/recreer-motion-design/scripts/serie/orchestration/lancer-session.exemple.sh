#!/bin/bash
cd /srv/faq-v4/1-temps
export IS_SANDBOX=1 SCALAI_NO_SOUND=1
exec claude --remote-control "FAQ1 v4" -n "FAQ1 v4" --model claude-opus-5-5 --dangerously-skip-permissions "$(cat CONSIGNE.txt)"
