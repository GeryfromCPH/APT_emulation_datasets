#!/usr/bin/env bash
# Environment for GUI automation
export NO_AT_BRIDGE=1
export DISPLAY=:0
export XAUTHORITY="$HOME/.Xauthority"

# Check for xdotool
if ! command -v xdotool >/dev/null; then
  echo "xdotool not found - GUI typing actions will be skipped" >&2
fi
# Simulate realistic office behavior on a minimal Linux workstation

MIN_PAUSE=30
MAX_PAUSE=120

mkdir -p "$HOME/simlogs"

# List of websites to simulate browsing
urls=(
    "https://exchange.apttestbed.local"
    "https://mail.apttestbed.local"
    "https://news.ycombinator.com"
    "https://stackoverflow.com"
    "https://github.com"
    "https://youtube.com"
)

# Idle and pause functions
random_sleep() { sleep $(( RANDOM % (MAX_PAUSE - MIN_PAUSE + 1) + MIN_PAUSE )); }
short_pause() { sleep $(( RANDOM % 11 + 5 )); }
maybe_long_idle() { (( RANDOM % 10 < 1 )) && sleep $(( RANDOM % 601 + 600 )); }

while true; do
  # Simulated office task pool
  actions=(
    "xdg-open ${urls[$((RANDOM % ${#urls[@]}))]} && sleep $((RANDOM % 10 + 10)) && pkill -f xdg-open"
    "echo 'Reminder: Update Q2 report' > $HOME/simlogs/note_$(date +%s).txt"
    "ls -lh /home > $HOME/simlogs/home_listing_$(date +%s).log"
    "uptime > $HOME/simlogs/uptime_$(date +%s).log"
    "df -h > $HOME/simlogs/disk_usage_$(date +%s).log"
    "echo -e 'Subject: Office Check-in\n\nAll systems normal.' | ssmtp johncena@apttestbed.local 2>/dev/null || true"
    "bash -c 'tmp=\$HOME/simlogs/report_\$(date +%s).txt; for i in {1..30}; do echo \"Line \$i: weekly report.\" >> \$tmp; done; libreoffice --headless --convert-to odt --outdir \$HOME/simlogs \$tmp; rm \$tmp'"
    "xdg-open $HOME/Documents && sleep 5 && pkill -f nautilus"
    "mkdir -p $HOME/shared && cp /etc/hosts $HOME/shared/hosts_backup_$(date +%s).txt"
    "echo 'Reminder: submit timecard' >> $HOME/simlogs/todo.txt"
    "lp /etc/hosts"
    "nmcli radio wifi off && sleep 2 && nmcli radio wifi on"
    "bash -c 'echo \"* * * * * echo Cron job executed >> \$HOME/simlogs/cronrun_\$(date +%s).log\" | crontab; sleep 65; crontab -r'",
    "wall 'Reminder: stand-up meeting in 5 minutes'",
    "xdg-email --subject \"Weekly Update\" --body \"All good here!\" john.cena@apttestbed.local",
    "bash -c 'mkdir -p \$HOME/network_share && sudo mount -t cifs //fileserver/shared \$HOME/network_share -o guest,ro && ls -l \$HOME/network_share > \$HOME/simlogs/share_contents_\$(date +%s).log && sudo umount \$HOME/network_share'",
    "grep -R \"TODO\" \$HOME/Documents > \$HOME/simlogs/todo_matches_\$(date +%s).log",
    "bash -c 'tar czf \$HOME/simlogs/docs_backup_\$(date +%s).tar.gz \$HOME/Documents && sleep 2 && tar xzf \$HOME/simlogs/docs_backup_\$(date +%s).tar.gz -C /tmp'",
    "bash -c 'echo \"echo \'Reminder from at\' >> \$HOME/simlogs/atjob_\$(date +%s).log\" | at now + 1 minute'",
    "speaker-test -t sine -f 440 -l 1",
    "sudo bash -c \"echo '# test' >> /etc/motd\"",
    "echo \"Hello team\" | write \$(whoami)",
  )

  cmd="${actions[$((RANDOM % ${#actions[@]}))]}"
  echo "$(date): Executing $cmd"
  eval "$cmd"

  short_pause
  random_sleep
  maybe_long_idle
done