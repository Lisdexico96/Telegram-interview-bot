#!/bin/bash
# Linux/Mac script to stop the bot

echo "Stopping Telegram Interview Bot..."
echo ""

# Find and kill bot.py processes
PIDS=$(ps aux | grep "[b]ot.py" | awk '{print $2}')

if [ -z "$PIDS" ]; then
    echo "No running bot processes found"
else
    echo "Found bot processes: $PIDS"
    for PID in $PIDS; do
        echo "Stopping process $PID..."
        kill -TERM $PID 2>/dev/null || kill -9 $PID 2>/dev/null
    done
    echo "Bot processes stopped"
fi

echo ""
echo "Done!"
